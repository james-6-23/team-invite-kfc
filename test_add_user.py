import requests

url = "https://kyx-cloud-email.kkyyxx.top/api/public/addUser"

headers = {
    "Authorization": "8eebb42d-d120-40ce-b324-3b2199f27d63",
    "Content-Type": "application/json"
}

payload = {
    "list": [
        {
            "email": "aaaateam4@kyx03.de",
            "password": "123456",
            "roleName": "gpt-team"
        }
    ]
}

response = requests.post(url, headers=headers, json=payload, timeout=10)

print(f"Status Code: {response.status_code}")
print(f"Response: {response.text}")
