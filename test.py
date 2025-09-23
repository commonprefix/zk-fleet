from snark import SimpleSnark
import random # don't use that in production
from poseidon import poseidon, fieldsize

class ShipPlacement:
    def __init__(self, startPointX, startPointY, directionSelector):
        self.startPointX = startPointX
        self.startPointY = startPointY
        self.directionSelector = directionSelector

    # to make it compatible with snark.py as_zokrates_input
    def as_zokrates_input(self):
        return [self.startPointX, self.startPointY, self.directionSelector]

class Board():
    SHIP_COUNT: int = 3
    SHIP_LENGTH: int = 3
    BOARD_DIMENSION: int = 11
    BOARD_PROVER_BACKEND: SimpleSnark = None

    def __init__(self, ships: list[ShipPlacement], randomness: int):
        self.ships = ships
        self.randomness = randomness

        self.board = self.place_ships(ships)
        self.boardCommitment = poseidon([self.board, randomness])

        # create a proof now
        self.proof = __class__.BOARD_PROVER_BACKEND.create_proof([self.boardCommitment, *self.ships, self.randomness])
        assert self.proof is not None, f"Generating the proof failed"

    def print_board(self):
        s = []
        for y in range(__class__.BOARD_DIMENSION):
            for x in range(__class__.BOARD_DIMENSION):
                if self.board & (1 << (y * __class__.BOARD_DIMENSION + x)) > 0:
                    s.append('X')
                else:
                    s.append('.')
            s.append('\n')
        return ''.join(s)

    def place_ships(self, shipPlacements: list[ShipPlacement]) -> int:
        return sum([self.place_ship(s) for s in shipPlacements])

    def place_ship(self, shipPlacement: ShipPlacement) -> int:
        # Compute end coordinates based on direction
        if shipPlacement.directionSelector:  # horizontal
            endPointX = shipPlacement.startPointX + __class__.SHIP_LENGTH
            endPointY = shipPlacement.startPointY
        else:  # vertical
            endPointX = shipPlacement.startPointX
            endPointY = shipPlacement.startPointY + __class__.SHIP_LENGTH

        # Assert that ship is within the board
        assert 0 <= shipPlacement.startPointX < __class__.BOARD_DIMENSION
        assert 0 <= endPointX < __class__.BOARD_DIMENSION
        assert 0 <= shipPlacement.startPointY < __class__.BOARD_DIMENSION
        assert 0 <= endPointY < __class__.BOARD_DIMENSION

        # Encode ship position as a bitmask
        partialBoard = 0
        currentPos = shipPlacement.startPointX + shipPlacement.startPointY * __class__.BOARD_DIMENSION

        for _ in range(__class__.SHIP_LENGTH):
            partialBoard += pow(2, currentPos)

            if shipPlacement.directionSelector:
                # move in x direction
                currentPos += 1
            else:
                # move in y direction
                currentPos += __class__.BOARD_DIMENSION

        return partialBoard


    @staticmethod
    def create_new():
        while True:
            try:
                ships = []
                for i in range(__class__.SHIP_COUNT):
                    direction = random.randrange(0, 2) == 0
                    posX, posY = [random.randrange(0,  __class__.BOARD_DIMENSION - (0 if (i == 1) == direction else __class__.SHIP_LENGTH)) for i in range(2)]
                    # TODO: check that they don't touch other ships
                    ships.append(ShipPlacement(posX, posY, direction))

                randomness = random.randrange(0, fieldsize)
                ret = __class__(ships, randomness)
                break
            except AssertionError:
                pass
        return ret


def create_board(ship1, ship2, ship3, randomness):
    return Board([ShipPlacement(*ship1), ShipPlacement(*ship2), ShipPlacement(*ship3)], randomness)

