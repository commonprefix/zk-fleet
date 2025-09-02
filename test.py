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
        ships = []
        for i in range(__class__.SHIP_COUNT):
            direction = random.randrange(0, 2) == 0
            posX, posY = [random.randrange(0,  __class__.BOARD_DIMENSION - (0 if (i == 1) == direction else __class__.SHIP_LENGTH)) for i in range(2)]
            # TODO: check that they don't touch other ships
            ships.append(ShipPlacement(posX, posY, direction))

        randomness = random.randrange(0, fieldsize)
        return __class__(ships, randomness)

board_snark = SimpleSnark("board")
Board.BOARD_PROVER_BACKEND = board_snark


board = Board.create_new()
print(board.print_board())