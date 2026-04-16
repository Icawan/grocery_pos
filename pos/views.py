from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.db import transaction
from django.db.models import F
from django.http import JsonResponse
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


def _serialize_sale(sale):
    items = sale.items.select_related('product').all().order_by('id')
    return {
        'items': [
            {
                'id': item.id,
                'name': item.product.name,
                'quantity': item.quantity,
                'unit_price': f'{item.unit_price:.2f}',
                'line_total': f'{item.line_total:.2f}',
            }
            for item in items
        ],
        'subtotal': f'{sale.subtotal:.2f}',
        'tax': f'{sale.tax:.2f}',
        'total': f'{sale.total:.2f}',
    }


def _scan_and_add(sale, barcode):
    product = Product.objects.filter(barcode=barcode, is_active=True).first()
    if not product:
        return False, f'Barcode {barcode} is not registered. Add this product below, then scan again.'

    existing_item = sale.items.filter(product=product).first()
    current_qty = existing_item.quantity if existing_item else 0
    next_qty = current_qty + 1
    if next_qty > product.stock:
        return False, f'Quantity is above stock for {product.name}. Available stock: {product.stock}.'

    SaleItem.add_or_increment(sale, product)
    sale.recalculate()
    return True, f'Added {product.name}'


def pos_screen(request):
    sale = _get_active_sale(request)
    form = BarcodeScanForm()
    products = Product.objects.order_by('name')[:200]
    context = {
        'sale': sale,
        'items': sale.items.select_related('product').all().order_by('id'),
        'form': form,
        'products': products,
        'pending_barcode': request.session.get('pending_barcode', ''),
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
    ok, message = _scan_and_add(sale, barcode)

    if not ok:
        if 'not registered' in message:
            request.session['pending_barcode'] = barcode
        messages.warning(request, message)
        return redirect('pos:home')

    request.session.pop('pending_barcode', None)
    messages.success(request, message)
    return redirect('pos:home')


@require_POST
@transaction.atomic
def scan_barcode_api(request):
    sale = _get_active_sale(request)
    form = BarcodeScanForm(request.POST)
    if not form.is_valid():
        return JsonResponse({'ok': False, 'message': 'Invalid barcode input.'}, status=400)

    barcode = form.cleaned_data['barcode'].strip()
    ok, message = _scan_and_add(sale, barcode)

    if not ok:
        if 'not registered' in message:
            request.session['pending_barcode'] = barcode
        return JsonResponse({'ok': False, 'message': message}, status=409)

    request.session.pop('pending_barcode', None)
    payload = _serialize_sale(sale)
    payload.update({'ok': True, 'message': message})
    return JsonResponse(payload)


@require_POST
def clear_sale(request):
    sale = _get_active_sale(request)
    sale.delete()
    request.session.pop('active_sale_id', None)
    messages.info(request, 'Sale cleared.')
    return redirect('pos:home')


@require_POST
@transaction.atomic
def checkout_sale(request):
    sale = _get_active_sale(request)
    items = list(sale.items.select_related('product').all())

    if not items:
        messages.warning(request, 'Cart is empty.')
        return redirect('pos:home')

    for item in items:
        if item.quantity > item.product.stock:
            messages.error(
                request,
                f'Cannot checkout: {item.product.name} quantity in cart ({item.quantity}) is above stock ({item.product.stock}).',
            )
            return redirect('pos:home')

    for item in items:
        Product.objects.filter(pk=item.product_id).update(stock=F('stock') - item.quantity)

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
    is_active = request.POST.get('is_active') == 'on'

    if not (name and barcode):
        messages.error(request, 'Name and barcode are required.')
        return redirect('pos:home')

    try:
        price_value = Decimal(price)
        if price_value < 0:
            raise InvalidOperation
        stock_value = int(stock)
        if stock_value < 0:
            raise ValueError
    except (InvalidOperation, ValueError):
        messages.error(request, 'Price and stock must be valid positive values.')
        return redirect('pos:home')

    product, created = Product.objects.update_or_create(
        barcode=barcode,
        defaults={
            'name': name,
            'price': price_value,
            'stock': stock_value,
            'is_active': is_active,
        },
    )

    request.session.pop('pending_barcode', None)

    if created:
        messages.success(request, f'Product {name} added.')
    else:
        messages.success(request, f'Product {product.name} updated.')
    return redirect('pos:home')


@require_POST
@transaction.atomic
def update_sale_item(request, item_id):
    sale = _get_active_sale(request)
    item = get_object_or_404(SaleItem.objects.select_related('product'), pk=item_id, sale=sale)

    quantity_raw = request.POST.get('quantity', '').strip()
    unit_price_raw = request.POST.get('unit_price', '').strip()

    try:
        quantity = int(quantity_raw)
        if quantity < 0:
            raise ValueError
        unit_price = Decimal(unit_price_raw)
        if unit_price < 0:
            raise InvalidOperation
    except (ValueError, InvalidOperation):
        messages.error(request, 'Quantity and unit price must be valid positive values.')
        return redirect('pos:home')

    if quantity > item.product.stock:
        messages.error(request, f'Quantity is above stock for {item.product.name}. Available stock: {item.product.stock}.')
        return redirect('pos:home')

    if quantity == 0:
        item.delete()
        sale.recalculate()
        messages.info(request, f'Removed {item.product.name} from cart.')
        return redirect('pos:home')

    item.quantity = quantity
    item.unit_price = unit_price
    item.save()
    sale.recalculate()
    messages.success(request, f'Updated {item.product.name} line.')
    return redirect('pos:home')


@require_POST
def update_product(request, product_id):
    product = get_object_or_404(Product, pk=product_id)

    name = request.POST.get('name', '').strip()
    barcode = request.POST.get('barcode', '').strip()
    price_raw = request.POST.get('price', '').strip()
    stock_raw = request.POST.get('stock', '').strip()
    is_active = request.POST.get('is_active') == 'on'

    if not (name and barcode):
        messages.error(request, 'Name and barcode are required for product updates.')
        return redirect('pos:products')

    existing = Product.objects.filter(barcode=barcode).exclude(pk=product.pk).first()
    if existing:
        messages.error(request, f'Barcode {barcode} is already used by {existing.name}.')
        return redirect('pos:products')

    try:
        price = Decimal(price_raw)
        if price < 0:
            raise InvalidOperation
        stock = int(stock_raw)
        if stock < 0:
            raise ValueError
    except (InvalidOperation, ValueError):
        messages.error(request, 'Price and stock must be valid positive values.')
        return redirect('pos:products')

    product.name = name
    product.barcode = barcode
    product.price = price
    product.stock = stock
    product.is_active = is_active
    product.save()

    messages.success(request, f'Updated {product.name}.')
    return redirect('pos:products')


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
