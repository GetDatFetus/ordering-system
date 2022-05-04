from enum import IntEnum
from datetime import datetime
import enum
from typing import Optional

from django.core.exceptions import ValidationError
from django.db.models import Model
from django.db.models.deletion import CASCADE, PROTECT
from django.db.models.fields import BinaryField, BooleanField, CharField, DateField, DateTimeField, DecimalField, EmailField, IntegerField, TextField, URLField
from django.db.models.fields.related import ForeignKey
from django.db.models.query import QuerySet


class XMRExchangeRate(Model):
    """
    The exchange rate at a snapshot of time. This can be updated with the
    update_exchange_rate command.
    """

    date_updated = DateTimeField(auto_now_add=True, null=False)
    rate = DecimalField(max_digits=10, decimal_places=10, null=False)
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
    title = CharField(max_length=100, null=False, unique=True)
    url = URLField(max_length=256, null=False)

    def __str__(self):
        return f'Supplier: {self.title}'


class StoreItem(Model):
    title = CharField(max_length=100, null=False, unique=True)
    description = TextField()

    image = URLField(max_length=128, null=True)

    date_added = DateField(auto_now_add=True)
    visible = BooleanField(default=False, null=False)
    active = BooleanField(default=False, null=False)

    supplier = ForeignKey(Supplier, on_delete=PROTECT)
    supplier_url = URLField(max_length=256)
    price_usd = DecimalField(max_digits=10, decimal_places=2, null=False)

    def __str__(self):
        return f'StoreItem: {self.title} by {self.supplier}'


class EncryptKeys(Model):
    """
    PGP keys that the frontend can use to encrypt sensitive fields.
    """
    date_created = DateTimeField(auto_now_add=True, null=False)
    active = BooleanField(default=False, null=False)
    key = BinaryField(max_length=8192, null=False)


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
    encrypt_key = ForeignKey(EncryptKeys, on_delete=PROTECT, null=False)
    mailing_address = BinaryField(max_length=300, null=True)
    """
    The mailing address to send the order to, encrypted using one of the keys.

    This public-facing server does not handle plaintext mailing addresses
    because if it got compromised, they would be leaked. Plaintext mailing
    addresses must be handled elsewhere.
    """

    state = IntegerField(default=State.CREATED, null=False)

    date_placed = DateTimeField(auto_now_add=True)
    date_paid = DateTimeField()
    date_purchased = DateTimeField()
    date_arrived = DateTimeField()

    xmr_address = CharField(max_length=105, null=True, unique=True)
    """
    The address that we will expect money on for this order.

    Every order pays to a different address to identify and mask transactions.
    Since users may be ordering from custodial exchanges, it will be cleared as
    soon as payment is received for privacy purposes.
    """

    xmr_per_usd_rate = DecimalField(
        max_digits=10,
        decimal_places=10,
        null=False
    )
    """
    XMR exchange rate may change between orders. This freezes it for this order.
    """

    processing_fees = DecimalField(max_digits=10, decimal_places=2, null=False)
    """Additional fees applied to this order in USD."""

    items: QuerySet['OrderedItem']  # related field

    def mark_paid(self, txn_hash: str, date: datetime) -> None:
        self.state = Order.State.PAID
        self.xmr_txn_hash = txn_hash
        self.date_paid = date
        self.xmr_address = None

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

        if st != Order.State.CREATED and self.xmr_address is not None:
            raise ValidationError(
                "Orders that have been paid for must have XMR address cleared"
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
    item = ForeignKey(StoreItem, on_delete=PROTECT)
    order = ForeignKey(Order, on_delete=CASCADE)
    quantity = IntegerField()
    unit_price_usd = DecimalField(max_digits=10, decimal_places=2, null=False)
    """In case supplier prices change between orders."""

    def __str__(self):
        return (
            f'OrderedItem: ${self.unit_price_usd} {self.item} x {self.quantity}'
            f' of #{self.order.id}'
        )

