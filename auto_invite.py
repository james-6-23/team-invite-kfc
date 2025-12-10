import requests
import re
import time

# ==================== 配置 ====================
# ChatGPT Team 邀请配置
CHATGPT_ACCOUNT_ID = "5c23a3c4-fb12-420d-b116-15ec4b6e27bb"
CHATGPT_TOKEN = "Bearer eyJhbGciOiJSUzI1NiIsImtpZCI6IjE5MzQ0ZTY1LWJiYzktNDRkMS1hOWQwLWY5NTdiMDc5YmQwZSIsInR5cCI6IkpXVCJ9.eyJhdWQiOlsiaHR0cHM6Ly9hcGkub3BlbmFpLmNvbS92MSJdLCJjbGllbnRfaWQiOiJhcHBfWDh6WTZ2VzJwUTl0UjNkRTduSzFqTDVnSCIsImV4cCI6MTc2NjE1MjU3NiwiaHR0cHM6Ly9hcGkub3BlbmFpLmNvbS9hdXRoIjp7ImNoYXRncHRfY29tcHV0ZV9yZXNpZGVuY3kiOiJub19jb25zdHJhaW50IiwiY2hhdGdwdF9kYXRhX3Jlc2lkZW5jeSI6Im5vX2NvbnN0cmFpbnQiLCJ1c2VyX2lkIjoidXNlci1LVjdaa3V4RHBVSU1iejVibzI4ZXJLTWYifSwiaHR0cHM6Ly9hcGkub3BlbmFpLmNvbS9wcm9maWxlIjp7ImVtYWlsIjoiZjcyOTcyMzEyQGdtYWlsLmNvbSIsImVtYWlsX3ZlcmlmaWVkIjp0cnVlfSwiaWF0IjoxNzY1Mjg4NTc1LCJpc3MiOiJodHRwczovL2F1dGgub3BlbmFpLmNvbSIsImp0aSI6IjBjMzkyZjdiLTQ4N2EtNGJjMi04MjIzLTBiMmQ5YmI1ZTQ4NiIsIm5iZiI6MTc2NTI4ODU3NSwicHdkX2F1dGhfdGltZSI6MTc2NTI4ODU3NDUzOSwic2NwIjpbIm9wZW5pZCIsImVtYWlsIiwicHJvZmlsZSIsIm9mZmxpbmVfYWNjZXNzIiwibW9kZWwucmVxdWVzdCIsIm1vZGVsLnJlYWQiLCJvcmdhbml6YXRpb24ucmVhZCIsIm9yZ2FuaXphdGlvbi53cml0ZSJdLCJzZXNzaW9uX2lkIjoiYXV0aHNlc3NfMkpkWHdLUlNFTUVnbnQ0akhSZUw3Q01tIiwic3ViIjoiZ29vZ2xlLW9hdXRoMnwxMDgwNjU4NjE0Nzc0Nzg2MDc1NTkifQ.k_tXffWlrXXyMGQ1IVW0xh_t-qAbubenjYlVBvR_UZdxez_ntpkDKZLIv1JqxUg_f01ycFH79wNhnDjbaWfvWW1yYjmXq-bhGjGrcZzJMsHpoxxkEbom00w522N6azVwLKugIup044X1sUoTQwwowUdF4qPM3pVJGcKPJ4PMu3RX-XhNLIcIqCX3IqBbX1fFPDCVhssPbVhg44TbUKmRJqPfKoghhWXf0U1Z63YDYbf_JC_jiYg55UHjjtsw0k3p84Yfo3wlwlZkLqmXM1J50V9LGoERNj7dRdKXlAsXQ9--a26qjkFjkQXXqHOAF8vdwILuLHyZNPapUW_Ulcw46VdBFf_CRbDQMG1W71U3RIjPzWTsO6Zv19KfNJ0FhnCJ8JWSey9dACgoiWntVcmxlW_pgrCC2K4ZuUSowaSg5bRrjSf64MYq-QKbW2U0FLv9q4j6aoTMpP61p8vSAUFs76SrAYprLuBfNGcI4VL8JTFAFWYZ-CvpGricZv9m7Pfs4y7xluEzk0zRDLFvW36EFZsvS98_zolnept3GdUT1tA5vdq_C-L8QnB0XkaKDhaA3Wux54P7uHngVaq04jO3Lc-SCLSjU9fEfPgBViYukrIkhwAiODMz8RZEQjfRLeBeQ4uCt-QQ4ZkwiiphE8kmEfMCCqi8h2xQk72JepyJIsA"

