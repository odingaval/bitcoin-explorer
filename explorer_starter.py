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

# ── original functions ────────────────────────────────────────────────────────

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
        direction = "IN" if tx['category'] in ('receive', 'generate', 'immature') else "OUT"
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

# ── UTXO set for a wallet ───────────────────────────────────────────

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

# ── total fees in a block ───────────────────────────────────────────

def show_block_fees(blockhash=None):
    """
    Calculate total fees collected in a block.

    Strategy: for every non-coinbase transaction, sum(inputs) - sum(outputs)
    is the fee. We fetch each raw tx with verbosity=2 so Bitcoin Core resolves
    the previous outputs inline, avoiding a second RPC call per input.
    """
    if blockhash is None:
        blockhash = rpc("getbestblockhash")['result']

    # verbosity=2 returns the full block with decoded transactions
    block = rpc("getblock", [blockhash, 2])['result']

    print(f"\n=== Fees in block #{block['height']} ===")
    print(f"Hash : {block['hash'][:32]}...")
    print(f"Txns : {block['nTx']}")

    total_fees = 0.0
    tx_fees = []

    for tx in block['tx']:
        # skip coinbase — it has no inputs spending previous outputs
        if 'coinbase' in tx['vin'][0]:
            continue

        input_total = sum(
            vin['prevout']['value']
            for vin in tx['vin']
            if 'prevout' in vin          # verbosity=2 attaches prevout
        )
        output_total = sum(vout['value'] for vout in tx['vout'])
        fee = input_total - output_total

        if fee >= 0:                     # guard against rounding artefacts
            total_fees += fee
            tx_fees.append((tx['txid'], fee))

    # print top-5 fee payers
    tx_fees.sort(key=lambda x: x[1], reverse=True)
    print("\n  Top fee-paying transactions:")
    for txid, fee in tx_fees[:5]:
        print(f"  {txid[:32]}...  {fee:.8f} BTC")

    print(f"\n  Total fees collected : {total_fees:.8f} BTC")
    print(f"  Average fee per tx   : {total_fees / max(len(tx_fees), 1):.8f} BTC")

# ── search transactions by address ──────────────────────────────────

def search_transactions_by_address(address, wallet_name=None, count=100):
    """
    Find all transactions that involve a given address.

    Two approaches are tried:
      1. If a wallet_name is given, scan listtransactions for the wallet and
         filter by address — fast and works with watch-only wallets too.
      2. Without a wallet, scan the mempool + recent blocks using
         scantxoutset for the current UTXO, then look up each tx.
    """
    print(f"\n=== Transactions for address: {address} ===")
    matches = []

    if wallet_name:
        try:
            rpc("loadwallet", [wallet_name])
        except:
            pass
        txs = rpc("listtransactions", ["*", count, 0, True], wallet=wallet_name)['result']
        matches = [tx for tx in txs if tx.get('address') == address]
    else:
        # scantxoutset finds UTXOs but not spent history;
        # for a full node we'd use getaddressinfo + scanblocks (v24+).
        # Here we do a best-effort UTXO scan.
        result = rpc("scantxoutset", ["start", [f"addr({address})"]])['result']
        utxos = result.get('unspents', [])
        for u in utxos:
            matches.append({
                'txid':     u['txid'],
                'vout':     u['vout'],
                'amount':   u['amount'],
                'category': 'utxo',
                'address':  address,
            })

    if not matches:
        print("  No transactions found for this address.")
        return

    received = sum(t['amount'] for t in matches if t.get('category') in ('receive', 'generate', 'immature', 'utxo'))
    sent     = sum(abs(t['amount']) for t in matches if t.get('category') == 'send')

    for tx in matches:
        direction = "IN " if tx.get('category') in ('receive', 'generate', 'immature', 'utxo') else "OUT"
        txid_short = tx['txid'][:32] + "..."
        print(f"  {direction}  {tx['amount']:+.8f} BTC  txid: {txid_short}")

    print(f"\n  Found {len(matches)} transaction(s)")
    print(f"  Total received : {received:.8f} BTC")
    print(f"  Total sent     : {sent:.8f} BTC")
    print(f"  Net balance    : {received - sent:.8f} BTC")

# ── main ──────────────────────────────────────────────────────────────────────

show_blockchain_info()
show_wallet_balance("alice")
list_transactions("alice")

txs = rpc("listtransactions", ["*", 1], wallet="alice")
if txs['result']:
    txid = txs['result'][0]['txid']
    print(f"\n=== Decoding tx: {txid[:20]}... ===")
    decode_transaction(txid)

show_block()

# bonus features
show_utxo_set("alice")
show_block_fees()                    # uses latest block; pass a hash to target one

# for search_transactions_by_address you need an address — grab one from alice
addrs = rpc("listaddressgroupings", [], wallet="alice")['result']
if addrs:
    alice_addr = addrs[0][0][0]      # first address in first group
    search_transactions_by_address(alice_addr, wallet_name="alice")