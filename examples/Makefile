FILE ?= main.zok

setup: out.r1cs
	zokrates setup -s gm17
	zokrates export-verifier

out.r1cs: $(FILE)
	zokrates compile -i $(FILE)

clean:
	rm -f abi.json out out.r1cs out.wtns proof.json proving.key verification.key verifier.sol witness verifier.sol