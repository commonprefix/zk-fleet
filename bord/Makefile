setup: out.r1cs
	zokrates setup
	zokrates export-verifier

out.r1cs: *.zok
	zokrates compile -i *.zok

clean:
	rm -f abi.json out out.r1cs out.wtns proof.json proving.key verification.key verifier.sol witness verifier.sol