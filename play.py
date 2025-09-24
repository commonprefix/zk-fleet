from web3 import Web3
import L1
import os
import sys
import time

from test import *

# use local anvil devnet
if int(os.getenv('PROD', '0')) > 0:
    L1.web3 = Web3(Web3.HTTPProvider("https://ethereum-sepolia-public.nodies.app"))
    L1.chain_id = 11155111
    CONTRACT_ADDRESS = "0x59134804d0Cf3ed908f0f2B6caA55E9D3d9Ac29c"
else:
    L1.web3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))
    L1.chain_id = 31337
    CONTRACT_ADDRESS = "0xDc64a140Aa3E981100a9becA4E685f962f0cF6C9"

private_key = os.getenv("PLAYER_KEY", "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80")

PLAYER = L1.OwnedL1Identity(private_key)
ABI_FILE = "game/out/Game.sol/Game.json"

ABI = L1.load_abi(ABI_FILE)

game = L1.Contract(CONTRACT_ADDRESS, ABI)

if sys.argv[1] == 'new':
    # if you are player one, you can select your opponent and the stake
    player2 = sys.argv[2]
    stake = int(sys.argv[3])

    board = Board.create_new()
    print(f"BACKUP YOUR BOARD: {board.export_board()}")
    board_proof_encoded = SimpleSnark.format_proof(board.proof)[0]

    # interact with the smart contract to create a new game
    tx_receipt, logs = game._interact(PLAYER, "newGame", [board.boardCommitment, board_proof_encoded, player2], stake)

    gameId = logs[0]['args']['gameId']
    print(f"CREATED GAME WITH ID {gameId} FOR PLAYER {player2} WITH STAKE {stake}")
elif sys.argv[1] == 'join':
    # if you are player two, you can specify the game you want to connect to
    gameId = int(sys.argv[2])

    res = game._call("games", [gameId])
    stake = res[13]

    board = Board.create_new()
    print(f"BACKUP YOUR BOARD: {board.export_board()}")
    board_proof_encoded = SimpleSnark.format_proof(board.proof)[0]

    # interact with the smart contract to join the game
    game._interact(PLAYER, "joinGame", [gameId, board.boardCommitment, board_proof_encoded], stake)
elif sys.argv[1] == 'rejoin':
    # if your script terminated, rejoin to a running game
    gameId = int(sys.argv[2])
    boardBackup = sys.argv[3]

    board = Board.import_board(boardBackup)
else:
    print(f"Unsupported option. Either use 'new', 'join' or 'rejoin'")
    sys.exit(-1)

