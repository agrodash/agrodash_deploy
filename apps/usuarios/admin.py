from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html, mark_safe
from .models import Usuario, TokenInscricao, Propriedade, Lote, ProjecaoGanho, GastoNutricional, CustoFixo, Receita, Mortalidade
from .forms import TokenInscricaoAdminForm


@admin.register(Usuario)
class UsuarioAdmin(BaseUserAdmin):
    list_display = ('email', 'nome', 'is_active', 'is_staff', 'date_joined')
    list_filter = ('is_active', 'is_staff', 'is_superuser', 'date_joined')
    search_fields = ('email', 'nome')
    ordering = ('email',)
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Informações Pessoais', {'fields': ('nome',)}),
        ('Permissões', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        ('Datas Importantes', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2'),
        }),
    )


@admin.register(TokenInscricao)
class TokenInscricaoAdmin(admin.ModelAdmin):
    form = TokenInscricaoAdminForm
    list_display = ('usuario_email', 'senha_gerada', 'data_criacao', 'utilizado', 'acoes')
    list_filter = ('utilizado', 'data_criacao')
    search_fields = ('usuario__email', 'usuario__nome')
    readonly_fields = ('senha_gerada', 'data_criacao', 'senha_display')
    ordering = ('-data_criacao',)
    
    fieldsets = (
        ('Informações do Token', {
            'fields': ('email_usuario', 'senha_display', 'senha_gerada', 'data_criacao', 'utilizado')
        }),
    )
    
    def usuario_email(self, obj):
        return obj.usuario.email if obj.usuario else '-'
    usuario_email.short_description = 'Email do Usuário'
    
    def senha_display(self, obj):
        if obj.senha_gerada:
            return format_html(
                '<div style="font-family: monospace; font-size: 16px; padding: 10px; '
                'background-color: #f0f0f0; border: 1px solid #ccc; border-radius: 4px; '
                'display: inline-block; font-weight: bold; color: #d32f2f;">{}</div>',
                obj.senha_gerada
            )
        return '-'
    senha_display.short_description = 'Senha Gerada'
    
    def acoes(self, obj):
        if not obj.utilizado:
            return mark_safe('<span style="color: green; font-weight: bold;">✓ Disponível</span>')
        return mark_safe('<span style="color: gray;">✗ Utilizado</span>')
    acoes.short_description = 'Status'


@admin.register(Propriedade)
class PropriedadeAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'proprietario', 'municipio_estado', 'data_criacao')
    list_filter = ('data_criacao', 'faz_rotacionado', 'faz_adubacao', 'faz_confinamento')
    search_fields = ('usuario__email', 'proprietario', 'municipio_estado')
    readonly_fields = ('data_criacao', 'data_atualizacao')
    ordering = ('-data_criacao',)
    
    def get_queryset(self, request):
        """Override para tratar erros de conversão de tipos"""
        qs = super().get_queryset(request)
        # Tenta retornar o queryset normalmente
        # Se houver erro ao acessar, será tratado no template/admin
        return qs
    
    fieldsets = (
        ('Dados Básicos/Iniciais', {
            'fields': ('usuario', 'proprietario', 'municipio_estado', 'proprio_ou_arrendamento', 
                      'indice_pluviometrico', 'area_total_ha', 'area_util_pastagem_ha')
        }),
        ('Área', {
            'fields': ('quantidade_pastos', 'tamanho_medio_pastos', 'faz_rotacionado', 
                      'percentual_area_rotacionada', 'faz_adubacao', 'faz_correcao_solo', 
                      'rotina_correcao', 'possui_area_volumoso', 'tamanho_area_volumoso_ha', 
                      'faz_integracao_lavoura_pecuaria')
        }),
        ('Produção', {
            'fields': ('quantidade_animais', 'sexo_animais', 'tipo_raca_animais', 'tipo_suplementacao',
                      'cria_recria_ou_engorda', 'quantidade_animais_lote_peso', 'compra_gado_produtor_ou_leilao',
                      'tipo_terminacao', 'taxa_desfrute', 'idade_media_abate', 'plantas_frigorificas')
        }),
        ('Gestão', {
            'fields': ('quantidade_funcionarios', 'utiliza_software_gestao', 'qual_software_gestao',
                      'possui_balanca', 'frequencia_pesagem', 'utiliza_controle_individual', 'tipo_brinco_chip')
        }),
        ('Terminação', {
            'fields': ('faz_confinamento', 'estatico_confinamento', 'tem_fabrica_racao', 'possui_moinho',
                      'possui_vagao_forrageiro', 'capacidade_armazenagem_volumoso', 'capacidade_armazenagem_graos')
        }),
        ('Datas', {
            'fields': ('data_criacao', 'data_atualizacao')
        }),
    )


@admin.register(Lote)
class LoteAdmin(admin.ModelAdmin):
    list_display = ('nome', 'tipo', 'propriedade', 'quantidade', 'peso_kg', 'data_criacao')
    list_filter = ('tipo', 'sexo', 'data_criacao')
    search_fields = ('nome', 'propriedade__usuario__email')
    ordering = ('nome',)


@admin.register(ProjecaoGanho)
class ProjecaoGanhoAdmin(admin.ModelAdmin):
    list_display = ('lote', 'mes', 'ano', 'gmd_kg', 'data_criacao')
    list_filter = ('ano', 'mes', 'data_criacao')
    search_fields = ('lote__nome', 'lote__propriedade__usuario__email')
    ordering = ('ano', 'mes')


@admin.register(GastoNutricional)
class GastoNutricionalAdmin(admin.ModelAdmin):
    list_display = ('lote', 'mes', 'ano', 'gasto_diario', 'gasto_mensal_calculado', 'data_criacao')
    list_filter = ('ano', 'mes', 'data_criacao')
    search_fields = ('lote__nome', 'lote__propriedade__usuario__email')
    ordering = ('ano', 'mes')
    
    def gasto_mensal_calculado(self, obj):
        return f"R$ {obj.calcular_gasto_mensal():.2f}"
    gasto_mensal_calculado.short_description = 'Gasto Mensal (R$)'


@admin.register(CustoFixo)
class CustoFixoAdmin(admin.ModelAdmin):
    list_display = ('propriedade', 'tipo', 'mes', 'ano', 'valor', 'data_criacao')
    list_filter = ('ano', 'mes', 'tipo', 'data_criacao')
    search_fields = ('propriedade__usuario__email', 'tipo')
    ordering = ('ano', 'mes', 'tipo')


@admin.register(Receita)
class ReceitaAdmin(admin.ModelAdmin):
    list_display = ('propriedade', 'tipo', 'mes', 'ano', 'valor', 'data_criacao')
    list_filter = ('ano', 'mes', 'tipo', 'data_criacao')
    search_fields = ('propriedade__usuario__email', 'tipo')
    ordering = ('ano', 'mes', 'tipo')


@admin.register(Mortalidade)
class MortalidadeAdmin(admin.ModelAdmin):
    list_display = ('lote', 'mes', 'ano', 'percentual', 'data_criacao')
    list_filter = ('ano', 'mes', 'data_criacao')
    search_fields = ('lote__nome', 'lote__propriedade__usuario__email')
    ordering = ('ano', 'mes')

