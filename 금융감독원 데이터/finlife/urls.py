from django.urls import path
from . import views

app_name = 'finlife'

urlpatterns = [
    path('save-deposit-products/', views.save_deposit_products),
    path('deposit-products/', views.deposit_products),
    path('deposit-products/top-rate/', views.top_rate),
    path('deposit-products/<str:fin_prdt_cd>/', views.deposit_product_detail),
    path('deposit-product-options/<str:fin_prdt_cd>/', views.deposit_product_options),
    path('generate-dummy-data/', views.generate_dummy_data),
]
