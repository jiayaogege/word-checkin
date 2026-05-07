# ✈️ 机场自动签到助手

<div align="center">

![Python](https://img.shields.io/badge/Python-3.8+-blue?style=flat-square&logo=python)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)
![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-自动执行-orange?style=flat-square&logo=github-actions)
![Email](https://img.shields.io/badge/通知方式-邮件推送-red?style=flat-square&logo=gmail)

**全自动机场签到 + 邮件推送通知，支持多账号、多站点、多收件人**

[快速开始](#-快速开始) · [配置说明](#-配置说明) · [邮箱配置](#-邮箱服务商配置) · [常见问题](#-常见问题)

</div>

---

## 📖 项目简介

每天定时自动完成所有机场账号的签到任务，签到完成后将结果以
**精美 HTML 邮件**的形式推送到你的邮箱，支持多账号、多站点同时管理。

### ✨ 主要特性

- 📬 **邮件推送** — 支持 HTML 富文本邮件，展示签到状态、流量信息
- 👥 **多账号管理** — 无限制添加机场账号，独立配置、独立启停
- 📮 **多收件人** — 支持同时推送到多个邮箱
- 🔄 **自动重试** — 登录/签到失败自动重试，可配置重试次数
- ⏰ **定时执行** — 基于 GitHub Actions，每天定时自动运行，无需服务器
- 📊 **流量解析** — 自动提取签到获得的流量信息展示在邮件中
- 📝 **日志记录** — 完整的运行日志，自动保存归档
- 🔒 **安全存储** — 所有敏感信息通过 GitHub Secrets 加密存储
- 🛠️ **双配置源** — 支持 JSON 配置文件或环境变量两种方式

---

## 📁 项目结构

```
jichang_checkin/
├── main.py              # 主程序入口
├── checkin.py           # 签到核心逻辑（登录、签到、重试）
├── email_notify.py      # 邮件通知模块（HTML模板、SMTP发送）
├── config.py            # 配置管理（环境变量/JSON双来源）
├── config.json          # 配置文件模板（本地运行使用）
├── requirements.txt     # Python 依赖包
├── .github/
│   └── workflows/
│       └── checkin.yml  # GitHub Actions 工作流
└── README.md            # 项目说明文档
```

---

## 🚀 快速开始

### 方式一：GitHub Actions（推荐，无需服务器）

#### 第一步：Fork 本仓库

点击右上角 **Fork** 按钮，将项目复制到你的 GitHub 账号下。

#### 第二步：配置 Secrets

进入你 Fork 后的仓库，点击：
**Settings → Secrets and variables → Actions → New repository secret**

按下表逐一添加：

| Secret 名称 | 必填 | 说明 |
|---|:---:|---|
| `ACCOUNT_1` | ✅ | 第一个账号，格式见下方说明 |
| `ACCOUNT_2` | ➕ | 第二个账号（可选，可无限添加） |
| `ACCOUNT_N` | ➕ | 第 N 个账号（按序编号即可） |
| `SMTP_HOST` | ✅ | SMTP 服务器地址 |
| `SMTP_PORT` | ✅ | SMTP 端口号 |
| `SMTP_SSL` | ✅ | 是否使用 SSL（填 `true` 或 `false`） |
| `SENDER_EMAIL` | ✅ | 发件人邮箱地址 |
| `SENDER_PASSWORD` | ✅ | 邮箱应用专用密码（非登录密码） |
| `EMAIL_RECEIVERS` | ✅ | 收件人邮箱，多个用英文逗号分隔 |

> **账号格式说明：**
> ```
> ACCOUNT_1 = https://站点地址.com|登录邮箱|登录密码|站点名称
>
> # 示例：
> ACCOUNT_1 = https://abc.example.com|user@gmail.com|mypassword123|ABC机场
> ACCOUNT_2 = https://xyz.example.com|user@gmail.com|mypassword456|XYZ机场
> ```
> 四个字段用竖线 `|` 分隔，站点名称可自定义，用于邮件中显示。

#### 第三步：手动触发测试

配置完成后，点击仓库顶部 **Actions** 选项卡：

```
Actions → 机场自动签到 → Run workflow → Run workflow
```

观察运行结果，成功后检查邮箱是否收到报告邮件。

#### 第四步：等待自动执行

工作流已设置每天 **北京时间 08:30** 自动运行，无需任何操作。

---

### 方式二：本地运行

#### 环境要求

- Python 3.8 或以上
- pip 包管理器

#### 安装步骤

```bash
# 1. 克隆仓库
git clone https://github.com/jiayaogege/word-checkin.git
cd word-checkin

# 2. 安装依赖
pip install -r requirements.txt

# 3. 复制并编辑配置文件
cp config.json.example config.json
```

编辑 `config.json`，填写你的账号和邮件信息：

```json
{
  "accounts": [
    {
      "site_name": "ABC机场",
      "site_url": "https://abc.example.com",
      "username": "user@gmail.com",
      "password": "your_password",
      "enabled": true
    },
    {
      "site_name": "XYZ机场",
      "site_url": "https://xyz.example.com",
      "username": "user@gmail.com",
      "password": "your_password",
      "enabled": true
    }
  ],
  "email": {
    "smtp_host": "smtp.gmail.com",
    "smtp_port": 465,
    "smtp_ssl": true,
    "sender_email": "your_sender@gmail.com",
    "sender_password": "your_app_password",
    "receiver_emails": [
      "receiver@gmail.com"
    ],
    "sender_name": "机场签到助手"
  },
  "retry_times": 3,
  "retry_interval": 5,
  "request_timeout": 30,
  "log_level": "INFO"
}
```

```bash
# 4. 运行程序
python main.py
```

---

## ⚙️ 配置说明

### 账号配置参数

| 参数 | 类型 | 必填 | 说明 |
|---|---|:---:|---|
| `site_name` | string | ✅ | 站点名称，显示在邮件报告中 |
| `site_url` | string | ✅ | 站点完整地址，如 `https://example.com` |
| `username` | string | ✅ | 登录账号（通常是邮箱） |
| `password` | string | ✅ | 登录密码 |
| `enabled` | boolean | ➖ | 是否启用该账号，默认 `true` |

### 邮件配置参数

| 参数 | 类型 | 必填 | 说明 |
|---|---|:---:|---|
| `smtp_host` | string | ✅ | SMTP 服务器地址 |
| `smtp_port` | integer | ✅ | SMTP 端口，SSL通常为465，STARTTLS为587 |
| `smtp_ssl` | boolean | ✅ | 使用 SSL 加密，端口465填`true`，587填`false` |
| `sender_email` | string | ✅ | 发件人邮箱地址 |
| `sender_password` | string | ✅ | 邮箱**应用专用密码**（非账号登录密码） |
| `receiver_emails` | array | ✅ | 收件人邮箱列表，支持多个 |
| `sender_name` | string | ➖ | 发件人显示名称，默认"机场签到助手" |

### 全局配置参数

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `retry_times` | integer | `3` | 登录/签到失败最大重试次数 |
| `retry_interval` | integer | `5` | 重试间隔秒数 |
| `request_timeout` | integer | `30` | HTTP 请求超时秒数 |
| `log_level` | string | `INFO` | 日志级别：`DEBUG`/`INFO`/`WARNING`/`ERROR` |

---

## 📧 邮箱服务商配置

### Gmail

> ⚠️ 需要先开启两步验证，再生成应用专用密码

1. 访问 [Google 账号安全](https://myaccount.google.com/security)
2. 开启**两步验证**
3. 搜索「应用专用密码」→ 生成密码（16位，不含空格填入）

```
SMTP_HOST    = smtp.gmail.com
SMTP_PORT    = 465
SMTP_SSL     = true
SENDER_PASSWORD = xxxx xxxx xxxx xxxx  （16位应用密码）
```

### QQ 邮箱

> ⚠️ 需要在设置中开启 SMTP 服务，获取授权码

1. 登录 QQ 邮箱网页版
2. **设置 → 账户 → POP3/IMAP/SMTP服务** → 开启
3. 按提示获取**授权码**（非 QQ 密码）

```
SMTP_HOST    = smtp.qq.com
SMTP_PORT    = 465
SMTP_SSL     = true
SENDER_PASSWORD = xxxxxxxxxxxxxxxx  （16位授权码）
```

### 163 邮箱

> ⚠️ 需要开启 SMTP 并设置客户端授权密码

1. 登录 163 邮箱
2. **设置 → POP3/SMTP/IMAP** → 开启 SMTP 服务
3. 设置**客户端授权密码**

```
SMTP_HOST    = smtp.163.com
SMTP_PORT    = 465
SMTP_SSL     = true
SENDER_PASSWORD = 你设置的授权密码
```

### Outlook / Hotmail

```
SMTP_HOST    = smtp.office365.com
SMTP_PORT    = 587
SMTP_SSL     = false   ← 注意：使用 STARTTLS，此处填 false
SENDER_PASSWORD = 账号登录密码
```

### 自定义域名邮箱

```
SMTP_HOST    = mail.yourdomain.com   （联系邮箱服务商获取）
SMTP_PORT    = 465
SMTP_SSL     = true
SENDER_PASSWORD = 邮箱登录密码
```

---

## 📬 邮件示例

签到完成后，你将收到类似以下格式的邮件：

**邮件主题：**
```
【机场签到】2024-01-15  ✅ 全部成功（2/2）
【机场签到】2024-01-15  ⚠️ 部分成功（1/2）
```

**邮件内容预览：**

```
╔══════════════════════════════════════╗
║         ✈️  机场签到报告              ║
║      2024年01月15日  08:30:25        ║
╠═══════════╦═══════════╦═════════════╣
║  ✅ 成功:2 ║  ❌ 失败:0 ║  📊 共计:2  ║
╠═══════════╩═══════════╩═════════════╣
║  #  站点名   账号         状态  信息  ║
║  1  ABC机场  user@..  ✅成功  +1GB  ║
║  2  XYZ机场  user@..  ✅成功  已签到 ║
╚══════════════════════════════════════╝

💡 此邮件由机场签到助手自动发送，请勿回复
🕐 下次签到：明日 08:30 自动执行
```

---

## 🔧 高级用法

### 修改执行时间

编辑 `.github/workflows/checkin.yml` 中的 cron 表达式：

```yaml
on:
  schedule:
    - cron: "30 0 * * *"   # UTC 时间，对应北京时间 08:30
```

**常用时间参考（北京时间 → UTC）：**

| 北京时间 | Cron 表达式 |
|---|---|
| 每天 00:30 | `30 16 * * *` |
| 每天 08:00 | `0 0 * * *` |
| 每天 08:30 | `30 0 * * *` |
| 每天 12:00 | `0 4 * * *` |
| 每天 20:00 | `0 12 * * *` |

> 在线工具：[crontab.guru](https://crontab.guru) 可视化编辑 Cron 表达式

### 禁用某个账号（不删除配置）

在 `config.json` 中将对应账号的 `enabled` 设为 `false`：

```json
{
  "site_name": "暂停的站点",
  "enabled": false
}
```

### 手动触发签到

在 GitHub Actions 页面随时手动触发：

```
仓库页面 → Actions → 机场自动签到 → Run workflow
```

---

## 📋 运行日志

每次运行会生成以日期命名的日志文件：

```
checkin_20240115.log
```

**GitHub Actions 日志查看：**
```
Actions → 对应的运行记录 → checkin-logs（Artifacts 下载）
```

**日志示例：**
```
2024-01-15 08:30:01 [INFO] main: ══════════════════════════════
2024-01-15 08:30:01 [INFO] main: 机场签到助手 启动
2024-01-15 08:30:01 [INFO] main: 时间: 2024-01-15 08:30:01
2024-01-15 08:30:02 [INFO] checkin: [1/2] 开始处理: ABC机场
2024-01-15 08:30:03 [INFO] checkin: 正在登录: user@gmail.com @ https://abc.com
2024-01-15 08:30:04 [INFO] checkin: 登录成功: user@gmail.com
2024-01-15 08:30:05 [INFO] checkin: [1/2] ABC机场 ✅ 成功: 获得 1GB 流量
2024-01-15 08:30:07 [INFO] checkin: [2/2] 开始处理: XYZ机场
2024-01-15 08:30:09 [INFO] checkin: [2/2] XYZ机场 ✅ 成功: 今日已签到
2024-01-15 08:30:09 [INFO] main: 签到完成：2/2 成功
2024-01-15 08:30:10 [INFO] email_notify: 邮件发送成功 -> receiver@gmail.com
2024-01-15 08:30:10 [INFO] main: ✅ 邮件通知发送成功
```

---

## ❓ 常见问题

<details>
<summary><strong>Q：收不到签到邮件怎么办？</strong></summary>

按以下步骤排查：

1. **检查垃圾邮件** — 首次收到可能被识别为垃圾邮件，标记为"不是垃圾邮件"
2. **检查 SMTP 配置** — 端口、SSL 设置是否与邮件服务商匹配
3. **检查应用密码** — 确认填写的是**应用专用密码**，而非账号登录密码
4. **检查 Actions 日志** — 在 GitHub Actions 运行记录中查看详细错误信息
5. **开启 SMTP 服务** — QQ/163 邮箱需要手动在设置中开启 SMTP

</details>

<details>
<summary><strong>Q：GitHub Actions 不自动运行怎么办？</strong></summary>

可能原因及解决方法：

1. **仓库长期无活动** — GitHub 会暂停超过 60 天无 push 的仓库的 Actions
   - 解决：定期向仓库提交任意修改，或手动触发一次
2. **Actions 被禁用** — 检查 Settings → Actions → General 是否允许运行
3. **Cron 表达式错误** — 使用 [crontab.guru](https://crontab.guru) 验证表达式
4. **GitHub 服务延迟** — 定时任务可能有 15-30 分钟延迟，属正常现象

</details>

<details>
<summary><strong>Q：签到失败，提示"登录失败"怎么办？</strong></summary>

1. 确认账号密码正确（直接在浏览器登录测试）
2. 检查站点地址是否包含 `https://` 前缀
3. 站点地址末尾**不要**加 `/`
4. 部分站点可能有 IP 封锁，GitHub Actions 的 IP 可能被限制（无解）
5. 查看 Actions 日志中的具体错误信息

</details>

<details>
<summary><strong>Q：如何添加更多账号？</strong></summary>

在 GitHub Secrets 中继续添加 `ACCOUNT_3`、`ACCOUNT_4` ... 按序编号即可，
程序会自动识别所有 `ACCOUNT_N` 格式的环境变量。

```
ACCOUNT_3 = https://site3.com|user@mail.com|pass|站点3
ACCOUNT_4 = https://site4.com|user@mail.com|pass|站点4
```

</details>

<details>
<summary><strong>Q：config.json 和环境变量哪个优先级更高？</strong></summary>

**`config.json` 优先级更高。**

- 存在 `config.json` 文件时：从文件读取配置
- 不存在 `config.json` 文件时：从环境变量读取配置

GitHub Actions 环境中没有 `config.json`，因此自动使用环境变量（Secrets）。
本地调试时，`config.json` 更方便。

> ⚠️ 切勿将含有真实密码的 `config.json` 提交到 GitHub！
> 项目已在 `.gitignore` 中排除此文件。

</details>

<details>
<summary><strong>Q：支持哪些机场后端系统？</strong></summary>

目前主要适配以下常见后端：

- **V2Board** — 大多数现代机场使用
- **SSPanel-UIM** — 老牌开源面板
- **sspanel** 系列变种

如果你的机场签到接口路径不同，可以修改 `checkin.py` 中的请求路径：

```python
# 登录接口
resp = self._post("/auth/login", data=login_data)

# 签到接口
resp = self._post("/user/checkin")
```

</details>

---

## 🛡️ 安全说明

- ✅ 所有密码通过 **GitHub Secrets** 加密存储，不会出现在代码或日志中
- ✅ `config.json` 已加入 `.gitignore`，不会被意外提交
- ✅ 邮件传输使用 SSL/TLS 加密
- ⚠️ 请勿将含密码的配置文件分享或公开
- ⚠️ 建议为签到专门创建一个邮箱，避免主邮箱密码泄露风险

---

## 📝 更新日志

| 版本 | 日期 | 更新内容 |
|---|---|---|
| v2.0.0 | 2024-01 | 重构代码，新增邮件推送通知 |
| v1.x.x | - | 原版 Telegram/其他通知 |

---

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建特性分支：`git checkout -b feature/your-feature`
3. 提交更改：`git commit -m 'Add some feature'`
4. 推送分支：`git push origin feature/your-feature`
5. 提交 Pull Request。

---

## 📄 License

本项目基于 [MIT License](LICENSE) 开源，请遵守相关服务条款，合理使用。

---

<div align="center">

**如果本项目对你有帮助，欢迎点个 ⭐ Star！**

</div>
