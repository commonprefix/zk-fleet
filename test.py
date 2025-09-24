from snark import SimpleSnark
import random # don't use that in production
from poseidon import poseidon, fieldsize
import json

class ShipPlacement:
    def __init__(self, startPointX, startPointY, directionSelector):
        self.startPointX = startPointX
        self.startPointY = startPointY
        self.directionSelector = directionSelector

    # to make it compatible with snark.py as_zokrates_input
    def as_zokrates_input(self):
        return [self.startPointX, self.startPointY, self.directionSelector]

    @staticmethod
    def from_zokrates_input(input):
        return __class__(*input)

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
    
    def export_board(self):
        return json.dumps({'ships': [ship.as_zokrates_input() for ship in self.ships], 'randomness': self.randomness}).encode().hex()

    @staticmethod
    def import_board(backupString: str):
        d = json.loads(bytes.fromhex(backupString).decode())
        ships = [ShipPlacement.from_zokrates_input(ship) for ship in d['ships']]
        return __class__(ships, d['randomness'])

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

board_snark = SimpleSnark("board-reference")
Board.BOARD_PROVER_BACKEND = board_snark

if __name__ == "__main__":

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

    # sanity check that board exporting works
    board = Board.create_new()
    exported = board.export_board()
    print(f"Exported: {exported}")
    imported = Board.import_board(exported)
    assert board.board == imported.board
    assert board.randomness == imported.randomness

    board = Board.create_new()
    print(board.print_board())