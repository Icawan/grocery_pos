from django.urls import path

from . import views

app_name = 'pos'

urlpatterns = [
    path('', views.pos_screen, name='home'),
    path('scan/', views.scan_barcode, name='scan'),
    path('clear/', views.clear_sale, name='clear'),
    path('checkout/', views.checkout_sale, name='checkout'),
    path('products/', views.product_list, name='products'),
    path('products/add/', views.quick_add_product, name='product_add'),
    path('seed/', views.seed_data, name='seed'),
]
