from flask import Flask, abort
import structlog
from monero.wallet import Wallet


_log = structlog.get_logger(__name__)

app = Flask(__name__)

app.config.from_envvar('CAS_CONFIG')

MONERO_RPC_HOST = app.config['MONERO_RPC_HOST']
MONERO_RPC_PORT = app.config['MONERO_RPC_PORT']
MONERO_RPC_USERNAME = app.config['MONERO_RPC_USERNAME']
MONERO_RPC_PASSWORD = app.config['MONERO_RPC_PASSWORD']

MONERO_TXN_MAX_HEIGHT = app.config['MONERO_TXN_MAX_HEIGHT']


@app.route("/api/addresses", methods = ['POST'])
def create_address():
    wallet = get_wallet()
    _log.info("Creating subaddress")
    address, _ = wallet.new_address()
    _log.info("Created subaddress", address=address)
    return str(address)


@app.route("/api/addresses/<address>", methods = ['GET'])
def get_address_info(address: str):
    log = _log.bind(address=address)
    log.info("Fetching incoming transactions")
    
    wallet = get_wallet()

    try:
        incoming_payments = wallet.incoming(
            local_address=address,
            max_height=MONERO_TXN_MAX_HEIGHT,
            confirmed=True,
        )
    except ValueError:
        log.warn("Address does not exist")
        return abort(404)

    total_received = sum((p.amount for p in incoming_payments))

    # Use last transaction as the source of information
    txn_hash = (
        incoming_payments[-1].hash
        if len(incoming_payments) > 0
        else None
    )

    _log.info(
        "Received transaction info",
        n_payments=len(incoming_payments),
        xmr_received=total_received,
        txn_hash=txn_hash,
    )
    return {
        'transaction': txn_hash,
        'total_xmr': total_received,
    }


def get_wallet():
    return Wallet(
        host = MONERO_RPC_HOST,
        port = MONERO_RPC_PORT,
        user = MONERO_RPC_USERNAME,
        password = MONERO_RPC_PASSWORD,
    )