def test_boards():
    # should pass
    create_board((1,1,1), (3,3,1), (5,5,1), 4533)
    create_board((2,2,1), (3,6,1), (7,7,0), 4533)
    create_board((2,2,1), (7,5,1), (7,7,0), 4533)

    # should fail
    tests_should_raise([
        lambda: create_board((1,1,1), (1,1,1), (5,5,1), 4533),
        lambda: create_board((1,1,1), (5,5,1), (5,5,1), 4533),
        lambda: create_board((1,1,1), (2,2,1), (5,5,1), 4533),
        lambda: create_board((1,1,1), (4,4,1), (5,5,1), 4533),
        lambda: create_board((1,1,0), (1,1,0), (5,5,0), 4533),
        lambda: create_board((1,1,0), (5,5,0), (5,5,0), 4533),
        lambda: create_board((1,1,0), (2,2,0), (5,5,0), 4533),
        lambda: create_board((1,1,0), (4,4,0), (5,5,0), 4533),
        # ship1 and ship2 intersect
        lambda: create_board((1,1,1), (0,0,0), (5,5,1), 4533),
        lambda: create_board((1,1,1), (1,0,0), (5,5,1), 4533),
        lambda: create_board((1,1,1), (2,0,0), (5,5,1), 4533),
        # ship2 and ship 3 touch or intersect
        lambda: create_board((2,2,1), (4,6,1), (7,7,0), 4533),
        lambda: create_board((2,2,1), (5,6,1), (7,7,0), 4533),
        lambda: create_board((2,2,1), (6,6,1), (7,7,0), 4533),
        lambda: create_board((2,2,1), (7,6,1), (7,7,0), 4533),
        lambda: create_board((2,2,1), (8,6,1), (7,7,0), 4533),
        lambda: create_board((2,2,1), (6,7,1), (7,7,0), 4533),
        lambda: create_board((2,2,1), (7,7,1), (7,7,0), 4533),
        lambda: create_board((2,2,1), (8,7,1), (7,7,0), 4533),
        lambda: create_board((2,2,1), (6,8,1), (7,7,0), 4533),
        lambda: create_board((2,2,1), (7,8,1), (7,7,0), 4533),
        lambda: create_board((2,2,1), (8,8,1), (7,7,0), 4533),
        lambda: create_board((2,2,1), (6,9,1), (7,7,0), 4533),
        lambda: create_board((2,2,1), (7,9,1), (7,7,0), 4533),
        lambda: create_board((2,2,1), (8,9,1), (7,7,0), 4533),
        lambda: create_board((2,2,1), (6,10,1), (7,7,0), 4533),
        lambda: create_board((2,2,1), (7,10,1), (7,7,0), 4533),
        lambda: create_board((2,2,1), (8,10,1), (7,7,0), 4533),
    ])


def tests_should_raise(funcs):
    for i, func in enumerate(funcs):
        try:
            func()
        except AssertionError as e:
            print(f"Board #{i} raised an error.")
            pass  # Expected AssertionError was raised
        else:
            raise AssertionError("AssertionError was not raised (e.g. 'Generating the proof failed')")


board_snark = SimpleSnark("board")
Board.BOARD_PROVER_BACKEND = board_snark

board = Board.create_new()
print(board.print_board())

from web3 import Web3
import L1
import os
import sys

# use local anvil devnet
L1.web3 = Web3(Web3.HTTPProvider("HTTP://127.0.0.1:8545"))
chain_id = 31337

# Address and private key
private_key = os.getenv("PRIVATE_KEY", "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80")
PLAYER1 = L1.OwnedL1Identity(private_key)

PLAYER2 = L1.OwnedL1Identity("0x59c6995e998f97a5a0044966f0945389dc9e86dae88c7a8412f4603b6b78690d")

CONTRACT_ADDRESS = "0x725314746e727f586E9FCA65AeD5dBe45aA71B99"

ABI_FILE = "game/out/Game.sol/Game.json"

ABI = L1.load_abi(ABI_FILE)

STAKE = 500_000_000_000_000_000

game = L1.Contract(CONTRACT_ADDRESS, ABI)

board1 = Board.create_new()
board1_proof_encoded = SimpleSnark.format_proof(board1.proof)[0]

tx_receipt, logs = game._interact(PLAYER1, "newGame", [board1.boardCommitment, board1_proof_encoded, PLAYER2.address], STAKE)

print(logs)

GAME_ID = logs[0]['args']['gameId']
print(f"Playing game {GAME_ID}")

board2 = Board.create_new()
board2_proof_encoded = SimpleSnark.format_proof(board2.proof)[0]

game._interact(PLAYER2, "joinGame", [GAME_ID, board2.boardCommitment, board2_proof_encoded], STAKE)

res = game._call("games", [GAME_ID])

print(res)

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



    
attackSnark = SimpleSnark('attack')
Game.backendAttackProver = attackSnark
Game.backendContract = game

gameFramework = Game(GAME_ID, PLAYER1, board1)
opponentGameFramework = Game(GAME_ID, PLAYER2, board2)

player2target = 0
while not gameFramework.gameEnded:
    # perform move of player 1
    gameFramework.print()
    while True:
        try:
            print("Enemy ships are at:")
            print(opponentGameFramework.board.print_board())
            target_str = input("Enter position that you want to hit> ")
            if target_str == 'q':
                sys.exit(-1)
            if ',' in target_str:
                target_x, target_y = target_str.split(',')
                target = int(target_y) * 11 + int(target_x)
            else:
                target = int(target_str)
            if gameFramework.attackedAlready(target):
                print(f"You already attacked that position. Try again")
            else:
                break
        except Exception as e:
            print(str(e))
            pass
    gameFramework.move(target)

    opponentGameFramework._update() # resolves player1's attack
    opponentGameFramework.move(player2target)
    player2target += 1

    gameFramework._update() # resolves player2's attack
