# 🚀 Team 邀请助手

<div align="center">

**Linux.do 社区 ChatGPT Team 自动邀请系统**

[![Docker](https://img.shields.io/badge/Docker-Ready-blue?logo=docker)](https://ghcr.io/james-6-23/team-invite-kfc)
[![Python](https://img.shields.io/badge/Python-3.10+-green?logo=python)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.0+-red?logo=flask)](https://flask.palletsprojects.com)
[![Redis](https://img.shields.io/badge/Redis-7+-orange?logo=redis)](https://redis.io)

</div>

---

## ✨ 功能特性

- 🔐 **Linux DO OAuth 登录** - 安全的第三方认证，支持信任等级验证
- 📧 **智能邮箱分配** - 自动生成格式化邮箱 (`{username}kfc@kyx03.de`)
- 🎫 **自动邀请流程** - 一键发送 ChatGPT Team 邀请
- 🔢 **验证码获取** - 自动从邮箱系统获取验证码
- 🛡️ **并发控制** - 分布式锁机制防止超卖
- 📊 **后台管理** - 完整的邀请记录和统计面板
- 💾 **Redis 持久化** - 可靠的数据存储和 Session 管理
- 🔄 **后台定时任务** - 自动刷新统计数据和待处理邀请
- 🌓 **深色/浅色主题** - 支持主题切换的现代化 UI

---

## 🏗️ 技术栈

| 组件 | 技术 |
|------|------|
| **后端框架** | Flask 3.0+ |
| **Session 存储** | Flask-Session + Redis |
| **数据持久化** | Redis 7+ |
| **定时任务** | APScheduler |
| **HTTP 客户端** | Requests |
| **容器化** | Docker + Docker Compose |
| **WSGI 服务器** | Gunicorn |

---

## 🚀 快速部署

### 方式一：Docker Compose 部署（推荐）

#### 1. 克隆仓库

```bash
git clone https://github.com/james-6-23/team-invite-kfc.git
cd team-invite-kfc
```

#### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 填写配置
```

#### 3. 启动服务

```bash
docker-compose up -d
```

#### 4. 访问应用

打开浏览器访问 `http://localhost:39001`

#### 5. 查看日志

```bash
docker-compose logs -f web
```

### 方式二：本地开发运行

#### 1. 创建虚拟环境

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# 或 .venv\Scripts\activate  # Windows
```

#### 2. 安装依赖

```bash
pip install -r requirements.txt
```

#### 3. 启动 Redis

```bash
# 确保本地 Redis 服务运行在 6379 端口
redis-server
```

#### 4. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 填写配置
```

#### 5. 运行应用

```bash
python main.py
```

---

## ⚙️ 配置说明

### 核心配置

| 变量 | 说明 | 必填 | 默认值 |
|------|------|:----:|--------|
| `SECRET_KEY` | Flask 密钥（生产环境必须修改） | ✅ | `dev_secret_key` |
| `AUTHORIZATION_TOKEN` | ChatGPT Team 授权 Token | ✅ | - |
| `ACCOUNT_ID` | ChatGPT Team 账户 ID | ✅ | - |

### Linux DO OAuth 配置

| 变量 | 说明 | 必填 | 默认值 |
|------|------|:----:|--------|
| `LINUXDO_CLIENT_ID` | OAuth Client ID | ✅ | - |
| `LINUXDO_CLIENT_SECRET` | OAuth Client Secret | ✅ | - |
| `LINUXDO_REDIRECT_URI` | OAuth 回调地址 | ✅ | `http://127.0.0.1:39001/callback` |

> 💡 在 [connect.linux.do](https://connect.linux.do) 申请 OAuth 应用

### 邮箱平台配置

| 变量 | 说明 | 必填 | 默认值 |
|------|------|:----:|--------|
| `EMAIL_API_AUTH` | 邮箱平台 API 密钥 | ✅ | - |
| `EMAIL_API_BASE` | 邮箱平台 API 地址 | ❌ | `https://kyx-cloud-email.kkyyxx.top/api/public` |
| `EMAIL_DOMAIN` | 邮箱域名 | ❌ | `kyx03.de` |
| `EMAIL_ROLE` | 邮箱角色标识 | ❌ | `gpt-team` |

### 其他配置

| 变量 | 说明 | 必填 | 默认值 |
|------|------|:----:|--------|
| `ADMIN_PASSWORD` | 后台管理密码 | ❌ | `admin123` |
| `MIN_TRUST_LEVEL` | 最低信任等级要求 (0-4) | ❌ | `1` |

### Redis 配置

| 变量 | 说明 | 必填 | 默认值 |
|------|------|:----:|--------|
| `REDIS_HOST` | Redis 主机地址 | ❌ | `localhost` |
| `REDIS_PORT` | Redis 端口 | ❌ | `6379` |
| `REDIS_PASSWORD` | Redis 密码 | ❌ | 空 |
| `REDIS_DB` | Redis 数据库编号 | ❌ | `0` |

---

## 🗺️ 路由说明

### 用户页面

| 路由 | 说明 |
|------|------|
| `/` | 首页，登录入口 |
| `/login` | 跳转 Linux DO OAuth 授权 |
| `/callback` | OAuth 回调处理 |
| `/invite` | 邀请页面（需登录） |
| `/logout` | 登出 |

### 后台管理

| 路由 | 说明 |
|------|------|
| `/admin` | 后台管理面板 |
| `/admin/login` | 后台登录 |
| `/admin/logout` | 后台登出 |

### API 接口

| 路由 | 方法 | 说明 |
|------|------|------|
| `/api/stats` | GET | 获取 Team 统计数据 |
| `/api/auto-invite` | POST | 执行自动邀请流程 |
| `/api/poll-code` | GET | 轮询获取验证码 |
| `/api/resend-invite` | POST | 重新发送邀请 |
| `/api/admin/records` | GET | 获取邀请记录（需管理员权限） |
| `/api/admin/stats` | GET | 获取统计概览（需管理员权限） |
| `/api/admin/pending-invites` | GET | 获取待处理邀请（需管理员权限） |
| `/api/admin/members` | GET | 获取空间成员（需管理员权限） |

### 健康检查

| 路由 | 说明 |
|------|------|
| `/health` | 服务健康检查端点 |

---

## 📁 项目结构

```
team-invite/
├── main.py              # 主应用入口
├── requirements.txt     # Python 依赖
├── Dockerfile          # Docker 镜像构建
├── docker-compose.yml  # Docker Compose 配置
├── .env.example        # 环境变量示例
├── .gitignore          # Git 忽略配置
├── .dockerignore       # Docker 忽略配置
├── README.md           # 项目文档
└── templates/          # HTML 模板
    ├── index.html      # 首页
    ├── invite.html     # 邀请页面
    ├── admin.html      # 后台管理
    ├── admin_login.html # 后台登录
    └── error.html      # 错误页面
```

---

## 🔒 安全特性

- **分布式锁** - 使用 Redis 分布式锁防止并发超卖
- **用户级锁** - 防止同一用户重复提交
- **全局锁** - 保证名额检查和邀请发送的原子性
- **Session 签名** - 使用签名保护的 Session 存储
- **Trust Level 验证** - 基于 Linux DO 信任等级的访问控制
- **OAuth State 验证** - 防止 CSRF 攻击

---

## 🔗 相关链接

- 📧 邮箱系统: https://kyx-cloud-email.kkyyxx.top/
- 💬 Linux DO: https://linux.do/
- 🤖 ChatGPT: https://chatgpt.com/
- 🔑 OAuth 申请: https://connect.linux.do/

---

## 📝 更新日志

### v1.0.0
- ✅ Linux DO OAuth 登录集成
- ✅ 自动邀请流程
- ✅ 验证码获取
- ✅ 后台管理面板
- ✅ 深色/浅色主题切换
- ✅ Redis 持久化存储
- ✅ Docker 容器化部署

---

## 📄 许可证

MIT License

---

<div align="center">

Made with ❤️ for Linux.do Community

</div>
