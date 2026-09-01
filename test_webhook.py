import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "marketplace_servicos.settings")
django.setup()

from solicitacoes.models import Contratacao
from utils import enviar_whatsapp


def testar_fluxo_direto():
    contratacao_id = 5
    print(f"Buscando contratação #{contratacao_id} no banco de dados...")

    try:
        contratacao = Contratacao.objects.get(pk=contratacao_id)
        print(f"Contratacao encontrada! Status atual: {contratacao.status}")

        # Simula a atualização de status feita pelo webhook
        contratacao.status = "pago"
        contratacao.save()
        print("Status atualizado para 'pago' com sucesso.")

        # Navega para buscar o telefone do usuário/profissional
        profissional = getattr(contratacao, 'profissional', None)
        usuario = getattr(profissional, 'usuario', None) if profissional else None
        telefone_destino = getattr(usuario, 'telefone', None) or getattr(profissional, 'telefone', None)

        print(f"Telefone de destino identificado: {telefone_destino}")

        if telefone_destino:
            nome_profissional = getattr(usuario, 'nome', None) or getattr(profissional, 'nome', 'Profissional')
            msg = (
                f"🎉 Olá, {nome_profissional}!\n\n"
                f"O pagamento da contratação #{contratacao.id} foi **aprovado** com sucesso! "
                f"O serviço já pode ser iniciado."
            )
            print("Disparando WhatsApp via Evolution API...")
            enviar_whatsapp(telefone_destino, msg)
            print("Disparo finalizado! Verifique o seu celular.")
        else:
            print("Aviso: Nenhum telefone foi encontrado associado a esta contratação.")

    except Contratacao.DoesNotExist:
        print(f"Erro: A contratação com ID {contratacao_id} não existe no banco de dados.")


if __name__ == "__main__":
    testar_fluxo_direto()