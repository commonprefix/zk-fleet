from snark import SimpleSnark

ss = SimpleSnark("bord")

x = ss.create_proof([2])
assert ss.verify_proof(x)