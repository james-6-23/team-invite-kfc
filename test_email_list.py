import requests

url = "https://kyx-cloud-email.kkyyxx.top/api/public/emailList"

headers = {
    "Authorization": "8eebb42d-d120-40ce-b324-3b2199f27d63",
    "Content-Type": "application/json"
}

payload = {
    "toEmail": "team4@kyx03.de"
}

response = requests.post(url, headers=headers, json=payload, timeout=10)

print(f"Status Code: {response.status_code}")

if response.status_code == 200:
    data = response.json()
    if data.get("code") == 200:
        emails = data.get("data", [])
        print(f"\n共 {len(emails)} 封邮件:\n")
        for email in emails:
            print(f"ID: {email['emailId']}")
            print(f"发件人: {email['sendName']} <{email['sendEmail']}>")
            print(f"主题: {email['subject']}")
            print(f"时间: {email['createTime']}")
            print("-" * 50)
    else:
        print(f"Error: {data.get('message')}")
else:
    print(f"Response: {response.text}")
