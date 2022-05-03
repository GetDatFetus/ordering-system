import uuid
from datetime import datetime

from django.db import IntegrityError
from django.db.models import Model
from django.db.models.deletion import CASCADE
from django.db.models.fields import BooleanField, CharField, DateField, DecimalField, EmailField, IntegerField, TextField, URLField, UUIDField
from django.db.models.fields.related import ForeignKey


class StoreItem(Model):
    title = CharField(max_length=100, null=False)
    description = TextField()

    date_added = DateField(auto_now_add=True)
    visible = BooleanField(default=True, null=False)
    active = BooleanField(default=True, null=False)

    source_url = URLField(max_length=256)
    price_usd = DecimalField(decimal_places=2, null=False)


class ItemList(Model):
    """A generic list of items, not associated with anything."""
    pass


class ItemListEntry(Model):
    item = ForeignKey(StoreItem, on_delete=CASCADE)
    list = ForeignKey(ItemList, on_delete=CASCADE)
    quantity = IntegerField()


class Order(Model):
    email = EmailField(null=False)

    mailing_address = TextField(max_length=1024, null=True)
    price_xmr = DecimalField(max_digits=40, decimal_places=20)

    date_placed = DateField(auto_now_add=True)
    date_paid = DateField()
    date_purchased = DateField()
    date_arrived = DateField()

    order_tag = UUIDField(default=uuid.uuid4, null=False)
    """Used to associate incoming transactions to orders."""

    items = ForeignKey(ItemList, on_delete=CASCADE)

    def mark_arrived(self, date_arrived: datetime):
        """
        As soon as an order arrives, we wipe the mailing address for privacy.
        """
        self.mailing_address = None
        self.date_arrived = date_arrived

    def save(self, *args, **kwargs):
        if self.mailing_address is not None and self.date_arrived is not None:
            raise IntegrityError(
                "If an order has arrived, the mailing address must be cleared!"
            )

        super(Order, self).save(*args, **kwargs)

