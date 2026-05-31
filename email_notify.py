"""
邮件通知模块
支持 HTML 格式邮件，包含签到结果汇总
"""

import smtplib
import ssl
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formataddr
from datetime import datetime
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

PROJECT_URL = "https://github.com/jiayaogege/word-checkin"
PROJECT_NAME = "word-checkin"


class CheckinResult:
    """签到结果数据类"""

    def __init__(self, site_name: str, username: str, site_url: str):
        self.site_name = site_name
        self.username = username
        self.site_url = site_url
        self.success: bool = False
        self.message: str = ""
        self.traffic_info: Dict[str, Any] = {}
        self.checkin_time: str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.error_detail: str = ""

    def to_dict(self) -> dict:
        return {
            "site_name": self.site_name,
            "username": self.username,
            "site_url": self.site_url,
            "success": self.success,
            "message": self.message,
            "traffic_info": self.traffic_info,
            "checkin_time": self.checkin_time,
            "error_detail": self.error_detail
        }


class EmailNotifier:
    """邮件通知器"""

    def __init__(self, email_config):
        self.config = email_config

    def send_report(self, results: List[CheckinResult]) -> bool:
        """发送签到报告邮件"""
        if not self._validate_config():
            return False

        try:
            subject = self._build_subject(results)
            html_body = self._build_html_body(results)
            text_body = self._build_text_body(results)
        except Exception as e:
            logger.error(f"构建邮件内容时发生错误: {e}", exc_info=True)
            return False

        return self._send_email(subject, html_body, text_body)

    def _validate_config(self) -> bool:
        """验证邮件配置"""
        if not self.config.sender_email:
            logger.error("发件人邮箱未配置")
            return False
        if not self.config.sender_password:
            logger.error("发件人密码未配置")
            return False
        if not self.config.receiver_emails:
            logger.error("收件人邮箱未配置")
            return False
        return True

    def _build_subject(self, results: List[CheckinResult]) -> str:
        """构建邮件主题"""
        total = len(results)
        success = sum(1 for r in results if r.success)
        date_str = datetime.now().strftime("%Y-%m-%d")
        status = "✅ 全部成功" if success == total else f"⚠️ {success}/{total} 成功"
        return f"【机场签到】{date_str} {status}"

    def _build_html_body(self, results: List[CheckinResult]) -> str:
        """构建 HTML 格式邮件正文"""
        total = len(results)
        success_count = sum(1 for r in results if r.success)
        fail_count = total - success_count
        now = datetime.now().strftime("%Y年%m月%d日 %H:%M:%S")

        # 统计卡片
        summary_cards = f"""
        <div style="display:flex; gap:15px; margin-bottom:25px; flex-wrap:wrap;">
            <div style="flex:1; min-width:120px; background:#e8f5e9; border-radius:10px; 
                        padding:15px; text-align:center; border-left:4px solid #4caf50;">
                <div style="font-size:28px; font-weight:bold; color:#2e7d32;">{success_count}</div>
                <div style="color:#555; font-size:13px; margin-top:5px;">✅ 签到成功</div>
            </div>
            <div style="flex:1; min-width:120px; background:#{'#fce4ec' if fail_count > 0 else '#e8f5e9'}; 
                        border-radius:10px; padding:15px; text-align:center; 
                        border-left:4px solid {'#f44336' if fail_count > 0 else '#4caf50'};">
                <div style="font-size:28px; font-weight:bold; color:{'#c62828' if fail_count > 0 else '#2e7d32'};">
                    {fail_count}
                </div>
                <div style="color:#555; font-size:13px; margin-top:5px;">❌ 签到失败</div>
            </div>
            <div style="flex:1; min-width:120px; background:#e3f2fd; border-radius:10px; 
                        padding:15px; text-align:center; border-left:4px solid #2196f3;">
                <div style="font-size:28px; font-weight:bold; color:#1565c0;">{total}</div>
                <div style="color:#555; font-size:13px; margin-top:5px;">📊 账号总数</div>
            </div>
        </div>
        """

        # 详细结果表格
        rows = ""
        for idx, result in enumerate(results, 1):
            status_icon = "✅" if result.success else "❌"
            status_color = "#e8f5e9" if result.success else "#fce4ec"
            status_text_color = "#2e7d32" if result.success else "#c62828"
            bg_color = "#ffffff" if idx % 2 == 0 else "#f9f9f9"

            # 流量信息
            traffic_html = ""
            if result.traffic_info:
                traffic_items = []
                for key, value in result.traffic_info.items():
                    traffic_items.append(
                        f'<span style="background:#e3f2fd; color:#1565c0; padding:2px 8px; '
                        f'border-radius:12px; font-size:12px; margin:2px; display:inline-block;">'
                        f'{key}: {value}</span>'
                    )
                traffic_html = '<div style="margin-top:6px;">' + "".join(traffic_items) + '</div>'

            rows += f"""
            <tr style="background:{bg_color};">
                <td style="padding:12px 15px; border-bottom:1px solid #eee; text-align:center; 
                           font-weight:bold; color:#666;">{idx}</td>
                <td style="padding:12px 15px; border-bottom:1px solid #eee;">
                    <div style="font-weight:bold; color:#333;">{result.site_name}</div>
                    <div style="font-size:12px; color:#888; margin-top:2px;">
                        <a href="{result.site_url}" style="color:#2196f3; text-decoration:none;">
                            {result.site_url}
                        </a>
                    </div>
                </td>
                <td style="padding:12px 15px; border-bottom:1px solid #eee; color:#555;">
                    {result.username}
                </td>
                <td style="padding:12px 15px; border-bottom:1px solid #eee; text-align:center;">
                    <span style="background:{status_color}; color:{status_text_color}; 
                                 padding:3px 10px; border-radius:12px; font-size:13px; 
                                 font-weight:bold;">
                        {status_icon} {'成功' if result.success else '失败'}
                    </span>
                </td>
                <td style="padding:12px 15px; border-bottom:1px solid #eee; color:#555;">
                    <div>{result.message}</div>
                    {traffic_html}
                    {f'<div style="color:#f44336; font-size:12px; margin-top:4px;">错误: {result.error_detail}</div>' 
                     if result.error_detail else ''}
                </td>
                <td style="padding:12px 15px; border-bottom:1px solid #eee; color:#888; 
                           font-size:12px; white-space:nowrap;">
                    {result.checkin_time}
                </td>
            </tr>
            """

        html = f"""
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>机场签到报告</title>
        </head>
        <body style="margin:0; padding:0; background:#f0f2f5; font-family:'Microsoft YaHei', 
                     Arial, sans-serif;">
            <div style="max-width:800px; margin:30px auto; padding:0 15px;">
                
                <!-- 顶部标题 -->
                <div style="background:linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                            border-radius:12px 12px 0 0; padding:30px; color:white; text-align:center;">
                    <div style="font-size:32px; margin-bottom:8px;">✈️</div>
                    <h1 style="margin:0; font-size:22px; letter-spacing:2px;">机场签到报告</h1>
                    <p style="margin:8px 0 0 0; opacity:0.85; font-size:14px;">{now}</p>
                </div>
                
                <!-- 主体内容 -->
                <div style="background:#ffffff; padding:25px; border-radius:0 0 12px 12px; 
                            box-shadow:0 4px 15px rgba(0,0,0,0.1);">
                    
                    <!-- 统计卡片 -->
                    {summary_cards}
                    
                    <!-- 详细结果 -->
                    <h3 style="color:#333; margin:0 0 15px 0; padding-bottom:10px; 
                               border-bottom:2px solid #667eea; font-size:16px;">
                        📋 详细签到结果
                    </h3>
                    
                    <div style="overflow-x:auto;">
                        <table style="width:100%; border-collapse:collapse; font-size:14px;">
                            <thead>
                                <tr style="background:linear-gradient(135deg, #667eea, #764ba2); 
                                           color:white;">
                                    <th style="padding:12px 15px; text-align:center; 
                                               font-weight:normal; white-space:nowrap;">#</th>
                                    <th style="padding:12px 15px; text-align:left; 
                                               font-weight:normal;">站点</th>
                                    <th style="padding:12px 15px; text-align:left; 
                                               font-weight:normal;">账号</th>
                                    <th style="padding:12px 15px; text-align:center; 
                                               font-weight:normal; white-space:nowrap;">状态</th>
                                    <th style="padding:12px 15px; text-align:left; 
                                               font-weight:normal;">签到信息</th>
                                    <th style="padding:12px 15px; text-align:center; 
                                               font-weight:normal; white-space:nowrap;">时间</th>
                                </tr>
                            </thead>
                            <tbody>
                                {rows}
                            </tbody>
                        </table>
                    </div>
                    
                    <!-- 底部说明 -->
                    <div style="margin-top:25px; padding:15px; background:#f8f9fa; 
                                border-radius:8px; border-left:4px solid #667eea;">
                        <p style="margin:0; color:#666; font-size:13px; line-height:1.8;">
                            💡 <strong>提示：</strong>此邮件由机场签到助手自动发送，请勿回复。<br>
                            🕐 <strong>下次签到：</strong>明日自动执行<br>
                            ⚙️ <strong>项目地址：</strong>
                            <a href="{PROJECT_URL}" 
                               style="color:#667eea;">{PROJECT_NAME}</a>
                        </p>
                    </div>
                </div>
                
                <!-- 页脚 -->
                <div style="text-align:center; padding:20px; color:#999; font-size:12px;">
                    <p style="margin:0;">© {datetime.now().year} 机场签到助手 · 自动化任务</p>
                </div>
            </div>
        </body>
        </html>
        """
        return html

    def _build_text_body(self, results: List[CheckinResult]) -> str:
        """构建纯文本格式邮件（备用）"""
        lines = [
            "=" * 50,
            "机场签到报告",
            f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "=" * 50,
            ""
        ]

        success_count = sum(1 for r in results if r.success)
        lines.append(f"签到统计：{success_count}/{len(results)} 成功")
        lines.append("")

        for idx, result in enumerate(results, 1):
            status = "✅ 成功" if result.success else "❌ 失败"
            lines.extend([
                f"{idx}. {result.site_name} ({result.username})",
                f"   状态：{status}",
                f"   信息：{result.message}",
                f"   时间：{result.checkin_time}",
            ])
            if result.traffic_info:
                traffic_str = " | ".join(f"{k}: {v}" for k, v in result.traffic_info.items())
                lines.append(f"   流量：{traffic_str}")
            if result.error_detail:
                lines.append(f"   错误：{result.error_detail}")
            lines.append("")

        lines.append("=" * 50)
        lines.append("此邮件由机场签到助手自动发送")

        return "\n".join(lines)

    def _send_email(self, subject: str, html_body: str, text_body: str) -> bool:
        """发送邮件"""
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = Header(subject, "utf-8")
            msg["From"] = formataddr(
                (self.config.sender_name, self.config.sender_email)
            )
            msg["To"] = ", ".join(self.config.receiver_emails)

            # 添加纯文本和 HTML 两种格式（客户端优先显示 HTML）
            msg.attach(MIMEText(text_body, "plain", "utf-8"))
            msg.attach(MIMEText(html_body, "html", "utf-8"))

            # 创建 SSL 上下文
            context = ssl.create_default_context()

            # 发送
            if self.config.smtp_ssl:
                logger.debug(f"使用 SSL 连接 {self.config.smtp_host}:{self.config.smtp_port}")
                server = smtplib.SMTP_SSL(
                    self.config.smtp_host, self.config.smtp_port, timeout=15, context=context
                )
            else:
                logger.debug(f"使用 STARTTLS 连接 {self.config.smtp_host}:{self.config.smtp_port}")
                server = smtplib.SMTP(
                    self.config.smtp_host, self.config.smtp_port, timeout=15
                )
                server.starttls(context=context)

            with server:
                server.login(self.config.sender_email, self.config.sender_password)
                server.sendmail(
                    self.config.sender_email,
                    self.config.receiver_emails,
                    msg.as_string()
                )

            logger.info(f"邮件发送成功 -> {', '.join(self.config.receiver_emails)}")
            return True

        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"邮件认证失败，请检查邮箱账号和密码（或应用专用密码）: {e}")
        except smtplib.SMTPConnectError as e:
            logger.error(f"连接 SMTP 服务器失败 {self.config.smtp_host}:{self.config.smtp_port}，"
                         f"请检查地址和端口是否正确: {e}")
        except smtplib.SMTPServerDisconnected as e:
            logger.error(f"SMTP 服务器连接断开，可能是端口或加密方式不匹配: {e}")
        except smtplib.SMTPException as e:
            logger.error(f"SMTP 错误: {e}")
        except ssl.SSLError as e:
            logger.error(f"SSL 错误，请检查 SMTP_SSL 设置是否正确（465→true, 587→false）: {e}")
        except Exception as e:
            logger.error(f"发送邮件时发生未知错误: {e}", exc_info=True)

        return False
