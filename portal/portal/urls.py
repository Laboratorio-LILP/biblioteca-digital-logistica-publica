from django.urls import include, path

urlpatterns = [
    path("", include("catalog.urls")),
]

# Páginas de erro no padrão da plataforma, com contexto mínimo e sem banco
# (catalog.views.erro_400 / erro_500). O 404 segue o padrão do Django (404.html).
handler400 = "catalog.views.erro_400"
handler500 = "catalog.views.erro_500"
