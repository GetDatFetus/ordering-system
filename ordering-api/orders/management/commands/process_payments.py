import logging
from datetime import datetime
from urllib.parse import urljoin

from django.conf import settings
from django.core.management.base import BaseCommand
from orders.models import Order
from requests import Session, RequestException


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Processes incoming monero transactions.'

    def handle(self, *_, **__):
        base_url = settings.CAS_BASE_URL
        self.stdout.write(f"base_url: {base_url}")

        orders = Order.objects.filter(state=Order.State.CREATED)
        self.stdout.write(f"to_process: {orders.count()}")

        with Session() as s:
            for order in orders:
                expected = order.total_price()

                self.stdout.write(f" - order: #{order.pk}")
                self.stdout.write(f"   expected: {expected}")
                self.stdout.write(f"   address: {order.address}")

                try:
                    response = s.get(
                        urljoin(base_url, f'/api/addresses/{order.address}')
                    )
                except RequestException as e:
                    self.stderr.write(repr(e))
                    continue

                data = response.json()
                received = data['total_xmr']
                txn_hash = data['txn_hash']

                self.stdout.write(f"  received: {received}")
                self.stdout.write(f"  txn_hash: {txn_hash}")
                if received < expected:
                    self.stdout.write(f"   paid: no")
                    break

                self.stdout.write(f"  paid: yes")
                order.mark_paid(txn_hash=txn_hash, date=datetime.now())
                order.full_clean()
                order.save()

            self.stderr.write("Done")

