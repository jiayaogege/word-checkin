"""
签到核心逻辑模块
处理登录、签到请求，解析签到结果
"""

import re
import time
import hashlib
import logging
import requests
from typing import Optional, Dict, Any
from email_notify import CheckinResult

logger = logging.getLogger(__name__)


class CheckinClient:
    """签到客户端"""

    # 常见机场后端请求头
    DEFAULT_HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Content-Type": "application/x-www-form-urlencoded",
    }

    def __init__(self, site_url: str, timeout: int = 30):
        self.site_url = site_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(self.DEFAULT_HEADERS)

    def _get(self, path: str, **kwargs) -> Optional[requests.Response]:
        """GET 请求"""
        url = f"{self.site_url}{path}"
        try:
            resp = self.session.get(url, timeout=self.timeout, **kwargs)
            resp.raise_for_status()
            return resp
        except requests.RequestException as e:
            logger.error(f"GET {url} 失败: {e}")
            return None

    def _post(self, path: str, data: dict = None, **kwargs) -> Optional[requests.Response]:
        """POST 请求"""
        url = f"{self.site_url}{path}"
        try:
            resp = self.session.post(url, data=data, timeout=self.timeout, **kwargs)
            resp.raise_for_status()
            return resp
        except requests.RequestException as e:
            logger.error(f"POST {url} 失败: {e}")
            return None

    def login(self, username: str, password: str) -> bool:
        """登录"""
        logger.info(f"正在登录: {username} @ {self.site_url}")

        # 预热会话。部分站点或 CI 出口 IP 会拒绝登录页 GET，但仍允许接口登录。
        self._get("/auth/login")

        login_data = {
            "email": username,
            "passwd": password,
            "remember_me": "week"
        }
        login_data.update(self._build_pow_fields())

        resp = self._post("/auth/login", data=login_data)
        if not resp:
            return False

        try:
            result = resp.json()
            if result.get("ret") == 1:
                logger.info(f"登录成功: {username}")
                return True
            else:
                msg = result.get("msg", "未知错误")
                logger.warning(f"登录失败: {msg}")
                return False
        except Exception:
            # 部分站点登录成功后跳转，检查 Cookie
            if "uid" in self.session.cookies or "key" in self.session.cookies:
                logger.info(f"登录成功（Cookie 验证）: {username}")
                return True
            logger.error("登录响应解析失败")
            return False

    def _build_pow_fields(self) -> Dict[str, Any]:
        """生成部分站点登录所需的 PoW 验证参数。"""
        resp = self._post("/auth/pow_challenge")
        if not resp:
            return {}

        try:
            challenge = resp.json()
            nonce = self._solve_pow(challenge)
            if nonce is None:
                return {}
            return {
                "pow_timestamp": challenge["timestamp"],
                "pow_ip": challenge["ip"],
                "pow_difficulty": challenge["difficulty"],
                "pow_salt": challenge["salt"],
                "pow_signature": challenge["signature"],
                "pow_nonce": nonce,
            }
        except Exception as e:
            logger.warning(f"生成 PoW 参数失败: {e}")
            return {}

    def _solve_pow(self, challenge: Dict[str, Any]) -> Optional[int]:
        """复现登录页 JS 的 SHA-256 工作量证明。"""
        difficulty = int(challenge["difficulty"])
        threshold = 0xFFFFFF // difficulty
        prefix = (
            f"{challenge['timestamp']}{challenge['ip']}"
            f"{challenge['difficulty']}{challenge['salt']}"
        )

        for nonce in range(50_000_000):
            digest = hashlib.sha256(f"{prefix}{nonce}".encode()).digest()
            value = (digest[0] << 16) | (digest[1] << 8) | digest[2]
            if value < threshold:
                return nonce
        return None

    def checkin(self) -> Dict[str, Any]:
        """执行签到"""
        resp = self._post("/user/checkin")
        if not resp:
            return {"success": False, "message": "签到请求失败", "traffic_info": {}}

        try:
            result = resp.json()
            success = result.get("ret") == 1
            message = result.get("msg", "签到完成")

            # 解析流量信息
            traffic_info = self._parse_traffic_info(message, result)

            return {
                "success": success,
                "message": message,
                "traffic_info": traffic_info
            }
        except Exception as e:
            logger.error(f"解析签到响应失败: {e}")
            return {"success": False, "message": "响应解析失败", "traffic_info": {}}

    def get_user_info(self) -> Dict[str, Any]:
        """获取用户信息（流量等）"""
        resp = self._get("/user")
        if not resp:
            return {}

        try:
            # 从用户页面解析流量信息
            info = {}
            html = resp.text

            # 尝试解析常见字段（正则提取）
            patterns = {
                "剩余流量": r"剩余流量[：:]\s*([0-9.]+\s*[KMGT]?B)",
                "已用流量": r"已用流量[：:]\s*([0-9.]+\s*[KMGT]?B)",
                "套餐流量": r"套餐流量[：:]\s*([0-9.]+\s*[KMGT]?B)",
                "到期时间": r"到期时间[：:]\s*(\d{4}-\d{2}-\d{2})",
            }

            for key, pattern in patterns.items():
                match = re.search(pattern, html)
                if match:
                    info[key] = match.group(1)

            return info
        except Exception:
            return {}

    def _parse_traffic_info(self, message: str, result: dict) -> Dict[str, str]:
        """从签到响应中解析流量信息"""
        traffic_info = {}

        # 从消息文本中提取流量
        traffic_patterns = [
            (r"获得\s*([0-9.]+\s*[KMGT]?B)", "获得流量"),
            (r"剩余\s*([0-9.]+\s*[KMGT]?B)", "剩余流量"),
            (r"([0-9.]+\s*[KMGT]?B)\s*流量", "流量"),
            (r"(\d+)\s*MB", "获得(MB)"),
            (r"(\d+)\s*GB", "获得(GB)"),
        ]

        for pattern, label in traffic_patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                traffic_info[label] = match.group(1)

        # 从 JSON 响应中提取
        for key in ["traffic", "trafficInfo", "flow"]:
            if key in result:
                traffic_info["流量"] = str(result[key])

        return traffic_info

    def close(self):
        """关闭会话"""
        self.session.close()


