import sys
sys.path.append("..")

from parse import txn

# CONFIG 
stop = 10

def header(string):
  post =  "\n" + "-"*60
  pre =  post + "\n"
  print pre + string + post

def counter(i):
  print "\n(" + str(i+1) + ")"

def line(pre=""):
  print pre + "-"*20

f = open("tx.txt", "r")
tx_data = f.read()
f.close()

tx = txn(tx_data=tx_data)
tx.parse()

print "\nSegwit: " + str(tx.segwit)
print "txn version: " + str(tx.version)
print "Flag: " + tx.flag

# inputs
header("Inputs: " + str(tx.input_count))

for i in range(tx.input_count):
  if i == stop:
    break
  counter(i)
  print "Previous txn hash: " + str(tx.inputs["hash"][i])
  print "Index: " + str(tx.inputs["index"][i])
  print "sigScript: " + tx.inputs["sigScript"][i]
  print "Sequence: " + tx.inputs["sequence"][i]

# outputs
header("Outputs: " + str(tx.output_count))

for i in range(tx.output_count):
  if i == stop:
    break
  counter(i)
  print "Value (satoshis): " + str(tx.outputs["value"][i])
  print "pubKeyScript: " + tx.outputs["pubKeyScript"][i]

line(pre="\n")

# segwit
if tx.segwit and tx.witness_count != 0:
  print "\nWitness Count: " + str(tx.witness_count)
  for i in range(tx.witness_count):
    if i == stop:
      break
    counter(i)
    print "Witness: " + tx.witness["witness"][i]
  line()
  
print "\nLocktime: " + str(tx.locktime)