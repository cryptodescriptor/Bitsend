import ecdsa, hashlib, msqr, bech32
from base58 import b58decode, b58encode
from ecdsa.ecdsa import curve_secp256k1
from os import urandom
from hashlib import sha256

class InvalidECPointException(Exception):
  """e.g. not on curve, or infinity"""

class IllegalArgumentError(ValueError):
    """bad argument passed to function"""

class UnexpectedAddr(Exception):
  """addresses derived from pk does 
  not match supplied addr"""

def hash160(x):
  h = hashlib.new("ripemd160")
  h.update(sha256(x).digest())
  return h.digest()

def dbl256(x):
  return sha256(sha256(x).digest()).digest()

def bytes_to_int(bytes):
  return int(bytes.encode("hex"), 16)

def sign(sk, s256):
  while 1:
    sig = sk.sign_digest(s256, 
      sigencode=ecdsa.util.sigencode_der)
    N = sk.curve.generator.order()
    r, s = ecdsa.util.sigdecode_der(sig, N)
    if s < N/2:
      return sig

def get_y_from_x(x, odd=True):
  curve = curve_secp256k1
  _p = curve.p()
  _a = curve.a()
  _b = curve.b()
  y2 = (pow(x, 3, _p) + _a * x + _b) % _p
  y = msqr.modular_sqrt(y2, _p)
  if curve.contains_point(x, y):
    if odd == bool(y & 1):
      return y
    return _p - y
  raise InvalidECPointException()

def pk_to_wif(pk, compressed=True):
  pk_extended = b"\x80" + pk
  if compressed:
    pk_extended += b"\x01"
  pk256 = dbl256(pk_extended)
  checksum = pk256[:4]
  return b58encode(pk_extended + checksum)

def wif_to_pk(pk):
  s = -4
  if pk[:1] in ("K", "L"):
    s-=1
  return b58decode(pk)[1:s]

def assert_wif_checksum(wif):
  decoded = b58decode(wif)
  assert dbl256(decoded[:-4])[:4] == decoded[-4:]

def get_private_key():
  pk = urandom(32)
  wif = pk_to_wif(pk)
  assert_wif_checksum(wif)
  return pk, wif

def get_compressed_publ(pk):
  sk, vk = get_sk_vk_from_pk(pk)
  
  x, y = vk[:32], vk[32:]

  odd = bool(bytes_to_int(y) & 1)

  if not odd:
    compressed = b"\x02" + x
  else:
    compressed = b"\x03" + x

  get_y = get_y_from_x(bytes_to_int(x), odd)
  assert bytes_to_int(y) == get_y

  return sk, compressed

def get_uncompressed_publ(pk):
  sk, vk = get_sk_vk_from_pk(pk)
  return sk, b"\x04" + vk

def get_sk_vk_from_pk(pk):
  sk = ecdsa.SigningKey.from_string(pk, curve=ecdsa.SECP256k1)
  vk = sk.get_verifying_key().to_string()
  return sk, vk

def get_keyhash(pk, compressed=True):
  if compressed:
    publ = get_compressed_publ(pk)[1]
  else:
    publ = get_uncompressed_publ(pk)[1]
  keyhash = hash160(publ)
  return keyhash

def generate_p2pkh_address(testnet, keyhash):
  p = b"\x6F" if testnet else b"\x00"
  checksum = dbl256(p + keyhash)[:4]
  return b58encode(p + keyhash + checksum)

def generate_p2sh_p2wpkh_address(testnet, keyhash):
  p = b"\xC4" if testnet else b"\x05"
  redeemScript = b"\x00\x14" + keyhash
  script_hash = hash160(redeemScript)
  checksum = dbl256(p + script_hash)[:4]
  return b58encode(p + script_hash + checksum)

def generate_bech32_address(testnet, keyhash):
  p = "tb" if testnet else "bc"
  return bech32.encode(p, 0, bytearray(keyhash))

def generate_addr(atype, testnet=False, compressed=True, pk=None):
  # atype is either: "p2pkh", "p2sh-p2wpkh", bech32
  
  if compressed == False:
    assert(atype == "p2pkh")

  if not pk:
    pk, wif = get_private_key()
  else:
    wif = pk_to_wif(pk)

  keyhash = get_keyhash(pk, compressed=compressed)

  if atype == "p2pkh":
    addr = generate_p2pkh_address(testnet, keyhash)
  elif atype == "p2sh-p2wpkh":
    addr = generate_p2sh_p2wpkh_address(testnet, keyhash)
  elif atype == "bech32":
    addr = generate_bech32_address(testnet, keyhash)
  else:
    raise IllegalArgumentError("Unexpected atype.")

  return addr, pk.encode("hex"), wif

def is_compr_addr(addr, pk, testnet=False):
  """ Derive compressed and uncompressed addresses 
  from the provided priv key to compare with the 
  addr provided as an argument. returns True/False/Error."""

  comp = generate_addr(
    atype="p2pkh", testnet=testnet, compressed=True, pk=pk
  )[0]

  if addr == comp:
    return True

  uncomp = generate_addr(
    atype="p2pkh", testnet=testnet, compressed=False, pk=pk
  )[0]

  if addr == uncomp:
    return False

  raise UnexpectedAddr(
    "Addresses do not match. Did you provide the correct private key?"
  )
