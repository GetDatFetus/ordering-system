from datetime import datetime
from secrets import token_urlsafe
from typing import Optional

from django.core.exceptions import ValidationError
from django.db.models import Model
from django.db.models.deletion import CASCADE
from django.db.models.fields import BooleanField, CharField, DateField, DateTimeField, DecimalField, EmailField, FloatField, IntegerField, TextField, URLField
from django.db.models.fields.related import ForeignKey


RANDOM_ORDER_TAG_BYTES_ENTROPY = 32
"""Bytes of entropy for an order tag."""


def get_random_order_tag():
    randstr = token_urlsafe(RANDOM_ORDER_TAG_BYTES_ENTROPY)
    return f'[{randstr}]'


class XMRExchangeRate(Model):
    date_updated = DateTimeField(auto_now_add=True, null=False)
    rate = FloatField(null=False)
    """Exchange rate, in XMR per USD."""

    def __str__(self):
        return f'{self.rate} XMR/USD @ {self.date_updated}'

    @staticmethod
    def current() -> Optional['XMRExchangeRate']:
        try:
            return XMRExchangeRate.objects.latest('date_updated')
        except XMRExchangeRate.DoesNotExist:
            return None


class Supplier(Model):
    title = CharField(max_length=100, null=False)
    url = URLField(max_length=256, null=False)

    def __str__(self):
        return f'Supplier: {self.title}'


class StoreItem(Model):
    title = CharField(max_length=100, null=False)
    description = TextField()

    date_added = DateField(auto_now_add=True)
    visible = BooleanField(default=True, null=False)
    active = BooleanField(default=True, null=False)

    supplier = ForeignKey(Supplier, on_delete=CASCADE)
    supplier_url = URLField(max_length=256)
    price_usd = DecimalField(max_digits=10, decimal_places=2, null=False)

    def __str__(self):
        return f'StoreItem: {self.title} by {self.supplier}'


class Order(Model):
    email = EmailField(max_length=64, null=False)

    mailing_address = TextField(max_length=256, null=True)

    date_placed = DateField(auto_now_add=True)
    date_paid = DateField()
    date_purchased = DateField()
    date_arrived = DateField()

    order_tag = CharField(max_length=32, default=get_random_order_tag(), null=False)
    """Used to associate incoming transactions to orders."""
    xmr_per_usd_rate = FloatField(null=False)
    """XMR exchange rate may change between orders."""
    processing_fees = DecimalField(max_digits=10, decimal_places=2, null=False)

    def mark_arrived(self, date_arrived: datetime) -> None:
        """
        As soon as an order arrives, we wipe the mailing address for privacy.
        """
        self.mailing_address = None
        self.date_arrived = date_arrived

    def clean(self) -> None:
        if self.mailing_address is not None and self.date_purchased is not None:
            raise ValidationError(
                "If an order has arrived, the mailing address must be cleared!"
            )

    def __str__(self):
        return f'Order #{self.pk} from {self.email} with tag {self.order_tag}'


class OrderedItem(Model):
    item = ForeignKey(StoreItem, on_delete=CASCADE)
    order = ForeignKey(Order, on_delete=CASCADE)
    quantity = IntegerField()
    unit_price_usd = DecimalField(max_digits=10, decimal_places=2, null=False)
    """In case supplier prices change between orders."""

    def __str__(self):
        return f'OrderedItem: {self.item} x {self.quantity} @ {self.unit_price_usd} of #{self.order.id}'

