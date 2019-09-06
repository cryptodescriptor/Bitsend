import requests, json, operator

class JSONError(Exception):
  """expected a JSON response"""

class BalanceError(Exception):
  """not enough balance"""

class web_api(object):
  def __init__(self, testnet=False):
    api_prefix = "testnet-api" if testnet else "api"
    self.API = "https://{}.smartbit.com.au".format(api_prefix)
    self.output_url = self.API + "/v1/blockchain/address/{}/unspent?limit=1000"
    self.push_url = self.API + "/v1/blockchain/pushtx"
    self.BALANCE_API = self.API + "/v1/blockchain/address/{}/wallet"
    self.FEE_API = "https://bitcoinfees.earn.com/api/v1/fees/recommended"
    self.ua = "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/63.0"
    self.h = { "User-Agent" : self.ua }

  def no_btc_error(self):
    raise BalanceError("You have no bitcoin!")

  def insufficient_sats_error(self):
    raise BalanceError("Not enough satoshis!")

  def JSON_error(self, scode):
    err = "WebError: Expected a JSON " + \
      "response. Status code: %i" % scode
    raise JSONError(err)

  def is_json(self, j):
    try:
      json.loads(j)
    except ValueError:
      return False
    return True

  def check_json_error(self, j):
    try:
      msg = j["error"]["message"]
      code = j["error"]["code"]
      e = code + ": " + msg
    except KeyError:
    	e = "WebError: Status Code " + scode
    raise JSONError(e)

  def check_err(self, r):
    scode = r.status_code
    if not self.is_json(r.text):
      self.JSON_error(scode)
    try:
      j = r.json()
      if j["success"] == True:
        return j
    except KeyError:
    	pass
    self.check_json_error(j)

  def get_unspent(self, addr):
    r = requests.get(self.output_url.format(addr), 
    	headers=self.h)
    j = self.check_err(r)
    return j

  def select_outputs(self, sats, addr, fee):
    outputs = self.get_unspent(addr)["unspent"]

    if not outputs:
      self.no_btc_error()

    to_spend = sats + fee

    tot = 0
    smallest = None # index
    vals = {}

    # find the smallest possible output
    for i, o in enumerate(outputs):
      val = o["value_int"]
      vals[i] = val # index:value
      tot += val
      if val >= to_spend and val < smallest:
        smallest = i

    if tot < to_spend:
      self.insufficient_sats_error()

    if smallest != None:
      return [outputs[smallest]]

    # all outputs are too small to cover the cost. Must combine.
    return self.combine_outputs(vals, to_spend, outputs)

  def combine_outputs(self, vals, to_spend, outputs):
    candidates = sorted(vals.items(), key=operator.itemgetter(1))
    candidates.reverse() # values in desc order

    total = 0
    ret = []
    find_last = False

    for i, v in enumerate(candidates):
      key = v[0]
      val = v[1]
      total+=val
      ret.append(outputs[key])
      last_iter = bool((len(candidates)-1) == i)

      if total >= to_spend: # find last output
        if last_iter:
          break
        else:
          find_last = True
          total-=val
          del ret[-1]
          prev_index = key
          prev_val = val
      elif find_last: # val too small. use previous
        del ret[-1]
        total-=val
        total+=prev_val
        ret.append(outputs[prev_index])
        break

    return ret

  def select_all_outs(self, addr, fee):
    outputs = self.get_unspent(addr)["unspent"]
    if not outputs:
      self.no_btc_error()
    tot = 0
    for o in outputs:
      val = o["value_int"]
      tot+=val
    if tot <= fee:
      self.insufficient_sats_error()
    return outputs

  def pushtx(self, tx):
    d = json.dumps({ "hex" : tx })
    r = requests.post(self.push_url, 
        headers=self.h, data=d)
    j = self.check_err(r)
    print "SUCCESS"

  def get_fee(self):
    r = requests.get(self.FEE_API, headers=self.h)
    if not self.is_json(r.text):
      scode = r.status_code
      self.JSON_error(scode)
    fee = r.json()["fastestFee"]
    return fee

  def get_balance(self, addr):
    url = self.BALANCE_API.format(addr)
    r = requests.get(url, headers=self.h)
    j = self.check_err(r)
    balance = j["wallet"]["total"]["balance"]
    return balance