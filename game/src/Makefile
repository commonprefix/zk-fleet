force_rebuild: ../../board/verifier.sol ../../attack/verifier.sol
	cp ../../board/verifier.sol BoardVerifier.sol
	cp ../../attack/verifier.sol AttackVerifier.sol
	sed -i 's/assembly/assembly ("memory-safe")/g' BoardVerifier.sol
	sed -i 's/assembly/assembly ("memory-safe")/g' AttackVerifier.sol
	# actually this might not be true memory safe - bump the free memory pointer after using result := mload(freemem)  with  mstore(0x40, add(freemem, 0xC0))

	# also backup the attack and board folders -> these will be used by the actual game application
	rm -rf ../../board-reference
	rm -rf ../../attack-reference
	cp -r ../../board ../../board-reference
	cp -r ../../attack ../../attack-reference
	rm ../../board-reference/main.zok
	rm ../../attack-reference/main.zok
	
