import sys
import os
from hashlib import sha256

# add parent directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from poseidon import poseidon,fieldsize

# EXAMPLES:
# 42, 1993 -> 3218876152071309830764723554014386374707796851655023455045545023069410016615
# 578982 98824455 -> 12178043633749404611900228859774058380290927692596228417987860186582579586418
def commitUsingPoseidon(secret, randomness):
    return poseidon([secret, randomness])

# EXAMPLES:
# 42, 1993 -> 4675308175894675802311962350188857100635762200306294593565387230215527950975
# 578982 98824455 -> 12150873530504354285925557637324242815614046105770230200364652111593576011861
def commitUsingSha(secret, randomness):
    s_bytes = secret.to_bytes(32, "big")
    r_bytes = randomness.to_bytes(32, "big")

    # compute SHA-256 hash of concatenated bytes
    digest = sha256(s_bytes + r_bytes).digest()
    return digest
    # TODO: format this in a way we can parse

if __name__ == "__main__":
    if len(sys.argv) == 3:
        secret = int(sys.argv[1])
        randomness = int(sys.argv[2])
        print(commitUsingPoseidon(secret, randomness))
    else:
        print("Usage: python commitment.py <secret> <randomness>")