class CheckinManager:
    """签到任务管理器"""

    def __init__(self, config):
        self.config = config

    def run_account(self, account_config) -> CheckinResult:
        """执行单个账号签到"""
        result = CheckinResult(
            site_name=account_config.site_name,
            username=account_config.username,
            site_url=account_config.site_url
        )

        client = CheckinClient(
            site_url=account_config.site_url,
            timeout=self.config.request_timeout
        )

        try:
            # 带重试的登录
            login_success = False
            for attempt in range(1, self.config.retry_times + 1):
                if client.login(account_config.username, account_config.password):
                    login_success = True
                    break
                logger.warning(f"登录重试 {attempt}/{self.config.retry_times}")
                time.sleep(self.config.retry_interval)

            if not login_success:
                result.success = False
                result.message = "登录失败，已达最大重试次数"
                result.error_detail = "账号或密码错误，或网站无法访问"
                return result

            # 带重试的签到
            checkin_result = None
            for attempt in range(1, self.config.retry_times + 1):
                checkin_result = client.checkin()
                if checkin_result["success"]:
                    break
                # 判断是否已签到（不需要重试）
                msg = checkin_result.get("message", "")
                if "已签到" in msg or "already" in msg.lower():
                    break
                logger.warning(f"签到重试 {attempt}/{self.config.retry_times}")
                time.sleep(self.config.retry_interval)

            if checkin_result:
                result.success = checkin_result["success"]
                result.message = checkin_result["message"]
                result.traffic_info = checkin_result.get("traffic_info", {})

            # 获取额外用户信息
            user_info = client.get_user_info()
            if user_info:
                result.traffic_info.update(user_info)

        except Exception as e:
            result.success = False
            result.message = "签到过程发生异常"
            result.error_detail = str(e)
            logger.error(f"账号 {account_config.username} 签到异常: {e}", exc_info=True)
        finally:
            client.close()

        return result

    def run_all(self) -> list:
        """执行所有账号签到"""
        results = []
        enabled_accounts = [a for a in self.config.accounts if a.enabled]

        logger.info(f"共 {len(enabled_accounts)} 个账号待签到")

        for idx, account in enumerate(enabled_accounts, 1):
            logger.info(f"[{idx}/{len(enabled_accounts)}] 开始处理: {account.site_name}")
            result = self.run_account(account)
            results.append(result)

            status = "✅ 成功" if result.success else "❌ 失败"
            logger.info(f"[{idx}/{len(enabled_accounts)}] {account.site_name} {status}: {result.message}")

            # 账号间隔，避免请求过快
            if idx < len(enabled_accounts):
                time.sleep(2)

        return results
