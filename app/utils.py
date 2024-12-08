import requests
from django.conf import settings
from .models import User
from bitcoinlib.keys import HDKey

def generate_btc_address_for_user(user_id):
    try:
        zpub = settings.ZPUB
        master_key = HDKey(zpub)

        if isinstance(user_id, int):
            user_id = str(user_id)

        index = int(user_id) if user_id.isdigit() else int.from_bytes(user_id.encode(), 'big') % (2**31)

        child_key = master_key.subkey_for_path(f"m/84h/0h/0h/0/{index}")

        return child_key.address(witness_type='p2wpkh')
    except ValueError:
        raise ValueError(f"Invalid user_id: {user_id}")
    except Exception as e:
        raise Exception(f"Error generating BTC address: {str(e)}")

def check_payments():
    rpc_url = settings.BITCOIN_RPC_URL
    rpc_user = settings.BITCOIN_RPC_USER
    rpc_pass = settings.BITCOIN_RPC_PASS

    headers = {'content-type': 'text/plain;'}
    threshold = 50000

    for user in User.objects.filter(is_premium=False, btc_address__isnull=False):
        payload = {
            "method": "getreceivedbyaddress",
            "params": [user.btc_address, 1],
            "id": 1
        }
        try:
            response = requests.post(rpc_url, json=payload, auth=(rpc_user, rpc_pass), headers=headers)
            response.raise_for_status()
            result = response.json().get('result', 0)
            if result * 1e8 >= threshold:
                user.is_premium = True
                user.save()
        except Exception as e:
            print(f"Error checking payments for {user.id}: {str(e)}")
