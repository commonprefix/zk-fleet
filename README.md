# ZoKrates tutorial
This repo contains two parts. First, some interesting examples that illustrate how ZoKrates works and some of its particularities. Second, an implementation of the battleships game, where ZoKrates is used to prove in zero knowledge the correctness of a board and the result of an attack.
The presentation `zk-fleet.pdf` will be used during the workshop.

## ZoKrates commands
1. Run `make` to compile and setup the circuit in a folder (run `make FILE=<filename>.zok` for `examples` folder). This command must be run from within the folder you want to compile.
2. Create a witness using `zokrates compute-witness -a <args>`
3. Create a proof using `zokrates generate-proof`
4. Verify the proof using `zokrates verify`
5. Profile the circuit using `zokrates profile`

## Examples
In [examples/](examples/) you can find the following ZoKrates code for the following tasks. Some examples are not complete, they are left as exercise and will be discussed during the workshop.
- Commitments: Prove knowledge of a secret value that commits to a publicly known commitment. Implemented using SHA and Poseidon. Compare the resulting number of constraints and the proof generation time! (You can use the provided Python scripts to generate the commitments given your secret.)
- Range proofs: Additionally prove that your secret is within a certain range. The examples compare different ways to perform the range check, including bit-decomposition and using the native implementation of ZoKrates.
- zerodiv.zok: This file does not contain a meaningful proof, but showcases how conditional statements work in a arithmetic circuits, and in ZoKrates specifically. Can you implement a function that returns the inverse of a field element, if that element is different from zero, or returns 0 otherwise?

To compile one of the examples, you can navigate to the [examples/](examples/) directory and use `make FILE=<filename>.zok`. For example, use `make FILE=commitment-sha.zok` to build `commitment-sha.zok`

## Zero-knowledge battleships
In `board\main.zok` and `attack\main.zok` you will find the ZoKrates code for generating and verifying proofs for a correct board setup and a valid attack result. These two files contain some TODOs, which are to be filled during the workshop.

Folders `attack-reference` and `board-reference` contain a reference solution that is deployed on `Ethereum Sepolia`.
The game contract can be found in `game/src/Game.sol` and is deployed at `0x59134804d0Cf3ed908f0f2B6caA55E9D3d9Ac29c`.
You can play the deployed version of the game:
- `python3 play.py new <player2 address> <stake in wei>`. Create a new game.
- `python3 play.py join <game id>`. Joins a game as player2.
- `python3 play.py rejoin <game id> <board backup>`. Rejoin a game using the board info that is generated when creating a new game or joining a game.