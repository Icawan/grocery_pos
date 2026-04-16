from django.urls import path

from . import views

app_name = 'pos'

urlpatterns = [
    path('', views.pos_screen, name='home'),
    path('scan/', views.scan_barcode, name='scan'),
    path('scan/api/', views.scan_barcode_api, name='scan_api'),
    path('clear/', views.clear_sale, name='clear'),
    path('checkout/', views.checkout_sale, name='checkout'),
    path('sale-item/<int:item_id>/update/', views.update_sale_item, name='sale_item_update'),
    path('products/', views.product_list, name='products'),
    path('products/add/', views.quick_add_product, name='product_add'),
    path('products/<int:product_id>/update/', views.update_product, name='product_update'),
    path('seed/', views.seed_data, name='seed'),
]
