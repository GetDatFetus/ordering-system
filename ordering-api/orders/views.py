from orders.serializers import OrderSerializer, StoreItemSerializer, XMRExchangeRateSerializer
from rest_framework.decorators import api_view
from rest_framework.request import Request
from rest_framework.response import Response

from .models import *


@api_view(http_method_names=['POST'])
def place_order(request: Request) -> Response:
    w_ser = OrderSerializer(data=request.body)
    if not w_ser.is_valid():
        return Response(status=400)
    result = w_ser.save()

    return Response(OrderSerializer(result).data)


@api_view(http_method_names=['GET'])
def get_store_info(_: Request) -> Response:
    exchange_rate = XMRExchangeRate.current()
    items = StoreItem.objects.filter(visible=True).all()
    return Response({
        'exchange': XMRExchangeRateSerializer(exchange_rate).data,
        'items': StoreItemSerializer(items, many=True).data,
    })

