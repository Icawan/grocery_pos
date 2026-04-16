from django.contrib import admin

from .models import Product, Sale, SaleItem


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'barcode', 'price', 'stock', 'is_active')
    search_fields = ('name', 'barcode')


class SaleItemInline(admin.TabularInline):
    model = SaleItem
    extra = 0
    readonly_fields = ('product', 'quantity', 'unit_price', 'line_total')


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ('id', 'created_at', 'subtotal', 'tax', 'total')
    inlines = [SaleItemInline]
    readonly_fields = ('subtotal', 'tax', 'total')
