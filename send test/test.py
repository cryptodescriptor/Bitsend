import sys
sys.path.append("..")

import keys, web
from txn import tx

my_addr = "2NFfq2QzgbEtRSAHbMNzTQ68YsLD3BNF8ve"
my_pk = "7db3bdfa33737423207c549c279dd8a25e37221c2d109b4c1b1525940ac3f4cb"

cfg = [
  [my_addr, my_pk],
  { 
  "2NFfq2QzgbEtRSAHbMNzTQ68YsLD3BNF8ve": 0.00001,
  "mjpqMuKZA9gYnxXFNdkGLQEMKxokhESvMG":0.00001,
  "2NBMEXfLZ6Mar5vy3EidQrTr7ARWxKUghFh":0.00001,
  "2MwVBqTsiQGFNCy4FRcKYB2quXUFz9Cut3H":0.00001,
  "msgnVPocDRqKo1fu7PzTw46N6AtcBAbcDK":0.00001,
  "mwMo8HyKXhNQfvRcxRzdVWsuS6Efzyq3Hq":0.00021,
  "mtproXYu8GK2AvrRqnsEdfw2R14T99Rwkn":0.00001,
  "mtbLoq1aCQ8VceaWKCmQsjwrEQkN4m8hbF":0.00001,
  "msawhdQkcPF2MLK6bxnwpoQRQP5bi7HgxH":0.00001,
  "2N5dZbDQX8SXRtUh9XvKyfCDRAoQFzQpCvs":0.00001,
  "tb1q4tqgnuwphrgt6yqn5zh5n6zz82f0elzgmtk0jj":0.00001
  }
]

"""
SWEEP ALL

cfg = [
  [my_addr, my_pk],
  "2NFfq2QzgbEtRSAHbMNzTQ68YsLD3BNF8ve"
]
"""

w = web.web_api(testnet=True)

print "Balance: " + str(w.get_balance(my_addr))

# fee is always in satoshis
t = tx(cfg=cfg, fee=19600, testnet=True)

print "\n" + t.return_raw(spaces=True) + "\n"

signed = t.signtx()

print signed + "\n"

t.pushtx(signed)