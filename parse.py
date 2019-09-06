import struct

def flip(hex):
  return hex.decode("hex")[::-1].encode("hex")

def uint4(uint):
  return struct.unpack("<I", uint.decode("hex"))[0]

def decode_amount(sats):
  return struct.unpack("<Q", sats.decode("hex"))[0]

class parser(object):
  def __init__(self, tx_data):
    self.tx = tx_data
    self.pnt = 0

  def consume(self, bytes):
    bytes = self.pnt+(bytes*2)
    ret = self.tx[self.pnt:bytes]
    self.pnt = bytes
    return ret

  def backtrack(self, minus):
    self.pnt-=(minus*2)

  def get_varint(self):
    x = self.consume(1)
    if x == "fd":
      return self.get('H')
    elif x == "fe":
      return self.get('I')
    elif x == "ff":
      return self.get('Q')
    x = x.decode("hex")
    return struct.unpack("<B", x)[0]

  def get(self, fmt):
    tlen = struct.calcsize("<" + fmt)
    con = self.consume(tlen).decode("hex")
    return struct.unpack("<"+fmt, con)[0]

class txn(object):
  def __init__(self, tx_data):
    self.tx_data = tx_data
    self.witnesses = None
    self.witness_count = None

    """ segwit, version, flag, input_count, 
    inputs, output_count, outputs, 
    witness_count, witnesses, locktime
    """
  def parse(self):
    tx = parser(self.tx_data)

    version = self.version = uint4(tx.consume(bytes=4))
    flag = self.flag = tx.consume(bytes=2)
    self.segwit = segwit = False

    if flag == "0001":
      segwit = self.segwit = True
    else:
      flag = self.flag = "00"
      tx.backtrack(minus=2)

    # parsing inputs
    input_count = self.input_count = tx.get_varint()

    inputs = self.inputs = { 
      "hash" : {}, 
      "index" : {}, 
      "script_len" : {}, 
      "sigScript" : {}, 
      "sequence" : {} 
    }

    for i in range(input_count):
      hash = flip(tx.consume(bytes=32))
      inputs["hash"][i] = hash
      inputs["index"][i] = uint4(tx.consume(bytes=4))
      script_len = tx.get_varint()
      inputs["script_len"][i] = script_len
      inputs["sigScript"][i] = tx.consume(bytes=script_len)
      inputs["sequence"][i] = tx.consume(bytes=4)

    # parsing outputs
    output_count = self.output_count = tx.get_varint()

    outputs = self.outputs = { 
      "value" : {}, 
      "script_len" : {}, 
      "pubKeyScript" : {} 
    }

    for i in range(output_count):
      val = tx.consume(bytes=8)
      outputs["value"][i] = decode_amount(val)
      script_len = tx.get_varint()
      outputs["script_len"][i] = script_len
      outputs["pubKeyScript"][i] = tx.consume(script_len)

    if segwit:
      # parsing witnesess
      witness = self.witness = { 
        "witness" : {}, 
        "witness_len" : {} 
      }
      
      witness_count = self.witness_count = len(self.inputs["hash"])

      for i in range(witness_count):
        stack_count = tx.get_varint()
        w = ""
        for i1 in range(stack_count):
          witness_len = tx.get_varint()
          w+=tx.consume(witness_len) + " "
        witness["witness"][i] = w.rstrip()

    locktime = self.locktime = uint4(tx.consume(4))