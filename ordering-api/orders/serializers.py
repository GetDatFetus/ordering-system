from rest_framework.relations import PrimaryKeyRelatedField
from rest_framework.serializers import ModelSerializer

from orders.models import Order, OrderedItem, StoreItem, XMRExchangeRate


class OrderedItemSerializer(ModelSerializer):
    item = PrimaryKeyRelatedField(
        queryset=StoreItem.objects.filter(
            visible=True,
            active=True,
        )
    )

    class Meta:
        model = OrderedItem
        fields = ['item', 'quantity']
        read_only_fields = ['unit_price_usd']


class OrderSerializer(ModelSerializer):
    items = OrderedItemSerializer(many=True)

    class Meta:
        model = Order
        fields = ['email', 'mailing_address', 'items']
        read_only_fields = [
            'xmr_per_usd_rate',
            'processing_fees',
            'order_tag',
            'date_placed'
        ]


class StoreItemSerializer(ModelSerializer):
    class Meta:
        model = StoreItem
        fields = [
            'title',
            'description',
            'date_added',
            'active',
            'supplier_url',
            'price_usd',
        ]


class XMRExchangeRateSerializer(ModelSerializer):
    class Meta:
        model = XMRExchangeRate
        fields = [
            'rate',
            'date_updated',
        ]


