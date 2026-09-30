from django.urls import path
from django.views.generic import RedirectView

from . import views

app_name = "catalog"

urlpatterns = [
    path("", views.home, name="home"),
    path("busca/", views.search, name="search"),
    path("documento/<str:code>/", views.document_detail, name="document_detail"),
    path("metodologia/", views.metodologia, name="metodologia"),
    path("metodologia/categorias/", views.metodologia, {"aba": "categorias"}, name="metodologia_categorias"),
    path("metodologia/assuntos/", views.metodologia, {"aba": "assuntos"}, name="metodologia_assuntos"),
    # Endereços antigos: a página chamava-se Coleções até 23/09/2026
    path("colecoes/", RedirectView.as_view(pattern_name="catalog:metodologia", permanent=True)),
    path("colecoes/categorias/", RedirectView.as_view(pattern_name="catalog:metodologia_categorias", permanent=True)),
    path("colecoes/assuntos/", RedirectView.as_view(pattern_name="catalog:metodologia_assuntos", permanent=True)),
    path("colecao/<int:topic_id>/", views.collection_detail, name="collection_detail"),
    path("download/<str:code>/", views.download, name="download"),
    path("curadoria/", views.curadoria, name="curadoria"),
    path("sobre/", views.about, name="about"),

    # Páginas institucionais e legais (LAI / LGPD / eMAG / Lei 13.460)
    path("transparencia/", views.transparencia, name="transparencia"),
    path("acessibilidade/", views.acessibilidade, name="acessibilidade"),
    path("politica-de-privacidade/", views.politica_privacidade, name="politica_privacidade"),
    path("politica-de-cookies/", views.politica_cookies, name="politica_cookies"),
    path("mapa-do-site/", views.mapa_site, name="mapa_site"),
    path("fale-conosco/", views.fale_conosco, name="fale_conosco"),
]
