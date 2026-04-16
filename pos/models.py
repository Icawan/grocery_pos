from decimal import Decimal

from django.db import models
from django.db.models import F


class Product(models.Model):
    name = models.CharField(max_length=150)
    barcode = models.CharField(max_length=64, unique=True, db_index=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.barcode})"


class Sale(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    total = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))

    TAX_RATE = Decimal('0.07')

    def recalculate(self):
        self.subtotal = self.items.aggregate(s=models.Sum('line_total')).get('s') or Decimal('0.00')
        self.tax = (self.subtotal * self.TAX_RATE).quantize(Decimal('0.01'))
        self.total = (self.subtotal + self.tax).quantize(Decimal('0.01'))
        self.save(update_fields=['subtotal', 'tax', 'total'])


class SaleItem(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    line_total = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        unique_together = ('sale', 'product')

    def save(self, *args, **kwargs):
        self.line_total = (self.unit_price * self.quantity).quantize(Decimal('0.01'))
        super().save(*args, **kwargs)

    @classmethod
    def add_or_increment(cls, sale, product):
        item, created = cls.objects.get_or_create(
            sale=sale,
            product=product,
            defaults={'quantity': 1, 'unit_price': product.price, 'line_total': product.price},
        )
        if not created:
            cls.objects.filter(pk=item.pk).update(quantity=F('quantity') + 1)
            item.refresh_from_db(fields=['quantity', 'unit_price'])
            item.save(update_fields=['line_total'])
        Product.objects.filter(pk=product.pk, stock__gt=0).update(stock=F('stock') - 1)
        return item