class Game:
    backendContract: L1.Contract
    backendAttackProver: SimpleSnark

    def __init__(self, gameId: int, player: L1.OwnedL1Identity, board: Board):
        self.gameId = gameId
        self.player = player
        self._fetch()
        self.ourHitPositions = 0
        self.ourLastHitCounter = 0
        self.isPlayerOne = player.address == self.player1Address
        self.board = board
        if self.isPlayerOne:
            assert self.boardCommitment1 == board.boardCommitment
        else:
            assert self.boardCommitment2 == board.boardCommitment
        self._update()
        

    def move(self, target: int):
        self._update()
        if self.isOurAction() != (True, True):
            print(f"Not our move")
            return False
                
        __class__.backendContract._interact(self.player, 'makeMove', [self.gameId, target])
        self.ourLastTarget = target
        self._update()
        return True

    def _resolve(self):
        # check whether there is a hit or not at the specified position
        isHit = (self.board.board & (1 << self.target)) > 0
        # calculate the decomposition of the board now
        boardDecomposition = [(self.board.board >> i) & 1 == 1 for i in range(11 * 11)]

        # sanity checking
        boardCheck = 0
        for i in range(11 * 11):
            if boardDecomposition[i]:
                boardCheck += 1 << i
        assert boardCheck == self.board.board
        assert self.board.boardCommitment == poseidon([boardCheck, self.board.randomness])

        proof = __class__.backendAttackProver.create_proof([self.board.boardCommitment, self.target, isHit, boardDecomposition, self.board.randomness])
        encoded_proof, _ = __class__.backendAttackProver.format_proof(proof)
        print(f"This is a hit? {isHit}. Target is {self.target}")
        __class__.backendContract._interact(self.player, "resolveMove", [self.gameId, 1 if isHit else 0, encoded_proof])

    def attackedAlready(self, target):
        if self.isPlayerOne:
            toCheck = self.hitTargets1
        else:
            toCheck = self.hitTargets2
        return (toCheck & (1 << target)) > 0

    def isOurAction(self):
        if self.gameEnded:
            return False, None # already ended
        if self.boardCommitment2 == 0:
            return False, None # not yet started
        if (self.isPlayerOne == (self.turn % 2 == 0)) and (self.target == 255):
            # our turn, and we have to attack
            return True, True
        if (self.isPlayerOne != (self.turn % 2 == 0)) and (self.target != 255):
            # opponent turn, and we have to resolve
            return True, False
        return False, None

    def _fetch(self):
        state = __class__.backendContract._call("games", [self.gameId])
        [self.boardCommitment1, self.boardCommitment2, self.player1Address, self.player2Address, self.hitCounter1, self.hitCounter2, self.hitTargets1, self.hitTargets2, self.turn, self.lastMove, self.target, self.gameEnded, self.winner, self.stake, self.withdrawn] = state
        self.player1 = L1.L1Identity(self.player1Address)
        self.player2 = L1.L1Identity(self.player2Address)
    
    def _update(self):
        self._fetch()

        if self.isPlayerOne:
            self.ourCurHitCounter = self.hitCounter1
            self.ourAttacks = self.hitTargets1
        else:
            self.ourCurHitCounter = self.hitCounter2
            self.ourAttacks = self.hitTargets2
        
        if self.ourCurHitCounter == self.ourLastHitCounter:
            pass # nothing interesting
        elif self.ourCurHitCounter == self.ourLastHitCounter + 1:
            # the last hit was a success!
            self.ourHitPositions += (1 << self.ourLastTarget)
            self.ourLastHitCounter = self.ourCurHitCounter
        else:
            assert False, "We missed a turn??"

        if self.gameEnded:
            print(f"Game has ended! You won? {self.isPlayerOne == self.winner}")
            if not self.withdrawn and (self.isPlayerOne == self.winner):
                # withdraw now
                print(f"Attempt to withdraw now")
                __class__.backendContract._interact(self.player, 'withdraw', [self.gameId])
                print(f"Money withdrawn successfully")
                self._update()
        else:
            # check if we can timeout the game
            isOurAction, isAttackAction = self.isOurAction()
            if isOurAction:
                if isAttackAction:
                    print(f"Please attack now!")
                else:
                    self._resolve()
                    self._update()
            else:
                # check if we can timeout the game
                if __class__.backendContract._call('isGameTimeout', [self.gameId]):
                    __class__.backendContract._interact(self.player, 'timeoutGame', [self.gameId])
                    print(f"Timeout successful")
                    self._update()

    def print(self):
        # print stats about the game
        print(f"Game ended: {self.gameEnded}. Round: {self.turn}.\nPlayer 1: {self.player1Address} Hits: {self.hitCounter1}. \nPlayer 2: {self.player2Address} Hits: {self.hitCounter2}.")
        # draw the game board
        for y in range(11):
            for x in range(11):
                n = y * 11 + x
                if self.ourHitPositions & (1 << n) > 0:
                    print("X", end='')
                elif self.ourAttacks & (1 << n) > 0:
                    print("O", end='')
                else:
                    print('.', end='')
            print()


attackSnark = SimpleSnark('attack-reference')
Game.backendAttackProver = attackSnark
Game.backendContract = game

gameFramework = Game(gameId, PLAYER, board)

while not gameFramework.gameEnded:
    while not gameFramework.isOurAction()[0]:
        print(f"Waiting... Press enter to continue")
        input()
        gameFramework._update()

    # perform our move
    gameFramework.print()
    while True:
        try:
            target_str = input("Enter position that you want to hit> ")
            if target_str == 'q':
                sys.exit(-1)
            if ',' in target_str:
                target_x, target_y = target_str.split(',')
                target = int(target_y) * 11 + int(target_x)
            else:
                target = int(target_str)
            if target < 0 or target >= 11 * 11:
                print(f"Invalid target! Try again")
            if gameFramework.attackedAlready(target):
                print(f"You already attacked that position. Try again")
            else:
                break
        except Exception as e:
            print(str(e))
            pass
    gameFramework.move(target)