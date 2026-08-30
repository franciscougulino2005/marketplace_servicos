Guia de Execucao e Configuracao - Marketplace de Servicos
1. Visao Geral
Este documento descreve os passos necessarios para rodar localmente a aplicacao Django Marketplace de Servicos e expor o ambiente local de forma segura via HTTPS utilizando o Cloudflare Tunnel.
2. Pre-requisitos
Python 3.x instalado e ambiente virtual configurado na pasta do projeto.
Executavel cloudflared.exe presente no diretorio raiz do projeto (D:\marketplace_servicos).
3. Passo a Passo de Execucao
Passo 3.1: Iniciar o Servidor Local (Django)
No terminal do PyCharm ou PowerShell na raiz do projeto, ative o ambiente virtual e execute o comando:
python manage.py runserver
O servidor ficara acessivel em http://127.0.0.1:8000/.
Passo 3.2: Iniciar o Cloudflare Tunnel
Em uma segunda aba do terminal PowerShell (na pasta raiz do projeto), rode:
.\cloudflared.exe tunnel --url http://localhost:8000
Aguarde a inicializacao. O terminal exibira um bloco em destaque com a URL publica temporaria gerada (exemplo: https://xxxxx.trycloudflare.com).
Nota: Mantenha essa janela do terminal aberta durante todos os testes externos.
4. Resumo das Configuracoes do Projeto
4.1. Configuracao do settings.py
Certifique-se de que o dominio do Cloudflare esta autorizado em ALLOWED_HOSTS e que a rota de redirecionamento pos-login esta definida:
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '.trycloudflare.com']

LOGIN_REDIRECT_URL = 'usuarios:perfil'
4.2. Classe de Login (usuarios/views.py)
A view de login contem a propriedade redirect_authenticated_user = True para redirecionar automaticamente usuarios que ja possuem sessao ativa:
class UsuarioLoginView(LoginView):
    template_name = "usuarios/login.html"
    authentication_form = LoginForm
    redirect_authenticated_user = True
4.3. Rota Raiz (marketplace_servicos/urls.py)
A rota vazia ("") do projeto aponta diretamente para a view de login:
from django.contrib import admin
from django.urls import include, path
from usuarios.views import UsuarioLoginView

urlpatterns = [
    path("", UsuarioLoginView.as_view(), name="home"),
    path("admin/", admin.site.urls),
    path("usuarios/", include("usuarios.urls")),
    path("servicos/", include("servicos.urls")),
    path("solicitacoes/", include("solicitacoes.urls")),
]
5. Fluxo de Acesso do Usuario
Usuario nao autenticado: Ao acessar a URL publica (ex: https://xxxxx.trycloudflare.com/), e direcionado imediatamente para a tela de login.
Usuario autenticado: Ao acessar a URL publica, a aplicacao detecta a sessao e o redireciona automaticamente para a pagina de perfil/dashboard.
