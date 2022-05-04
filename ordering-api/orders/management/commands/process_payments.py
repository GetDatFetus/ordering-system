from datetime import datetime
from monero.backends.jsonrpc.wallet import JSONRPCWallet
from monero.wallet import Wallet

import logging
from django.conf import settings
from django.core.management.base import BaseCommand
from orders.models import Order


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Processes incoming monero transactions.'

    def handle(self, *_, **__):
        host=settings.MONERO_RPC_HOST
        port=settings.MONERO_RPC_PORT
        user=settings.MONERO_RPC_USERNAME
        password=settings.MONERO_RPC_PASSWORD

        self.stderr.write(
            f"Processing incoming payments using RPC {user}@{host}:{port}..."
        )
        wallet = Wallet(host=host, port=port, user=user, password=password)

        orders = Order.objects.filter(state=Order.State.CREATED)
        self.stderr.write(f"{orders.count()} orders to process")

        for order in orders:
            total_price = order.total_price()

            self.stderr.write(f"Order #{order.pk} expected XMR{total_price}")
            self.stderr.write(f"  Address {order.address}")

            incoming_payments = wallet.incoming(
                local_address=order.address,
                max_height=settings.MONERO_TXN_MAX_HEIGHT,
                confirmed=True,
            )
            total_received = sum((p.amount for p in incoming_payments))
            self.stderr.write(
                f"  Got XMR{total_received} over {len(incoming_payments)} payments"
            )

            if total_received < total_price:
                self.stderr.write(f"  Did not receive enough payment, skipping")
                break
            
            # Use last transactio as the source of information
            txn = incoming_payments[-1]

            self.stderr.write(
                f"  Received enough payment, marking it as purchased"
            )
            order.mark_paid(
                txn_hash=txn.hash,
                date=datetime.now()
            )
            order.full_clean()
            order.save()

        self.stderr.write("Done.")

