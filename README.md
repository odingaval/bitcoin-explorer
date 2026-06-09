# Bitcoin Blockchain Explorer

A simple command-line Bitcoin blockchain explorer that interacts with Bitcoin Core via JSON-RPC.

## Requirements

- Bitcoin Core running in regtest mode
- Python 3.x
- `requests` library

## Installation

```bash
pip install requests
```

## Configuration

The explorer connects to Bitcoin Core with these default settings:

- **URL**: `http://127.0.0.1:18443/`
- **Username**: `bootcamp`
- **Password**: `bootcamp123`

## Usage

```bash
python3 explorer_starter.py
```

## Functions

### `rpc(method, params, wallet)`
Base helper that sends JSON-RPC requests to Bitcoin Core. All other functions use this internally.

### `show_blockchain_info()`
Displays current blockchain status including chain type, block height and difficulty.

### `show_wallet_balance(wallet_name)`
Loads the specified wallet and prints its current BTC balance.

### `list_transactions(wallet_name, count)`
Lists the most recent transactions for a wallet showing direction (IN/OUT) and amount in BTC. Defaults to 5 transactions.

### `decode_transaction(txid)`
Decodes a raw transaction by txid, showing size, inputs (with coinbase detection) and outputs with addresses and amounts.

### `show_block(blockhash)`
Displays block details including height, hash, timestamp and transaction count. Defaults to the latest block if no hash is provided.

## Network

Designed for **regtest** mode on port `18443`. For testnet or mainnet change the port in the `rpc()` function.
