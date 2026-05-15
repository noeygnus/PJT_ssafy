from django.contrib import admin
from .models import DepositProducts, DepositOptions


@admin.register(DepositProducts)
class DepositProductsAdmin(admin.ModelAdmin):
    list_display = ('id', 'fin_prdt_cd', 'kor_co_nm', 'fin_prdt_nm')
    search_fields = ('fin_prdt_cd', 'kor_co_nm', 'fin_prdt_nm')


@admin.register(DepositOptions)
class DepositOptionsAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'product',
        'fin_prdt_cd',
        'intr_rate_type_nm',
        'save_trm',
        'intr_rate',
        'intr_rate2',
    )
    search_fields = ('fin_prdt_cd', 'product__fin_prdt_nm')
    list_filter = ('save_trm', 'intr_rate_type_nm')