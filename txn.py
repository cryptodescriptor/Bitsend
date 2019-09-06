import struct, web, utils, ecdsa
from keys import dbl256
import keys

class tx(object):
  def __init__(self, cfg, fee, testnet):
    self.cfg = cfg
    self.sweep = self.config_type()
    self.testnet = testnet
    self.web = web.web_api(testnet=self.testnet)
    self.marker = "00"
    self.flag = "01"
    self.hashtype = "01000000"
    self.input_vals = []

    self.raw = { 
      "nVersion": self.p("I", 1), 
      "txin": {
        "count":"",
        "hash":[],
        "index":[],
        "scriptSig":[],
        "sequence":[]
      }, 
      "txout": {
        "count":"",
        "amount":[], 
        "pks":[]
      },
      "nLocktime": "00000000"
    }

    self.rtxin = self.raw["txin"]
    self.rtxout = self.raw["txout"]

    self.fee = fee
    self.my_addr = self.cfg[0][0]
    self.my_pk = self.cfg[0][1].decode("hex")

    self.get_inputs()
    self.outputs = self.calculate_outputs()

  def exit_yn(self, raw_input_str):
    if not raw_input(raw_input_str).lower() == "y":
      exit()

  def init_sweep(self):
    self.addr_val = self.cfg[1]
    self.exit_yn("Are you sure you want to send? [y]: ")

  def init_send(self):
    self.sweep_to = self.cfg[1]
    self.exit_yn("Confirm sweep [y]: ")

  def config_type(self):
    if type(self.cfg[1]) == dict:
      self.init_sweep()
      return False
    elif type(self.cfg[1]) == str:
      self.init_send()
      return True

    raise keys.IllegalArgumentError("Bad config format!")

  def p(self, fmt, x):
    return struct.pack("<"+fmt, x).encode("hex")

  def flip(self, x):
    return x.decode("hex")[::-1].encode("hex")

  def encode_amount(self, sats):
    return struct.pack("<Q", sats).encode("hex")

  def varint(self, i):
    if i < 0xfd: # 253
      return self.p("B", i)
    """ change to "ff" p("Q") 
    if need HUGE amounts of ins/outs"""
    return "fd" + self.p("H", i)

  def varstr(self, s):
    l = len(s)
    s = s.encode("hex")
    if l < 0xfd:
      return self.p("B", l) + s
    return "fd" + self.p("H", l) + s

  def is_legacy(self, addr):
    f = addr[:1]
    return f == "1" or f in ("m", "n")

  def is_bech32(self, addr):
    f = addr[:3]
    return f == "bc1" or f == "tb1"

  def is_p2sh(self, addr):
    f = addr[:1]
    return f == "3" or f == "2"

  def get_program(self, addr, compr=True):
    if self.is_bech32(addr):
      return utils.get_witness(addr, testnet=self.testnet)
    elif self.is_p2sh(addr):
      return keys.get_keyhash(self.my_pk, compr)
    elif self.is_legacy(addr):
      return utils.b58_check(addr)
    else:
      self.raise_unsupported_addr(addr)

  def raise_unsupported_addr(self, addr):
    raise utils.UnsupportedFormat(
      "Error: Unfamiliar with this address: " + addr
    )

  def get_pks(self, addr):
    if self.is_legacy(addr):
      pks = utils.p2pkh(addr)
    elif self.is_p2sh(addr):
      pks = utils.p2sh_p2wpkh(addr)
    elif self.is_bech32(addr):
      pks = utils.p2wpkh(addr, testnet=self.testnet)
    else:
      self.raise_unsupported_addr()
    return self.varstr(pks)

  def btc_to_sats(self, btc):
    return int(round(btc*100000000))

  def set_total_sweep_amount(self):
    amount = 0

    for a in self.input_vals:
      amount += a

    amount = amount - self.fee
    amount = self.encode_amount(amount)
    pks = self.get_pks(self.sweep_to)
    self.rtxout["amount"].append(amount)
    self.rtxout["pks"].append(pks)

  def set_total_amount(self):
    outputs_total = 0

    for address in self.addr_val:
      amount = self.btc_to_sats(self.addr_val[address])
      a = self.encode_amount(amount)
      pks = self.get_pks(address)
      outputs_total += amount
      self.rtxout["amount"].append(a)
      self.rtxout["pks"].append(pks)

    # calculate change output
    inputs_tot = self.tot_input_val
    change = inputs_tot-(outputs_total+self.fee)

    if change > 0:
      pks = self.get_pks(self.my_addr)
      a = self.encode_amount(change)
      self.rtxout["amount"].append(a)
      self.rtxout["pks"].append(pks)

  def calculate_outputs(self):
    if self.sweep == True:
      self.set_total_sweep_amount()
    elif self.sweep == False:
      self.set_total_amount()

    self.outcount = len(self.rtxout["pks"])
    self.rtxout["count"] = self.varint(self.outcount)

  def get_inputs(self):
    if self.sweep == True:
      inputs = self.web.select_all_outs(
        addr=self.my_addr, fee=self.fee
      )

      return self.parse_inputs(inputs)

    # not sweeping below
    inputs_total = 0

    for a in self.addr_val:
      inputs_total += self.btc_to_sats(self.addr_val[a])

    inputs = self.web.select_outputs(
      sats=inputs_total, addr=self.my_addr, fee=self.fee
    )

    self.parse_inputs(inputs)

  def parse_inputs(self, inputs):
    self.tot_input_val = 0

    for i in inputs:
      self.rtxin["hash"].append(self.flip(i["txid"]))
      self.rtxin["index"].append(self.p("I", i["n"]))
      self.rtxin["scriptSig"].append("00")
      self.rtxin["sequence"].append("ffffffff")
      self.tot_input_val += i["value_int"]
      self.input_vals.append(i["value_int"])

    self.incount = len(self.rtxin["hash"])
    self.rtxin["count"] = self.varint(self.incount)

  def create_sequence_and_prevouts(self):
    sequence = prevouts = ""

    for i in range(self.incount):
      outpoint = self.rtxin["hash"][i] + self.rtxin["index"][i]
      prevouts += outpoint
      sequence += self.rtxin["sequence"][i]

    return sequence, prevouts

  def create_outputs(self):
    outputs = ""

    for i in range(self.outcount):
      # amount + pks (outputs)
      output = self.rtxout["amount"][i] + self.rtxout["pks"][i]
      outputs += output

    return outputs

  def create_pre_images(self, witness_prog, hashes):
    scriptCode = "76a914"+witness_prog+"88ac"
    sc_len = self.varint(len(scriptCode)/2)

    PreImages = []

    for i in range(self.incount):
      PreImages.append(
        self.raw["nVersion"] +
        hashes[0].encode("hex") + 
        hashes[1].encode("hex") +
        self.rtxin["hash"][i] +
        self.rtxin["index"][i] +
        sc_len + scriptCode +
        self.p("Q", self.input_vals[i]) +
        self.rtxin["sequence"][i] +
        hashes[2].encode("hex") +
        self.raw["nLocktime"] +
        self.hashtype
      )

    return PreImages

  def sign_pre_images(self, PreImages, sk):
    signatures = []

    for image in PreImages:
      sigHash = dbl256(image.decode("hex"))
      signature = keys.sign(sk, sigHash)
      sig_type = signature.encode("hex") + "01"
      signatures.append(sig_type)

    return signatures

  def get_scriptsig(self, witness_prog):
    if self.is_bech32(self.my_addr):
      # Bech32 scriptSig is always 00
      return "00"
    else:
      # p2sh-p2wpkh scriptSig = redeemScript push
      scriptSig = "160014" + witness_prog
      ss_len = len(scriptSig)/2
      return self.varint(ss_len) + scriptSig

  def serialize_inputs(self, witness_prog):
    inputs = self.rtxin["count"]

    for i in range(self.incount):
      inputs += self.rtxin["hash"][i]
      inputs += self.rtxin["index"][i]

      # scriptSig
      inputs += self.get_scriptsig(witness_prog)

      # sequence
      inputs += self.rtxin["sequence"][i]

    return inputs

  def serialize_outputs(self):
    outputs = self.rtxout["count"]

    for i in range(self.outcount):
      outputs += self.rtxout["amount"][i]
      outputs += self.rtxout["pks"][i]

    return outputs

  def serialize_witnesses(self, signatures, my_publ):
    stack_count = self.p("B", 2)
    witness_count = len(signatures)

    my_publ = my_publ.encode('hex')
    publ_len = self.p("B", len(my_publ)/2)

    witnesses = ""

    for i in range(witness_count):
      signature = signatures[i]
      witnesses += stack_count
      signature_len = self.varint(len(signature)/2)
      witnesses += signature_len + signature
      witnesses += publ_len + my_publ

    return witnesses

  def sign_segwit_tx(self):
    sequence, prevouts = self.create_sequence_and_prevouts()
    outputs = self.create_outputs()

    # hashes
    hashPrevouts = dbl256(prevouts.decode("hex"))
    hashSequence = dbl256(sequence.decode("hex"))
    hashOutputs = dbl256(outputs.decode("hex"))

    # get witness program
    witness_prog = self.get_program(self.my_addr, True).encode("hex")

    # create pre-images
    hashes = [hashPrevouts, hashSequence, hashOutputs]
    PreImages = self.create_pre_images(witness_prog, hashes)

    # get signature key and public key
    sk, my_publ = keys.get_compressed_publ(self.my_pk)

    # sign pre-images individually
    signatures = self.sign_pre_images(PreImages, sk)

    # serialize transaction..
    signed_tx = self.raw["nVersion"]
    signed_tx += self.marker
    signed_tx += self.flag

    # inputs
    signed_tx += self.serialize_inputs(witness_prog)

    # outputs
    signed_tx += self.serialize_outputs()

    # witnesses
    signed_tx += self.serialize_witnesses(signatures, my_publ)

    # set locktime
    signed_tx += self.raw["nLocktime"]

    return signed_tx

  def sign_legacy_tx(self):
    transaction = self.raw["nVersion"]

    # inputs
    transaction += self.rtxin["count"]

    for i in range(self.incount):
      transaction += self.rtxin["hash"][i]
      transaction += self.rtxin["index"][i]
      transaction += "{"+str(i)+"}" # format
      transaction += self.rtxin["sequence"][i]

    # outputs
    transaction += self.serialize_outputs()

    # locktime and hashtype
    transaction += self.raw["nLocktime"]
    transaction += self.hashtype

    # signing
    is_compr = keys.is_compr_addr(self.my_addr, self.my_pk, self.testnet)

    if is_compr:
      sk, my_publ = keys.get_compressed_publ(self.my_pk)
    else:
      sk, my_publ = keys.get_uncompressed_publ(self.my_pk)

    my_program = self.get_program(self.my_addr, is_compr).encode("hex")

    scriptSig = "76a914" + my_program + "88ac"
    sc_len = self.varint(len(scriptSig)/2)
    scriptSig = sc_len + scriptSig

    scriptSigs = []

    my_publ = my_publ.encode("hex")
    publ_len = self.p("B", len(my_publ)/2)

    for i in range(self.incount):
      sign_this = self.format_scripts(transaction, i, scriptSig)
      sigHash = dbl256(sign_this.decode("hex"))
      sig_type = keys.sign(sk, sigHash).encode("hex") + "01"
      signature_len = self.varint(len(sig_type)/2)
      ss = signature_len + sig_type + publ_len + my_publ
      scriptSigs.append(ss)

    """ [:-8] to remove the sighashtype """
    signed_tx = self.replace_scriptsigs(transaction, scriptSigs)[:-8]

    return signed_tx

  def replace_scriptsigs(self, tx, scriptSigs):
    """Replaces all 00 with <sig><pub>"""
    for i, ss in enumerate(scriptSigs):
      ss_len = self.varint(len(ss)/2)
      replace = "{"+str(i)+"}"
      tx = tx.replace(replace, ss_len+ss)
    return tx

  def format_scripts(self, tx, index, replacer):
    """Replaces scriptSig at specified index
    with replace param. Otherwise replaces with 00"""
    for i in range(self.incount):
      replace = "{"+str(i)+"}"
      if i != index:
        tx = tx.replace(replace, "00")
      else:
        tx = tx.replace(replace, replacer)
    return tx

  def signtx(self):
    if self.is_legacy(self.my_addr):
      return self.sign_legacy_tx()
    else:
      return self.sign_segwit_tx()

  def pushtx(self, tx):
    self.web.pushtx(tx)

  def do_tuple(self, tx, key):
    ret_str = ''
    name = key[0]
    values = key[1]

    # input/output
    io = tx[name]

    # add tx count to rtx
    ret_str += io['count'] + ' '

    # get input/output count
    count = len(io[values[0]])

    for i in range(count):
      for sub_key in values:
        ret_str += io[sub_key][i] + ' '

    return ret_str

  def return_raw(self, spaces=True):
    """ Returns the raw tx as a string """
    tx = self.raw

    keys = [
        "nVersion", 
        ("txin", ["hash", "index", "scriptSig",  "sequence"]), 
        ("txout", 
            ["amount", "pks"]), 
        "nLocktime"
      ]

    rtx_str = ''

    for key in keys:
      key_type = type(key)

      if type(key) == str:
        rtx_str += tx[key] + ' '
      elif type(key) == tuple:
        rtx_str += self.do_tuple(tx, key)

    if not spaces:
      return rtx_str.replace(' ', '')

    return rtx_str
