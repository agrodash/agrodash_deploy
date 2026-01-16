from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Filtro para acessar valores de um dicionário usando uma chave"""
    if dictionary is None:
        return None
    try:
        return dictionary.get(key)
    except (AttributeError, TypeError):
        return None

@register.filter
def formatar_br(value, casas_decimais=2):
    """Formata número no padrão brasileiro (1.234,56)"""
    if value is None:
        return '-'
    try:
        # Converter para float se necessário
        num = float(value)
        # Formatar com casas decimais
        formatado = f"{num:,.{casas_decimais}f}"
        # Substituir vírgula por ponto temporariamente, depois trocar
        # Separador de milhares: vírgula -> ponto
        # Separador decimal: ponto -> vírgula
        formatado = formatado.replace(',', 'X').replace('.', ',').replace('X', '.')
        return formatado
    except (ValueError, TypeError):
        return str(value) if value else '-'

@register.simple_tag
def make_gmd_key(lote_id, mes, ano):
    """Cria chave composta para buscar GMD: lote_id_mes_ano"""
    try:
        return f"{lote_id}_{mes}_{ano}"
    except:
        return ""
