"""core URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from usuarios import views as usuarios_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', usuarios_views.login_view, name='login'),
    path('logout/', usuarios_views.logout_view, name='logout'),
    path('preencher-informacoes/', usuarios_views.preencher_informacoes_view, name='preencher_informacoes'),
    path('lotes/', usuarios_views.lotes_view, name='lotes'),
    path('lotes/dashboard/', usuarios_views.lotes_dashboard_view, name='lotes_dashboard'),
    path('lotes/<int:lote_id>/deletar/', usuarios_views.deletar_lote, name='deletar_lote'),
    path('projecoes/<int:projecao_id>/deletar/', usuarios_views.deletar_projecao, name='deletar_projecao'),
    path('nutricional/', usuarios_views.nutricional_view, name='nutricional'),
    path('nutricional/dashboard/', usuarios_views.nutricional_dashboard_view, name='nutricional_dashboard'),
    path('nutricional/<int:gasto_id>/deletar/', usuarios_views.deletar_gasto_nutricional, name='deletar_gasto_nutricional'),
    path('faturamento/', usuarios_views.faturamento_view, name='faturamento'),
    path('fluxo-caixa/', usuarios_views.fluxo_caixa_view, name='fluxo_caixa'),
    path('ponto-equilibrio/', usuarios_views.ponto_equilibrio_view, name='ponto_equilibrio'),
    path('', usuarios_views.home_view, name='home'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
