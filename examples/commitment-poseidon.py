import sys
import os

# add parent directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from poseidon import poseidon,fieldsize

# EXAMPLES:
# 42, 1993 -> 3218876152071309830764723554014386374707796851655023455045545023069410016615
# 578982 98824455 -> 12178043633749404611900228859774058380290927692596228417987860186582579586418
def commitUsingPoseidon(secret, randomness):
    return poseidon([secret, randomness])

if __name__ == "__main__":
    if len(sys.argv) == 3:
        secret = int(sys.argv[1])
        randomness = int(sys.argv[2])
        print(f"zokrates compute-witness -a {commitUsingPoseidon(secret, randomness)} {secret} {randomness}")
    else:
        print("Usage: python commitment.py <secret> <randomness>")