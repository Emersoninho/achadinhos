# products/templatetags/product_filters.py
from django import template

register = template.Library()


@register.filter
def format_brl(value):
    """Formata valor para Real brasileiro: 1999.90 -> 1.999,90"""
    try:
        # Converte para float e formata com vírgula
        value = float(value)
        # Separa parte inteira e decimal
        integer_part = int(value)
        decimal_part = int(round((value - integer_part) * 100))
        
        # Formata a parte inteira com pontos de milhar
        formatted_integer = f"{integer_part:,}".replace(",", ".")
        
        # Retorna no formato brasileiro
        return f"{formatted_integer},{decimal_part:02d}"
    except:
        return "0,00"