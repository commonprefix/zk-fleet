# This is a simple Zokrates interface
from subprocess import Popen, PIPE
import json
from time import perf_counter
import math

def as_zokrates_input(data):
    s = []
    for o in data:
        if isinstance(o, list):
            s.append(as_zokrates_input(o))
        elif isinstance(o, bool):
            s.append('1' if o else '0')
        else:
            s.append(str(o))
    return ' '.join(s)

def round_sig(x, sig=3):
    if x == 0:
        return 0
    return round(x, sig - int(math.floor(math.log10(abs(x)))) - 1)

class SimpleSnark():
    def __init__(self, dir: str):
        self.dir = dir # this is where the SNARK is hiding 

    def create_proof(self, data: list):
        startTime = perf_counter()
        parsed = as_zokrates_input(data).split(' ')
        p = Popen(["zokrates", "compute-witness", "-a", *parsed], cwd=self.dir, stdout=PIPE, stdin=PIPE, stderr=PIPE)
        p.wait()
        stdout, stderr = p.communicate()
        if len(stderr) > 0:
            raise Exception(f"zokrates returned: {stderr.decode()}")
        if p.returncode != 0 or stdout != b"Computing witness...\nWitness file written to 'witness'\n":
            print(stdout)
            return None 
        # witness okay

        # generate proof now
        p = Popen(["zokrates", "generate-proof", "-s", "gm17"], cwd=self.dir, stdout=PIPE, stdin=PIPE, stderr=PIPE)
        p.wait()
        stdout, stderr = p.communicate()
        if len(stderr) > 0:
            raise Exception(f"zokrates returned: {stderr.decode()}")
        if p.returncode != 0 or stdout != b"Generating proof...\nProof written to 'proof.json'\n":
            print(stdout)
            return None
        stopTime = perf_counter()
            
        # read proof.json now
        with open(self.dir + '/proof.json', 'r') as f:
            s = f.read()
            obj = json.loads(s)
            assert obj['scheme'] == 'gm17'
            assert obj['curve'] == 'bn128'

            # read and parse the 8 values 
            proof = obj['proof']
            p = b''
            for l1 in [proof['a'], proof['b'][0], proof['b'][1], proof['c']]:
                for point in l1:
                    p += (int(point, 16)).to_bytes(32)

            i = b''
            for data in obj['inputs']:
                # assert: all inputs are field elements or at most uint256
                i += (int(data, 16)).to_bytes(32)

        # the first 256 bytes are proof bytes, the rest is input data
        print(f"Creating this proof of length {len(p) + len(i)} took {round_sig(stopTime - startTime)} seconds")

        return p + i
    
    @staticmethod
    def _bytes_to_hex(o: bytes):
        return '0x' + hex(int.from_bytes(o))[2:].zfill(64)
    
    # format a given serialized proof into the input format for the EVM verifier contract
    @staticmethod 
    def format_proof(proof):
        p = proof[0:256]
        i = proof[256:]

        proofs = [int.from_bytes(p[x:x+32]) for x in range(0, len(p), 32)]
        inputs = [int.from_bytes(i[x:x+32]) for x in range(0, len(i), 32)]

        proof_encoded = ((proofs[0], proofs[1]), ([proofs[2], proofs[3]], [proofs[4], proofs[5]]), (proofs[6], proofs[7]))
        return proof_encoded, inputs
    
    def verify_proof(self, proof: bytes):
        p = proof[0:256]
        i = proof[256:]

        proofs = [SimpleSnark._bytes_to_hex(p[x:x+32]) for x in range(0, len(p), 32)]
        inputs = [SimpleSnark._bytes_to_hex(i[x:x+32]) for x in range(0, len(i), 32)]

        obj = {
            'scheme': 'gm17',
            'curve': 'bn128',
            'proof': {
                'a': [proofs[0], proofs[1]],
                'b': [
                    [proofs[2], proofs[3]],
                    [proofs[4], proofs[5]]
                ],
                'c': [proofs[6], proofs[7]]
            },
            'inputs': inputs,
        }

        with open(self.dir + '/proof.json', 'w') as f:
            # rebuild the structure of the proof.json file 
            s = json.dumps(obj)
            f.write(s)
        
        # verify it
        startTime = perf_counter()
        p = Popen(["zokrates", "verify"], cwd=self.dir, stdout=PIPE, stdin=PIPE, stderr=PIPE)
        p.wait()
        stdout, stderr = p.communicate()
        if len(stderr) > 0:
            raise Exception(f"zokrates returned: {stderr.decode()}")
        stopTime = perf_counter()
        print(f"Verifying this proof of length {len(proof)} required {round_sig(stopTime - startTime)} seconds")
        if p.returncode != 0 or stdout != b'Performing verification...\nPASSED\n':
            return False
        else:
            return True