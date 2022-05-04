from enum import IntEnum
from datetime import datetime
import enum
from typing import Optional

from django.core.exceptions import ValidationError
from django.db.models import Model
from django.db.models.deletion import CASCADE
from django.db.models.fields import BooleanField, CharField, DateField, DateTimeField, DecimalField, EmailField, FloatField, IntegerField, TextField, URLField
from django.db.models.fields.related import ForeignKey
from django.db.models.query import QuerySet


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
    @enum.unique
    class State(IntEnum):
        CREATED = 10
        PAID = 15

        PURCHASED = 20
        ARRIVED = 25

        COMPLETED = 30
        LOST = 40

    email = EmailField(max_length=64, null=False)
    mailing_address = TextField(max_length=256, null=True)

    state = IntegerField(default=State.CREATED, null=False)

    date_placed = DateTimeField(auto_now_add=True)
    date_paid = DateTimeField()
    date_purchased = DateTimeField()
    date_arrived = DateTimeField()

    xmr_address = CharField(max_length=105, null=False, unique=True)
    """Every order pays to a different address to identify transactions."""

    xmr_txn_hash = CharField(max_length=105, null=True)
    """Every order pays to a different address to identify transactions."""

    xmr_per_usd_rate = FloatField(null=False)
    """XMR exchange rate may change between orders."""

    processing_fees = DecimalField(max_digits=10, decimal_places=2, null=False)

    items: QuerySet['OrderedItem']

    def mark_paid(self, txn_hash: str, date: datetime) -> None:
        self.state = Order.State.PAID
        self.xmr_txn_hash = txn_hash
        self.date_paid = date

    def mark_purchased(self, date: datetime) -> None:
        self.state = Order.State.PURCHASED
        self.mailing_address = None
        self.date_purchased = date

    def mark_arrived(self, date: datetime) -> None:
        self.state = Order.State.ARRIVED
        self.date_arrived = date

    def clean(self) -> None:
        try:
            st = Order.State(self.state)
        except ValueError:
            raise ValidationError(f"Invalid order state value {self.state}")

        if self.items.count() == 0:
            raise ValidationError("Orders must have at least one item")

        if st in [Order.State.CREATED, Order.State.PAID]:
            if not self.mailing_address:
                raise ValidationError(
                    "CREATED and PAID orders must have mailing address set"
                )
        elif self.mailing_address:
            raise ValidationError(
                "Orders that have been purchased must have mailing address cleared"
            )

        if st < Order.State.PAID:
            self.date_paid = None
            self.xmr_txn_hash = None
        elif not all((self.date_paid, self.xmr_txn_hash)):
            raise ValidationError(f"State {st} missing fields")

        if st < Order.State.PURCHASED:
            self.date_purchased = None
        elif not all((self.date_purchased, self.date_paid, self.xmr_txn_hash)):
            raise ValidationError(f"State {st} missing fields")

        if st < Order.State.COMPLETED:
            self.date_arrived = None
        elif not all((
            self.date_arrived,
            self.date_purchased,
            self.date_paid,
            self.xmr_txn_hash,
        )):
            raise ValidationError(f"State {st} missing fields")

    def __str__(self):
        return f'Order #{self.pk} state={self.state} buyer={self.email}'


class OrderedItem(Model):
    item = ForeignKey(StoreItem, on_delete=CASCADE)
    order = ForeignKey(Order, on_delete=CASCADE)
    quantity = IntegerField()
    unit_price_usd = DecimalField(max_digits=10, decimal_places=2, null=False)
    """In case supplier prices change between orders."""

    def __str__(self):
        return f'OrderedItem: {self.item} x {self.quantity} @ {self.unit_price_usd} of #{self.order.id}'

