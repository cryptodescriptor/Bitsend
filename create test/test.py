import sys
sys.path.append("..")

import keys

types = ["p2pkh", "p2sh-p2wpkh", "bech32"]

""" Generate all 3 address types """

for t in types:
  a, pk, wif = keys.generate_addr(atype=t, testnet=True, compressed=True)
  print "-"*25
  print "Address Type: " + t
  print "-"*25 + "\n"
  print "Address: " + a
  print "Priv Key: " + pk
  print "WIF: " + wif + "\n"

""" Generate all 3 address types using provided Privkey (pk) """

priv_key = "7db3bdfa33737423207c549c279dd8a25e37221c2d109b4c1b1525940ac3f4cb".decode("hex")

for t in types:
  a, pk, wif = keys.generate_addr(atype=t, testnet=True, compressed=True, pk=priv_key)
  print "-"*25
  print "Address Type: " + t
  print "-"*25 + "\n"
  print "Address: " + a
  print "Priv Key: " + pk
  print "WIF: " + wif + "\n"

print "-"*25

""" Generate mainnet p2pkh address using compressed public key """
a, pk, wif = keys.generate_addr(atype="p2pkh", testnet=False, compressed=True)
print "compressed p2pkh (mainnet): " + a

""" Generate mainnet p2pkh address using un-compressed public key """
a, pk, wif = keys.generate_addr(atype="p2pkh", testnet=False, compressed=False)
print "un-compressed p2pkh (mainnet): " + a

""" Generate testnet p2pkh address using provided private key and un-compressed
public key """
a, pk, wif = keys.generate_addr(atype="p2pkh", testnet=True, compressed=False, pk=priv_key)
print "un-compressed p2pkh (testnet): " + a


""" Check if address is using a compressed public key (testnet) """
print "Is Compressed?: " + str(keys.is_compr_addr(addr=a, pk=pk.decode("hex"), testnet=True))
