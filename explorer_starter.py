import requests, json

def rpc(method, params=None, wallet=None):
    url = "http://127.0.0.1:18443/"
    if wallet:
        url = f"{url}wallet/{wallet}"
    data = json.dumps({
        "jsonrpc": "1.0", "id": "explorer",
        "method": method, "params": params or []
    })
    resp = requests.post(url, data=data, auth=("bootcamp", "bootcamp123"))
    return resp.json()

def show_blockchain_info():
    info = rpc("getblockchaininfo")
    print(f"Chain: {info['result']['chain']}")
    print(f"Blocks: {info['result']['blocks']}")
    print(f"Difficulty: {info['result']['difficulty']}")

def show_wallet_balance(wallet_name):
    try:
        rpc("loadwallet", [wallet_name])
    except:
        pass
    balance = rpc("getbalance", [], wallet=wallet_name)
    print(f"=== Wallet: {wallet_name} ===")
    print(f"{wallet_name} has {balance['result']} BTC")

def list_transactions(wallet_name, count=5):
    try:
        rpc("loadwallet", [wallet_name])
    except:
        pass
    txs = rpc("listtransactions", ["*", count], wallet=wallet_name)
    for tx in txs['result']:
        if tx['category'] in ('receive', 'generate', 'immature'):
            direction = "IN"
        else:
            direction = "OUT"
        print(f"{direction} {tx['amount']:+.8f} BTC")

def decode_transaction(txid):
    tx = rpc("getrawtransaction", [txid, True])['result']
    print(f"Size: {tx['size']} bytes")
    print("\nInputs:")
    for vin in tx['vin']:
        if 'coinbase' in vin:
            print("  COINBASE (mining reward)")
        else:
            print(f"  From: {vin['txid'][:20]}...")
    print("\nOutputs:")
    for vout in tx['vout']:
        addr = vout['scriptPubKey'].get('address', '?')
        print(f"  To: {addr}  Amount: {vout['value']:+.8f} BTC")

def show_block(blockhash=None):
    if blockhash is None:
        blockhash = rpc("getbestblockhash")['result']
    block = rpc("getblock", [blockhash, 1])['result']
    print(f"=== Block #{block['height']} ===")
    print(f"Hash: {block['hash'][:32]}...")
    print(f"Time: {block['time']}")
    print(f"Transactions: {block['nTx']}")

show_blockchain_info()
show_wallet_balance("alice")
list_transactions("alice")


txs = rpc("listtransactions", ["*", 1], wallet="alice")
if txs['result']:
    txid = txs['result'][0]['txid']
    print(f"\n=== Decoding tx: {txid[:20]}... ===")
    decode_transaction(txid)

show_block()

 
def show_utxo_set(wallet_name, min_confirmations=0):
    """
    List all unspent outputs for a wallet.
    Uses listunspent which returns each UTXO with its txid, vout index,
    address, amount, and confirmation count.
    """
    try:
        rpc("loadwallet", [wallet_name])
    except:
        pass
 
    utxos = rpc("listunspent", [min_confirmations, 9999999], wallet=wallet_name)['result']
 
    print(f"\n=== UTXO set: {wallet_name} ===")
    if not utxos:
        print("  No unspent outputs found.")
        return
 
    total = 0.0
    for u in utxos:
        confs = u['confirmations']
        status = "confirmed" if confs > 0 else "unconfirmed"
        print(f"  txid : {u['txid'][:32]}...")
        print(f"  vout : {u['vout']}")
        print(f"  addr : {u['address']}")
        print(f"  amt  : {u['amount']:.8f} BTC  ({confs} confs, {status})")
        print()
        total += u['amount']
 
    print(f"  Total spendable: {total:.8f} BTC across {len(utxos)} UTXO(s)")
 
show_utxo_set("alice")
