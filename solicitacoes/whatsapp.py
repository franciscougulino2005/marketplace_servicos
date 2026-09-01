import requests
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


def enviar_whatsapp(telefone, mensagem):
    """
    Envia mensagem via WhatsApp. Compatível estruturalmente com Z-API ou Evolution API.
    """
    if not telefone:
        return False

    # Limpeza básica do número (deixa apenas números)
    telefone_limpo = "".join(filter(str.isdigit, str(telefone)))

    # Exemplo utilizando o formato padrão de requisição POST (ajuste a URL e o header conforme o provedor escolhido)
    url = getattr(settings, "WHATSAPP_API_URL", "")
    token = getattr(settings, "WHATSAPP_API_TOKEN", "")

    if not url or not token:
        logger.warning("Credenciais de WhatsApp não configuradas no settings.")
        return False

    # Payload adaptado para APIs no estilo Z-API / Evolution
    payload = {
        "phone": telefone_limpo,
        "message": mensagem
    }

    # Se usar Z-API, o header costuma usar 'Client-Token'. Se usar Evolution API, usa 'apikey'.
    headers = {
        "Content-Type": "application/json",
        "apikey": token  # Altere para "Client-Token" se optar pelo Z-API
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        if response.status_code in [200, 201]:
            return True
        else:
            logger.error(f"Erro ao enviar WhatsApp. Status: {response.status_code}, Resposta: {response.text}")
            return False
    except Exception as e:
        logger.error(f"Erro de conexão com a API de WhatsApp: {str(e)}")
        return False