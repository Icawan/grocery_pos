from django.contrib import messages
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import BarcodeScanForm
from .models import Product, Sale, SaleItem


def _get_active_sale(request):
    sale_id = request.session.get('active_sale_id')
    sale = Sale.objects.filter(pk=sale_id).first() if sale_id else None
    if not sale:
        sale = Sale.objects.create()
        request.session['active_sale_id'] = sale.pk
    return sale


def pos_screen(request):
    sale = _get_active_sale(request)
    form = BarcodeScanForm()
    products = Product.objects.order_by('name')[:200]
    context = {
        'sale': sale,
        'items': sale.items.select_related('product').all().order_by('id'),
        'form': form,
        'products': products,
    }
    return render(request, 'pos/pos_screen.html', context)


@require_POST
@transaction.atomic
def scan_barcode(request):
    sale = _get_active_sale(request)
    form = BarcodeScanForm(request.POST)
    if not form.is_valid():
        messages.error(request, 'Invalid barcode input.')
        return redirect('pos:home')

    barcode = form.cleaned_data['barcode'].strip()
    product = Product.objects.filter(barcode=barcode, is_active=True).first()
    if not product:
        messages.error(request, f'No active product found for barcode: {barcode}')
        return redirect('pos:home')

    if product.stock <= 0:
        messages.error(request, f'{product.name} is out of stock.')
        return redirect('pos:home')

    SaleItem.add_or_increment(sale, product)
    sale.recalculate()
    messages.success(request, f'Added {product.name}')
    return redirect('pos:home')


@require_POST
def clear_sale(request):
    sale = _get_active_sale(request)
    sale.delete()
    request.session.pop('active_sale_id', None)
    messages.info(request, 'Sale cleared.')
    return redirect('pos:home')


@require_POST
def checkout_sale(request):
    sale = _get_active_sale(request)
    sale.recalculate()
    request.session.pop('active_sale_id', None)
    messages.success(request, f'Checkout complete. Total charged: ${sale.total}')
    return redirect('pos:home')


@require_POST
def quick_add_product(request):
    name = request.POST.get('name', '').strip()
    barcode = request.POST.get('barcode', '').strip()
    price = request.POST.get('price', '0').strip()
    stock = request.POST.get('stock', '0').strip()

    if not (name and barcode):
        messages.error(request, 'Name and barcode are required.')
        return redirect('pos:home')

    product, created = Product.objects.get_or_create(
        barcode=barcode,
        defaults={'name': name, 'price': price, 'stock': stock},
    )
    if not created:
        messages.warning(request, f'Barcode {barcode} already exists for {product.name}.')
    else:
        messages.success(request, f'Product {name} added.')
    return redirect('pos:home')


def product_list(request):
    return render(request, 'pos/products.html', {'products': Product.objects.order_by('name')})


def seed_data(request):
    if Product.objects.exists():
        messages.info(request, 'Seed skipped: products already exist.')
        return redirect('pos:home')

    Product.objects.bulk_create([
        Product(name='Milk 1L', barcode='1000001', price='2.99', stock=30),
        Product(name='Bread', barcode='1000002', price='1.99', stock=40),
        Product(name='Eggs (12)', barcode='1000003', price='3.49', stock=25),
        Product(name='Apples (1kg)', barcode='1000004', price='4.25', stock=20),
    ])
    messages.success(request, 'Seed products created.')
    return redirect('pos:home')
