import requests
from django.conf import settings
from .models import User
from bip32utils import BIP32Key

def generate_btc_address_for_user(user_id):
    """Generate a unique Bitcoin address for a user."""
    try:
        xpub = settings.XPUB
        master_key = BIP32Key.fromExtendedKey(xpub)

        if isinstance(user_id, int):
            user_id = str(user_id)  # Convert to string if it's an integer

        index = int(user_id) if user_id.isdigit() else int.from_bytes(user_id.encode(), 'big') % (2**31)
        child_key = master_key.ChildKey(0).ChildKey(index)
        return child_key.Address()
    except ValueError:
        raise ValueError(f"Invalid user_id: {user_id}")
    except Exception as e:
        raise Exception(f"Error generating BTC address: {str(e)}")

def check_payments():
    """Check payments for non-premium users and update their status if the payment is received."""
    rpc_url = settings.BITCOIN_RPC_URL
    rpc_user = settings.BITCOIN_RPC_USER
    rpc_pass = settings.BITCOIN_RPC_PASS

    headers = {'content-type': 'text/plain;'}
    threshold = 50000  # 0.0005 BTC in Satoshis

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
            if result * 1e8 >= threshold:  # Convert BTC to Satoshis for comparison
                user.is_premium = True
                user.save()
        except Exception as e:
            print(f"Error checking payments for {user.id}: {str(e)}")
