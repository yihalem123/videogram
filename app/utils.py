import requests
from django.conf import settings
from .models import User
from bip32utils import BIP32Key

def generate_btc_address_for_user(user_id):
    xpub = settings.XPUB
    master_key = BIP32Key.fromExtendedKey(xpub)
    # Derivation path m/0/<user_id>
    child_key = master_key.ChildKey(0).ChildKey(user_id)
    return child_key.Address()

def check_payments():
    rpc_url = settings.BITCOIN_RPC_URL
    rpc_user = settings.BITCOIN_RPC_USER
    rpc_pass = settings.BITCOIN_RPC_PASS

    headers = {'content-type': 'text/plain;'}

    for user in User.objects.filter(is_premium=False, btc_address__isnull=False):
        payload = {
            "method": "getreceivedbyaddress",
            "params": [user.btc_address, 1],
            "id": 1
        }
        response = requests.post(rpc_url, json=payload, auth=(rpc_user, rpc_pass), headers=headers)
        if response.status_code == 200:
            result = response.json().get('result', 0)
            if result >= 0.0005:
                user.is_premium = True
                user.save()
