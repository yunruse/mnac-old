'''Meta Noughts and Crosses core game. Requires Python 3.'''

import random

# Helper functions

ERRORS = {
    1: "House rules: cannot start in middle",
    11: "That cell is already taken.",
    21: "Cannot send player to own grid.",
    22: "Cannot send player to taken grid."
}


class MoveError(Exception):
    __slots__ = ('code', )

    def __init__(self, code):
        self.code = code

    def __str__(self):
        return ERRORS.get(self.code, 'Unknown error')


def takenStatus(grid):
    for match in (
        (0, 1, 2), (3, 4, 5), (6, 7, 8),  # horizontal
        (0, 3, 6), (1, 4, 7), (2, 5, 8),  # vertical
        (0, 4, 8), (2, 4, 6)  # diagonal
    ):
        statuses = [grid[i] for i in match]
        s = statuses[0]
        if s and all(i == s for i in statuses):
            return s
    else:
        if all(grid):
            return 3
        return 0


numpad = [0, 7, 8, 9, 4, 5, 6, 1, 2, 3].index  # or __getindex__, I'm easy

DIRECTIONS = [
    ('nw', 'northwest',  'tl', 'topleft'),
    ('ne', 'northeast',  'tr', 'topright'),
    ('n',  'north',      't',  'top'),
    ('w',  'west',       'l',  'left'),
    ('c',  'centre',     'm',  'middle'),
    ('e',  'east',       'r',  'right'),
    ('sw', 'southwest',  'bl', 'bottomleft'),
    ('s',  'south',      'b',  'bottom'),
    ('se', 'southeast',  'br', 'bottomright')
]


def getIndex(text):
    text = text.strip().lower().replace('-', '').replace(' ', '')
    for index, aliases in enumerate(DIRECTIONS):
        if any(text == alias for alias in aliases):
            return index
    try:
        index = int(text)
    except ValueError:
        return None
    if 0 < index < 10:
        return numpad(index) - 1
    else:
        return None


class MNAC:
    '''Stateful game of Meta Noughts and Crosses.'''

    moves = 0

    # 'Taken status' is an integer as such:
    # 0 is not taken, 1 is noughts, 2 crosses, and 3
    # is used for draws.

    gridStatus = []  # 9 grid taken status
    grids = []  # 9 * [list of cell status]
    winner = 0  # taken status for whole game

    # State:
    #   'begin' : pre-game (player 1 chooses their board)
    #   'inner' : player is in grid, and will pick cell to take
    #   'outer' : player has taken teleporter, and picks grid to send to

    state = 'begin'
    player = None
    opponent = property(lambda s: 1 if s.player == 2 else 1)

    # Grid to play in.
    grid = None

    def __init__(self, startGrid=None, noMiddleStart=False):
        self.noMiddleStart = noMiddleStart

        self.lastPlacedGrid = None
        self.lastPlacedCell = None
        self.gridStatus = [0] * 9
        self.grids = [[0] * 9 for i in range(9)]
        self.player = 1
        self.moves = 0
        self.state = 'inner'

        if startGrid == 'random':
            # random, but not unfair advantage in centre
            self.grid = int(random.random() * 8)
            if self.grid > 3:
                self.grid += 1

        elif isinstance(startGrid, int):
            self.grid = startGrid
        else:
            self.grid = None
            self.state = 'begin'

    def check(self):
        self.gridStatus = [takenStatus(g) for g in self.grids]
        self.winner = takenStatus(self.gridStatus)

    def play(self, index):
        '''Play with index 1 through 9.'''
        try:
            self._play(index - 1)
            self.moves += 1
        except MoveError:
            raise

    def _swapPlayer(self):
        self.player = 2 if self.player == 1 else 1

    def onPlace(self, grid, cell):
        '''Overwritable, called when a cell is taken.'''
        pass

    def playableOptions(self):
        '''Returns list of 1-9 that are playable.'''
        if self.state == 'begin':
            possible = list(range(1, 10))
            if self.noMiddleStart:
                possible.remove(5)
            return possible
        else:
            scan = (self.grids[self.grid]
                    if self.state == 'inner' else self.gridStatus)
            return [i+1 for i in range(9) if scan[i] == 0]

    def _play(self, index):
        if self.state == 'begin':
            if self.noMiddleStart and index == 4:
                raise MoveError(1)  # House rules
            self.grid = index
            self.state = 'inner'

        elif self.state == 'inner':
            if self.grids[self.grid][index] != 0:
                raise MoveError(11)
            self.grids[self.grid][index] = self.player
            self.lastPlacedGrid = self.grid
            self.lastPlacedCell = index
            if callable(self.onPlace):
                self.onPlace(self.grid, index)
            self.check()
            if self.winner:
                return

            # if only one grid remains and the play in the last
            # grid remaining did not win, it is a draw
            takenCount = sum(bool(i) for i in self.gridStatus)
            if takenCount == 8:
                self.winner = 3

            isTeleporterCell = (index == self.grid
                                or self.gridStatus[index] != 0)
            if isTeleporterCell:
                # Todo: auto-send if only one other grid, or draw
                # if no other grids remain
                self.state = 'outer'
            else:
                self.grid = index
                self._swapPlayer()

        else:
            # Always gotta go to a different grid that isn't taken
            if index == self.grid:
                raise MoveError(21)
            elif self.gridStatus[index] != 0:
                raise MoveError(22)
            self.grid = index
            self._swapPlayer()
            self.state = 'inner'

    def stressTest(self, move_limit=None):
        moves = self.moves
        while self.moves - moves != move_limit and not self.winner:
            choices = list(range(9))
            random.shuffle(choices)
            for i in choices:
                try:
                    self.play(i)
                    break
                except MoveError:
                    continue
            else:
                return

    def __hash__(self):
        return hash((
            self.grid,
            self.lastPlacedGrid,
            self.lastPlacedCell,
            self.player,
            {'begin': 1, 'inner': 2, 'outer': 3}.get(self.state),
            tuple(tuple(grid) for grid in self.grids)
        ))


def _test(n=1000, **args):

    TAGS = {0: 'errors', 1: 'noughts', 2: 'crosses', 3: 'draws'}
    results = {i: [] for i in TAGS.values()}

    def loop():
        game = MNAC(**args)
        game.stressTest()
        result = TAGS.get(game.winner)
        results[result].append(game)

    import math
    import timeit

    time_taken = timeit.timeit(loop, number=n)

    fmt = ('{:<%s} ' % math.ceil(math.log10(n))).format

    print(
        fmt(n) + 'games in {:.1f}s ({:.4f}s per game)'.format(time_taken, time_taken / n))
    for i in TAGS.values():
        tag_n = len(results[i])
        proportion = 10 + math.ceil(10 * math.log10((tag_n or 1) / (n / 3)))
        print(fmt(tag_n) + '{:<7} {}'.format(i, '*' * proportion))

    return results


if __name__ == '__main__':
    results = _test(50000)
    results = _test(50000, noMiddleStart=True)
