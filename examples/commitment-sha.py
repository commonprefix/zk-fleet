import hashlib
import sys

def commitUsingSHA(value: bytes) -> bytes:
    return hashlib.sha256(value).digest()

def hash_to_u32(val: bytes) -> str:
    M0 = val.hex()
    b0 = [str(int(M0[i:i+8], 16)) for i in range(0,len(M0), 8)]
    assert len(b0) == 8
    s = ' '.join(b0)
    return s

if __name__ == "__main__":
    if len(sys.argv) == 3:
        secret = int.to_bytes(int(sys.argv[1]), 32, "big")
        randomness = int.to_bytes(int(sys.argv[2]), 32, "big")
        commitment = commitUsingSHA(secret + randomness)
        print(f"zokrates compute-witness -a {hash_to_u32(commitment)} {hash_to_u32(secret)} {hash_to_u32(randomness)}")
    else:
        print("Usage: python commitment.py <secret> <randomness>")