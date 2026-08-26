import mercadopago

from django.conf import settings


def criar_preferencia_oauth():
    """
    Cria a configuração necessária para iniciar
    o processo OAuth do Mercado Pago.
    """

    return {
        "client_id": settings.MERCADO_PAGO_CLIENT_ID,
        "redirect_uri": settings.MERCADO_PAGO_REDIRECT_URI,
    }