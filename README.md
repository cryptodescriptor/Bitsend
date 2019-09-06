# Segwit Compatible Multi-Address Transaction Maker/Sender/Parser (Python 2.7.x) 

This library intends to make it easy to make it easy to create a Segwit/Legacy transaction automatically using a simple config that consists of your address, private key, and recipient addresses. I started this project to gain more of an insight about how Bitcoin works under the hood.

The library uses [Smartbit API](https://www.smartbit.com.au) to collect input data and to push transacions.

Supported address types:
* p2pkh (compressed/uncompressed)
* p2sh-p2wpkh (address starting with 3)
* p2wpkh (bech32)

**This library does not support Multisig/custom p2sh transactions nor p2pk (not to be confused with p2pkh)!**

## Installation

Use the package manager [pip](https://pip.pypa.io/en/stable/) to install the project dependencies.

```bash
pip install ecdsa, requests
```
Then download the .zip and extract the files into {pythondir}\Lib\site-packages\\{custom folder}

## Usage

```python
import keys, web
from txn import tx

my_addr = "mmJi9zWYjRSCpEFPGQox7sVAZxLV9SACbr"
my_wif = "L1S4PyopJDLC1LZWchnqhWJrkbn8rF2PR2imydPum3VKWaZY8JFv"

# convert WIF (wallet import format) to privkey
my_pk = keys.wif_to_pk(my_wif).encode("hex")

# amounts are always in full BTC
cfg = [
  [my_addr, my_pk],
  { 
  "2NFfq2QzgbEtRSAHbMNzTQ68YsLD3BNF8ve": 0.001,
  "tb1q8alltexekdkteem3nyzr6h84rd0mf6x3vhf9nt": 0.00120000
  }
]

# use the configuration format below to sweep an address
"""
SWEEP ALL

cfg = [
  [my_addr, my_pk],
  "2NFfq2QzgbEtRSAHbMNzTQ68YsLD3BNF8ve"
]
"""

w = web.web_api(testnet=True)

# retrieve and print balance
print "Balance: " + str(w.get_balance(my_addr))

# fee is always in satoshis (create tx object)
t = tx(cfg=cfg, fee=19600, testnet=True)

# print raw tx with spaces to make it easier to read
print "\n" + t.return_raw(spaces=True) + "\n"

# sign the transaction
signed = t.signtx()

print signed + "\n"

# push the transaction to smartbit
t.pushtx(signed)
```
## What's More?

There is more to this module than sending Bitcoin. It also comes with a built-in signed tx parser. This can be found in the "parse test" folder.

### Usage
Just put the transaction you wish to be parsed inside the tx.txt file and run test.py. **Warning! The test parser will only parse the first 10 transactions unless you change the "stop" limit in test.py**. 

```html
Segwit: True
txn version: 1
Flag: 0001

------------------------------------------------------------
Inputs: 2
------------------------------------------------------------

(1)
Previous txn hash: 9f96ade4b41d5433f4eda31e1738ec2b36f6e7d1420d94a6af99801a88f7f7ff
Index: 0
sigScript: 4830450221008b9d1dc26ba6a9cb62127b02742fa9d754cd3bebf337f7a55d114c8e5cdd30be0220405
29b194ba3f9281a99f2b1c0a19c0489bc22ede944ccf4ecbab4cc618ef3ed01
Sequence: eeffffff

(2)
Previous txn hash: 8ac60eb9575db5b2d987e29f301b5b819ea83a5c6579d282d189cc04b8e151ef
Index: 1
sigScript:
Sequence: ffffffff

------------------------------------------------------------
Outputs: 2
------------------------------------------------------------

(1)
Value (satoshis): 112340000
pubKeyScript: 76a9148280b37df378db99f66f85c95a783a76ac7a6d5988ac

(2)
Value (satoshis): 223450000
pubKeyScript: 76a9143bde42dbee7e4dbe6a21b2d50ce2f0167faa815988ac

--------------------

Witness Count: 2

(1)
Witness:

(2)
Witness: 304402203609e17b84f6a7d30c80bfa610b5b4542f32a8a0d5447a12fb1366d7f01cc44a0220573a954
c4518331561406f90300e8f3358f51928d43c212a8caed02de67eebee01 025476c2e83188368da1ff3e292e7aca
fcdb3566bb0ad253f62fc70f07aeee6357
--------------------

Locktime: 17
```

## Address Creation

Samples of address creation can be found in "create test" folder. Here is a short snippet of that file:

```python
""" Generate mainnet p2pkh address using compressed public key """
a, pk, wif = keys.generate_addr(atype="p2pkh", testnet=False, compressed=True)

""" Generate mainnet p2pkh address using un-compressed public key """
a, pk, wif = keys.generate_addr(atype="p2pkh", testnet=False, compressed=False)

```
## Future Plans
In the future I would like to make the fee selection automatic to save the user having to entering a fee when creating the tx object.

## Disclaimer
I am not responsible for any loss of funds that may occur from either improper use of the software or any unforseen bugs. I have tested all use cases but there is always the possibility something slipped under my radar.

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## License
[MIT](https://choosealicense.com/licenses/mit/)