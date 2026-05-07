"""
主程序入口
协调配置加载、签到执行、邮件通知
"""

import sys
import logging
from datetime import datetime

from config import ConfigManager
from checkin import CheckinManager
from email_notify import EmailNotifier


def setup_logging(level: str = "INFO"):
    """配置日志"""
    log_format = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format=log_format,
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(
                f"checkin_{datetime.now().strftime('%Y%m%d')}.log",
                encoding="utf-8"
            )
        ]
    )


def main():
    # 加载配置
    config_manager = ConfigManager()
    config = config_manager.config

    # 初始化日志
    setup_logging(config.log_level)
    logger = logging.getLogger(__name__)

    logger.info("=" * 50)
    logger.info("机场签到助手 启动")
    logger.info(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 50)

    # 检查账号配置
    if not config.accounts:
        logger.error("没有配置任何账号，请检查配置文件或环境变量")
        sys.exit(1)

    # 执行签到
    manager = CheckinManager(config)
    results = manager.run_all()

    # 打印摘要
    success_count = sum(1 for r in results if r.success)
    logger.info(f"\n签到完成：{success_count}/{len(results)} 成功")

    # 发送邮件通知
    if config.email.sender_email and config.email.receiver_emails:
        logger.info("正在发送邮件通知...")
        notifier = EmailNotifier(config.email)
        email_sent = notifier.send_report(results)
        if email_sent:
            logger.info("✅ 邮件通知发送成功")
        else:
            logger.error("❌ 邮件通知发送失败")
    else:
        logger.warning("邮件配置不完整，跳过邮件通知")

    logger.info("任务结束")

    # 返回退出码（失败时非零）
    sys.exit(0 if success_count == len(results) else 1)


if __name__ == "__main__":
    main()