"""
配置管理模块
支持从环境变量或配置文件读取配置
"""

import os
import json
import logging
import re
from dataclasses import dataclass, field
from typing import List, Optional

logger = logging.getLogger(__name__)


@dataclass
class AccountConfig:
    """单个账号配置"""
    username: str
    password: str
    site_url: str
    site_name: str = "未知站点"
    enabled: bool = True


@dataclass
class EmailConfig:
    """邮件配置"""
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 465
    smtp_ssl: bool = True
    sender_email: str = ""
    sender_password: str = ""
    receiver_emails: List[str] = field(default_factory=list)
    sender_name: str = "机场签到助手"


@dataclass
class AppConfig:
    """应用总配置"""
    accounts: List[AccountConfig] = field(default_factory=list)
    email: EmailConfig = field(default_factory=EmailConfig)
    retry_times: int = 3
    retry_interval: int = 5
    request_timeout: int = 30
    log_level: str = "INFO"


class ConfigManager:
    """配置管理器"""

    def __init__(self, config_file: str = "config.json"):
        self.config_file = config_file
        self.config: AppConfig = AppConfig()
        self._load_config()

    def _load_config(self):
        """加载配置：优先环境变量，其次配置文件"""
        if self._has_env_accounts():
            self._load_from_env()
            logger.info("从环境变量加载配置")
        elif os.path.exists(self.config_file):
            self._load_from_file()
            logger.info(f"从配置文件 {self.config_file} 加载配置")
        else:
            self._load_from_env()
            logger.info("从环境变量加载配置")

    def _has_env_accounts(self) -> bool:
        """是否配置了环境变量账号。"""
        return any(os.environ.get(f"ACCOUNT_{i}") for i in range(1, 100))

    def _load_from_file(self):
        """从 JSON 配置文件加载"""
        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            # 解析账号配置
            accounts = []
            for acc in data.get("accounts", []):
                accounts.append(AccountConfig(
                    username=acc["username"],
                    password=acc["password"],
                    site_url=acc["site_url"],
                    site_name=acc.get("site_name", "未知站点"),
                    enabled=acc.get("enabled", True)
                ))

            # 解析邮件配置
            email_data = data.get("email", {})
            email_config = EmailConfig(
                smtp_host=email_data.get("smtp_host", "smtp.gmail.com"),
                smtp_port=email_data.get("smtp_port", 465),
                smtp_ssl=email_data.get("smtp_ssl", True),
                sender_email=email_data.get("sender_email", ""),
                sender_password=email_data.get("sender_password", ""),
                receiver_emails=email_data.get("receiver_emails", []),
                sender_name=email_data.get("sender_name", "机场签到助手")
            )

            self.config = AppConfig(
                accounts=accounts,
                email=email_config,
                retry_times=data.get("retry_times", 3),
                retry_interval=data.get("retry_interval", 5),
                request_timeout=data.get("request_timeout", 30),
                log_level=data.get("log_level", "INFO")
            )

        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            raise

    def _load_from_env(self):
        """从环境变量加载配置"""
        # 账号配置：支持多账号，格式 ACCOUNT_1=url|username|password|name
        accounts = []
        i = 1
        while True:
            account_str = os.environ.get(f"ACCOUNT_{i}")
            if not account_str:
                break
            parts = account_str.split("|")
            if len(parts) >= 3:
                accounts.append(AccountConfig(
                    site_url=self._clean_account_url(parts[0]),
                    username=parts[1].strip(),
                    password=parts[2].strip(),
                    site_name=parts[3].strip() if len(parts) > 3 else f"站点{i}"
                ))
            i += 1

        # 邮件配置
        receiver_str = os.environ.get("EMAIL_RECEIVERS", "")
        receivers = [r.strip() for r in receiver_str.split(",") if r.strip()]

        email_config = EmailConfig(
            smtp_host=os.environ.get("SMTP_HOST", "smtp.gmail.com"),
            smtp_port=int(os.environ.get("SMTP_PORT", "465")),
            smtp_ssl=os.environ.get("SMTP_SSL", "true").lower() == "true",
            sender_email=os.environ.get("SENDER_EMAIL", ""),
            sender_password=os.environ.get("SENDER_PASSWORD", ""),
            receiver_emails=receivers,
            sender_name=os.environ.get("SENDER_NAME", "机场签到助手")
        )

        self.config = AppConfig(
            accounts=accounts,
            email=email_config,
            retry_times=int(os.environ.get("RETRY_TIMES", "3")),
            retry_interval=int(os.environ.get("RETRY_INTERVAL", "5")),
            request_timeout=int(os.environ.get("REQUEST_TIMEOUT", "30")),
            log_level=os.environ.get("LOG_LEVEL", "INFO")
        )

    def _clean_account_url(self, value: str) -> str:
        """兼容将 `ACCOUNT_1 = ...` 整行粘贴到 Secret value 的情况。"""
        return re.sub(r"^ACCOUNT_\d+\s*=\s*", "", value.strip())
