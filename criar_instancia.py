import requests

url = "https://apisend.alpb.cloud/instance/create"
headers = {
    "Content-Type": "application/json",
    "apikey": "s1E8DC07C890C-44B1-A047-DD1C31680251"
}
payload = {
    "instanceName": "marketplace_servicos",
    "qrcode": True,
    "integration": "WHATSAPP-BAILEYS"
}

response = requests.post(url, json=payload, headers=headers)
print("Status Code:", response.status_code)
print("Resposta:", response.text)