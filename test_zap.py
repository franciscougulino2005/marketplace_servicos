import os
import django
import requests

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "marketplace_servicos.settings")
django.setup()

from django.conf import settings


def testar_envio():
    url = getattr(settings, "WHATSAPP_API_URL", "")
    token = getattr(settings, "WHATSAPP_API_TOKEN", "")

    telefone = "83988359190"
    telefone_limpo = "".join(filter(str.isdigit, str(telefone)))
    if not telefone_limpo.startswith("55"):
        telefone_limpo = f"55{telefone_limpo}"

    payload = {
        "number": telefone_limpo,
        "text": "🧪 Teste de integração do Marketplace com a Evolution API!",
        "delay": 1200,
        "linkPreview": False
    }
    headers = {
        "Content-Type": "application/json",
        "apikey": token
    }

    print(f"Enviando para URL: {url}")
    response = requests.post(url, json=payload, headers=headers, timeout=10)
    print("Status Code:", response.status_code)
    print("Resposta:", response.text)


if __name__ == "__main__":
    testar_envio()