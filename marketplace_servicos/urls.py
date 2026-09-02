from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from usuarios.views import home  # Import direto da view home


urlpatterns = [
    # Rota raiz chamando a função home
    path("", home, name="home"),
    path("admin/", admin.site.urls),
    path("usuarios/", include("usuarios.urls")),
    path("servicos/", include("servicos.urls")),
    path("solicitacoes/", include("solicitacoes.urls")),
    path('categorias/', include('categorias.urls')),
    path('admin-relatorios/', include('relatorios_administrativos.urls')),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )