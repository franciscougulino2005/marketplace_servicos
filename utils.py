import requests
from django.conf import settings


def enviar_whatsapp(telefone, mensagem):
    if not telefone:
        return False

    url = getattr(settings, "WHATSAPP_API_URL", "")
    token = getattr(settings, "WHATSAPP_API_TOKEN", "")

    telefone_limpo = "".join(filter(str.isdigit, str(telefone)))
    if not telefone_limpo.startswith("55"):
        telefone_limpo = f"55{telefone_limpo}"

    payload = {
        "number": telefone_limpo,
        "text": mensagem,
        "delay": 1200,
        "linkPreview": False
    }
    headers = {
        "Content-Type": "application/json",
        "apikey": token
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        return response.status_code in [200, 201]
    except requests.RequestException:
        return False