# Team 邀请助手

Linux.do 社区 ChatGPT Team 自动邀请系统。

## 功能

- Linux DO OAuth 登录
- 自动分配邮箱 (`{username}kfc@kyx03.de`)
- 自动发送邀请并获取验证码
- 后台管理查看邀请记录
- Redis 持久化存储

## 快速部署

### 1. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 填写配置
```

### 2. Docker Compose 部署

```bash
docker-compose up -d
```

访问 `http://localhost:39001`

### 3. 查看日志

```bash
docker-compose logs -f web
```

## 配置说明

| 变量 | 说明 |
|------|------|
| `AUTHORIZATION_TOKEN` | ChatGPT Team 授权 Token |
| `ACCOUNT_ID` | ChatGPT Team 账户 ID |
| `LINUXDO_CLIENT_ID` | Linux DO OAuth Client ID |
| `LINUXDO_CLIENT_SECRET` | Linux DO OAuth Secret |
| `LINUXDO_REDIRECT_URI` | OAuth 回调地址 |
| `EMAIL_API_AUTH` | 邮箱平台 API 密钥 |
| `ADMIN_PASSWORD` | 后台管理密码 |
| `MIN_TRUST_LEVEL` | 最低信任等级要求 |

## 页面

- `/` - 首页，登录入口
- `/invite` - 邀请页面（需登录）
- `/admin` - 后台管理
- `/health` - 健康检查

## 相关链接

- 邮箱系统: https://kyx-cloud-email.kkyyxx.top/
- Linux DO: https://linux.do/
- ChatGPT: https://chatgpt.com/
