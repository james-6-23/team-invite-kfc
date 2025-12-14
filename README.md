# 🚀 Linux.do ChatGPT Team 邀请助手

<div align="center">

**Linux.do 社区 ChatGPT Team 自动邀请系统**

[![Docker](https://img.shields.io/badge/Docker-Ready-blue?logo=docker)](https://ghcr.io/james-6-23/team-invite-kfc)
[![Python](https://img.shields.io/badge/Python-3.10+-green?logo=python)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.0+-red?logo=flask)](https://flask.palletsprojects.com)
[![Redis](https://img.shields.io/badge/Redis-7+-orange?logo=redis)](https://redis.io)

</div>

---

## 📖 项目简介

这是一个专为 Linux.do 社区定制的 ChatGPT Team 自动邀请系统。它集成了 Linux DO OAuth 登录，并利用开源项目 [Cloud Mail](https://github.com/maillab/cloud-mail) 作为邮件服务后端，实现了从邮箱生成到邀请发送的全自动化流程。

## ✨ 功能特性

- 🔐 **Linux DO OAuth 登录** - 安全的第三方认证，支持信任等级验证
- 📧 **智能邮箱分配** - 集成 [Cloud Mail](https://github.com/maillab/cloud-mail)，自动生成临时邮箱
- 🎫 **自动邀请流程** - 一键发送 ChatGPT Team 邀请
- 🔢 **验证码自动获取** - 自动从邮件系统提取验证码
- 🛡️ **并发控制** - Redis 分布式锁机制防止超卖和并发问题
- 📊 **后台管理** - 完整的邀请记录、统计面板及成员管理
- 💾 **可靠存储** - Redis 持久化数据存储和 Session 管理
- 🔄 **自动维护** - 后台定时任务自动刷新缓存和处理过期邀请
- 🌓 **现代化 UI** - 支持深色/浅色主题切换

---

## 🏗️ 技术栈

| 组件 | 技术 |
|------|------|
| **后端框架** | Flask 3.0+ |
| **邮件服务** | [Cloud Mail](https://github.com/maillab/cloud-mail) (Cloudflare Workers) |
| **Session 存储** | Flask-Session + Redis |
| **数据持久化** | Redis 7+ |
| **定时任务** | APScheduler |
| **容器化** | Docker + Docker Compose |
| **部署** | Gunicorn |

---

## 🚀 快速部署

### 前置准备

本项目依赖 [Cloud Mail](https://github.com/maillab/cloud-mail) 作为邮件后端。请先参考 Cloud Mail 文档部署您自己的邮件服务，并获取 API 地址和鉴权信息。

### 方式一：Docker Compose 部署（推荐）

#### 1. 克隆仓库

```bash
git clone https://github.com/james-6-23/team-invite-kfc.git
cd team-invite-kfc
```

#### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 填写配置，特别是邮件服务相关的配置
```

#### 3. 启动服务

```bash
docker-compose up -d
```

#### 4. 访问应用

打开浏览器访问 `http://localhost:39001`

### 方式二：本地开发运行

#### 1. 环境准备

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate  # Windows

pip install -r requirements.txt
```

#### 2. 启动 Redis

需确保本地安装并运行 Redis (默认端口 6379)。

#### 3. 运行应用

```bash
cp .env.example .env
# 填写配置
python main.py
```

---

## ⚙️ 配置说明

### 核心配置

| 变量 | 说明 | 必填 | 默认值 |
|------|------|:----:|--------|
| `SECRET_KEY` | Flask 密钥（生产环境请修改） | ✅ | `dev_secret_key` |
| `AUTHORIZATION_TOKEN` | ChatGPT Team 邀请者 Token | ✅ | - |
| `ACCOUNT_ID` | ChatGPT Team 账户 ID | ✅ | - |

### Linux DO OAuth 配置

| 变量 | 说明 | 必填 | 默认值 |
|------|------|:----:|--------|
| `LINUXDO_CLIENT_ID` | OAuth Client ID | ✅ | - |
| `LINUXDO_CLIENT_SECRET` | OAuth Client Secret | ✅ | - |
| `LINUXDO_REDIRECT_URI` | OAuth 回调地址 | ✅ | `http://127.0.0.1:39001/callback` |

> 💡 在 [connect.linux.do](https://connect.linux.do) 申请 OAuth 应用

### 邮箱平台配置 (Cloud Mail)

| 变量 | 说明 | 必填 | 默认值 |
|------|------|:----:|--------|
| `EMAIL_API_AUTH` | Cloud Mail API 密钥 | ✅ | - |
| `EMAIL_API_BASE` | Cloud Mail API 地址 | ❌ | `https://your-cloud-mail.com/api/public` |
| `EMAIL_DOMAIN` | 邮箱域名 | ❌ | `your-domain.com` |
| `EMAIL_ROLE` | 邮箱角色标识 | ❌ | `gpt-team` |

### 其他配置

| 变量 | 说明 | 必填 | 默认值 |
|------|------|:----:|--------|
| `ADMIN_PASSWORD` | 后台管理密码 | ❌ | `admin123` |
| `MIN_TRUST_LEVEL` | 最低信任等级要求 (0-4) | ❌ | `1` |
| `REDIS_HOST` | Redis 主机地址 | ❌ | `localhost` |

---

## 🔗 相关链接

- 📧 邮件后端: [Cloud Mail (Open Source)](https://github.com/maillab/cloud-mail)
- 💬 Linux DO: [https://linux.do/](https://linux.do/)
- 🤖 ChatGPT: [https://chatgpt.com/](https://chatgpt.com/)
- 🔑 OAuth 申请: [https://connect.linux.do/](https://connect.linux.do/)

---

## 📝 更新日志

### v1.0.0
- ✅ Linux DO OAuth 登录集成
- ✅ 集成 Cloud Mail 邮件服务
- ✅ 自动邀请与验证码提取
- ✅ 后台管理面板与数据统计
- ✅ Redis 分布式锁与持久化
- ✅ Docker 容器化支持

---

## 📄 许可证

MIT License

---

<div align="center">

Made with ❤️ for Linux.do Community

</div>