# 邮箱平台配置
EMAIL_API_AUTH = "8eebb42d-d120-40ce-b324-3b2199f27d63"
EMAIL_API_BASE = "https://kyx-cloud-email.kkyyxx.top/api/public"

# 要邀请的邮箱配置
EMAIL_TO_INVITE = "team5@kyx03.de"
EMAIL_PASSWORD = "123456"
EMAIL_ROLE = "gpt-team"


def step1_add_user(email, password, role_name):
    """步骤1: 在邮箱平台创建用户"""
    print(f"\n[步骤1] 创建邮箱用户: {email}")
    
    url = f"{EMAIL_API_BASE}/addUser"
    headers = {
        "Authorization": EMAIL_API_AUTH,
        "Content-Type": "application/json"
    }
    payload = {
        "list": [
            {
                "email": email,
                "password": password,
                "roleName": role_name
            }
        ]
    }
    
    response = requests.post(url, headers=headers, json=payload, timeout=10)
    data = response.json()
    
    if data.get("code") == 200:
        print(f"✓ 用户创建成功")
        return True
    else:
        print(f"✗ 用户创建失败: {data.get('message')}")
        return False


def step2_send_invite(email):
    """步骤2: 发送 ChatGPT Team 邀请"""
    print(f"\n[步骤2] 发送 ChatGPT Team 邀请: {email}")
    
    url = f"https://chatgpt.com/backend-api/accounts/{CHATGPT_ACCOUNT_ID}/invites"
    headers = {
        "accept": "*/*",
        "accept-language": "zh-CN,zh;q=0.9",
        "authorization": CHATGPT_TOKEN,
        "chatgpt-account-id": CHATGPT_ACCOUNT_ID,
        "content-type": "application/json",
        "origin": "https://chatgpt.com",
        "referer": "https://chatgpt.com/",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    payload = {
        "email_addresses": [email],
        "role": "standard-user",
        "resend_emails": True
    }
    
    response = requests.post(url, headers=headers, json=payload, timeout=10)
    
    if response.status_code == 200:
        print(f"✓ 邀请发送成功")
        return True
    else:
        print(f"✗ 邀请发送失败: {response.status_code} - {response.text}")
        return False


def step3_get_verification_code(email, max_retries=10, interval=3):
    """步骤3: 获取验证码"""
    print(f"\n[步骤3] 获取验证码: {email}")
    
    url = f"{EMAIL_API_BASE}/emailList"
    headers = {
        "Authorization": EMAIL_API_AUTH,
        "Content-Type": "application/json"
    }
    payload = {"toEmail": email}
    
    for i in range(max_retries):
        print(f"  尝试 {i + 1}/{max_retries}...")
        
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        data = response.json()
        
        if data.get("code") == 200:
            emails = data.get("data", [])
            if emails:
                # 获取最新的邮件（第一封）
                latest_email = emails[0]
                subject = latest_email.get("subject", "")
                
                # 从主题中提取验证码
                match = re.search(r"代码为\s*(\d{6})", subject)
                if match:
                    code = match.group(1)
                    print(f"✓ 获取验证码成功: {code}")
                    print(f"  邮件主题: {subject}")
                    print(f"  邮件时间: {latest_email.get('createTime')}")
                    return code
        
        if i < max_retries - 1:
            print(f"  未找到验证码，{interval}秒后重试...")
            time.sleep(interval)
    
    print(f"✗ 获取验证码失败")
    return None


def main():
    print("=" * 50)
    print("ChatGPT Team 自动邀请流程")
    print("=" * 50)
    
    # 步骤1: 创建邮箱用户
    if not step1_add_user(EMAIL_TO_INVITE, EMAIL_PASSWORD, EMAIL_ROLE):
        print("\n流程中断: 用户创建失败")
        return
    
    # 步骤2: 发送邀请
    if not step2_send_invite(EMAIL_TO_INVITE):
        print("\n流程中断: 邀请发送失败")
        return
    
    # 等待邮件到达
    print("\n等待邮件到达...")
    time.sleep(5)
    
    # 步骤3: 获取验证码
    code = step3_get_verification_code(EMAIL_TO_INVITE)
    
    print("\n" + "=" * 50)
    if code:
        print(f"流程完成!")
        print(f"邮箱: {EMAIL_TO_INVITE}")
        print(f"密码: {EMAIL_PASSWORD}")
        print(f"验证码: {code}")
    else:
        print("流程完成，但未获取到验证码")
    print("=" * 50)


if __name__ == "__main__":
    main()
