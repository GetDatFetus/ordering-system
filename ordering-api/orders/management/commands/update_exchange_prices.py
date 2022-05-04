import requests
import logging
from django.core.management.base import BaseCommand
from orders.models import XMRExchangeRate


logger = logging.getLogger(__name__)

API_URL = 'https://min-api.cryptocompare.com/data/price'


class Command(BaseCommand):
    help = 'Updates the USD/XMR exchange rate.'

    def handle(self, *_, **__):
        self.stderr.write("Querying cryptocompare.com...")
        
        response = requests.get(
            API_URL,
            params={'fsym': 'USD', 'tsyms': 'XMR'}
        )
        data = response.json()
        self.stderr.write(f"Got JSON response {repr(data)}")

        rate = data['XMR']
        obj = XMRExchangeRate.objects.create(rate=rate)
        self.stderr.write(f"Created entry {obj}")

