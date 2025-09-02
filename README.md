# zk-fleet

1. Run `make` to compile and setup the circuit.
2. Create a witness using `zokrates compute-witness -a <args>`
3. Create a proof using `zokrates generate-proof -s gm17`
4. Verify the proof using `zokrates verify`
5. Profile the circuit using `zokrates profile`

# TODOs
- Complete bord SNARK (doShipsTouch)
- Write circuit for ship hit or miss (takes bord and private inputs, and checks whether the bit at this position is set or not)
- Optional: Optimize doShipsTouch to get rid of quadratic complexity