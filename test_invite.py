import requests

# ChatGPT 官方邀请 API
url = "https://chatgpt.com/backend-api/accounts/5c23a3c4-fb12-420d-b116-15ec4b6e27bb/invites"

# 请求头
headers = {
    "accept": "*/*",
    "accept-language": "zh-CN,zh;q=0.9",
    "authorization": "Bearer eyJhbGciOiJSUzI1NiIsImtpZCI6IjE5MzQ0ZTY1LWJiYzktNDRkMS1hOWQwLWY5NTdiMDc5YmQwZSIsInR5cCI6IkpXVCJ9.eyJhdWQiOlsiaHR0cHM6Ly9hcGkub3BlbmFpLmNvbS92MSJdLCJjbGllbnRfaWQiOiJhcHBfWDh6WTZ2VzJwUTl0UjNkRTduSzFqTDVnSCIsImV4cCI6MTc2NjE1MjU3NiwiaHR0cHM6Ly9hcGkub3BlbmFpLmNvbS9hdXRoIjp7ImNoYXRncHRfY29tcHV0ZV9yZXNpZGVuY3kiOiJub19jb25zdHJhaW50IiwiY2hhdGdwdF9kYXRhX3Jlc2lkZW5jeSI6Im5vX2NvbnN0cmFpbnQiLCJ1c2VyX2lkIjoidXNlci1LVjdaa3V4RHBVSU1iejVibzI4ZXJLTWYifSwiaHR0cHM6Ly9hcGkub3BlbmFpLmNvbS9wcm9maWxlIjp7ImVtYWlsIjoiZjcyOTcyMzEyQGdtYWlsLmNvbSIsImVtYWlsX3ZlcmlmaWVkIjp0cnVlfSwiaWF0IjoxNzY1Mjg4NTc1LCJpc3MiOiJodHRwczovL2F1dGgub3BlbmFpLmNvbSIsImp0aSI6IjBjMzkyZjdiLTQ4N2EtNGJjMi04MjIzLTBiMmQ5YmI1ZTQ4NiIsIm5iZiI6MTc2NTI4ODU3NSwicHdkX2F1dGhfdGltZSI6MTc2NTI4ODU3NDUzOSwic2NwIjpbIm9wZW5pZCIsImVtYWlsIiwicHJvZmlsZSIsIm9mZmxpbmVfYWNjZXNzIiwibW9kZWwucmVxdWVzdCIsIm1vZGVsLnJlYWQiLCJvcmdhbml6YXRpb24ucmVhZCIsIm9yZ2FuaXphdGlvbi53cml0ZSJdLCJzZXNzaW9uX2lkIjoiYXV0aHNlc3NfMkpkWHdLUlNFTUVnbnQ0akhSZUw3Q01tIiwic3ViIjoiZ29vZ2xlLW9hdXRoMnwxMDgwNjU4NjE0Nzc0Nzg2MDc1NTkifQ.k_tXffWlrXXyMGQ1IVW0xh_t-qAbubenjYlVBvR_UZdxez_ntpkDKZLIv1JqxUg_f01ycFH79wNhnDjbaWfvWW1yYjmXq-bhGjGrcZzJMsHpoxxkEbom00w522N6azVwLKugIup044X1sUoTQwwowUdF4qPM3pVJGcKPJ4PMu3RX-XhNLIcIqCX3IqBbX1fFPDCVhssPbVhg44TbUKmRJqPfKoghhWXf0U1Z63YDYbf_JC_jiYg55UHjjtsw0k3p84Yfo3wlwlZkLqmXM1J50V9LGoERNj7dRdKXlAsXQ9--a26qjkFjkQXXqHOAF8vdwILuLHyZNPapUW_Ulcw46VdBFf_CRbDQMG1W71U3RIjPzWTsO6Zv19KfNJ0FhnCJ8JWSey9dACgoiWntVcmxlW_pgrCC2K4ZuUSowaSg5bRrjSf64MYq-QKbW2U0FLv9q4j6aoTMpP61p8vSAUFs76SrAYprLuBfNGcI4VL8JTFAFWYZ-CvpGricZv9m7Pfs4y7xluEzk0zRDLFvW36EFZsvS98_zolnept3GdUT1tA5vdq_C-L8QnB0XkaKDhaA3Wux54P7uHngVaq04jO3Lc-SCLSjU9fEfPgBViYukrIkhwAiODMz8RZEQjfRLeBeQ4uCt-QQ4ZkwiiphE8kmEfMCCqi8h2xQk72JepyJIsA",
    "chatgpt-account-id": "5c23a3c4-fb12-420d-b116-15ec4b6e27bb",
    "content-type": "application/json",
    "origin": "https://chatgpt.com",
    "referer": "https://chatgpt.com/",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
}

# 请求体
payload = {
    "email_addresses": ["test123@kyx03.de"],
    "role": "standard-user",
    "resend_emails": True
}

response = requests.post(url, headers=headers, json=payload, timeout=10)

print(f"Status Code: {response.status_code}")
print(f"Response: {response.text}")
