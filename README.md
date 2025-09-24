# zk-fleet

1. Run `make` to compile and setup the circuit in a folder. In the `examples` folder, use `make FILE=commitment-sha.zok` to build `commitment-sha.zok`. 
2. Create a witness using `zokrates compute-witness -a <args>`
3. Create a proof using `zokrates generate-proof`
4. Verify the proof using `zokrates verify`
5. Profile the circuit using `zokrates profile`

`attack-reference` and `board-reference` contain a reference solution that is deployed on `Ethereum Sepolia`.
The game contract can be found in `game/src/Game.sol` and is deployed at `0x59134804d0Cf3ed908f0f2B6caA55E9D3d9Ac29c`.
You can play the deployed version of the game:
- `python3 play.py new <player2 address> <stake in wei>`. Create a new game. 
- `python3 play.py join <game id>`. Joins a game as player2.
- `python3 play.py rejoin <game id> <board backup>`. Rejoin a game using the board info that is generated when creating a new game or joining a game.