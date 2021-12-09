'''Ascii-enabled version of Meta Noughts and Crosses.

Some of the code here is re-used in bots.
'''
import argparse
import os
import re
import sys

import mnac

COLOURS = {
    # for more: man console_codes [under ECMA-48 Set Graphics Rendition]
    'normal': 0,
    'gray': 30,
    'red': 31,
    'green': 32,
    'yellow': 33,
    'blue': 34,
    'magenta': 35,
    'cyan': 36,
    'white': 37
}


def colourify(name='normal', bright=None):
    # if os.name == 'nt':
    #    return ''
    name = name.lower()
    if 'dark' in name:
        bright = 0
    elif bright is None:
        bright = 1
    return '\033[{};{}m'.format(COLOURS.get(name.replace(' ', '').replace('dark', ''), 0), bright)


NOUGHTS = colourify('cyan')
CROSSES = colourify('red')
INFO = colourify('green')
ERROR = colourify('red')
TAKEN = colourify('gray')
NORMAL = colourify()


class AsciiMNAC(mnac.MNAC):
    def __init__(self, args):
        self.args = args
        super().__init__(middleStart=args.middleStart)

    def _grid(self, grid, colors=True):
        normal = NORMAL
        tele = INFO
        noughts = NOUGHTS
        crosses = CROSSES

        taken = self.gridStatus[grid]
        if not colors:
            normal = noughts = crosses = tele = ''
        elif taken == 1:
            normal = noughts = crosses = tele = NOUGHTS
        elif taken == 2:
            normal = noughts = crosses = tele = CROSSES
        elif taken == 3:
            normal = noughts = crosses = tele = TAKEN

        symbols = [
            noughts + 'x' if cell == 1 else
            crosses + 'o' if cell == 2 else
            ' ' if taken in (1, 2) else
            tele + '.' if c == grid or self.gridStatus[c] != 0 else
            normal + '.'
            for c, cell in enumerate(self.grids[grid])]
        selector = (
            '   ' if self.state == 'begin' and grid == 4 and not self.middleStart else
            normal + ('[{}]' if self.grid == grid else ' {} ').format(mnac.numpad(grid + 1)))
        return [''.join(symbols[0:3]), ''.join(symbols[3:6]), ''.join(symbols[6:9]), selector]

    def __repr__(self):
        rows = []
        for row in range(3):
            # transpose
            chars = zip(*(self._grid(row * 3 + col)
                        for col in range(3)))
            rows.append('\n'.join(map(' '.join, chars)))

        return '\n\n'.join(rows)

    def onPlace(self, _, index):
        pass

    @property
    def action(self):
        if self.state == 'begin':
            return 'Start in grid'
        elif self.state == 'inner':
            return 'Take a cell'
        else:
            return 'Send your opponent to'

    def _loop(self):
        self._last_error = ''
        if os.name == 'nt':
            os.system('title Meta Noughts and Crosses')

        while True:
            os.system('cls' if os.name == 'nt' else 'clear')

            print('{}Meta Noughts and Crosses\n\n{}\n'.format(
                INFO, repr(self)))
            if self._last_error:
                print('{}[ {} ]{}'.format(
                    ERROR, self._last_error, NORMAL))
            else:
                print()

            self._last_error = ''

            if self.winner:
                print('GAME OVER! {}!'.format(
                    ['Noughts wins', 'Crosses wins', "It's a draw"][self.winner-1]))
                sys.exit(self.winner)

            prompt = ('{}{}{}: {}... > '.format(
                NOUGHTS + 'Noughts' if self.player == 1 else CROSSES + 'Crosses', NORMAL,
                ' in {} grid'.format(
                    mnac.DIRECTIONS[self.grid][1]) if self.grid is not None else '',
                self.action))

            # TODO: handle eg '12' if and only if a teleporter move can be played?

            inp = input(prompt).lower().strip().replace(
                ' ', '').replace('-', '')
            if 'exit' in inp or inp == 'q':
                sys.exit(0)
            elif not inp:
                continue

            index = mnac.getIndex(inp)
            if index is None:
                self._last_error = 'Invalid argument {!r}'.format(inp)
                continue
            try:
                self.play(index + 1)
            except mnac.MoveError as e:
                self._last_error = str(e)
                continue
            error = ''

    def loop(self):
        try:
            self._loop()
        except KeyboardInterrupt:
            sys.exit(0)


parser = argparse.ArgumentParser(
    description='AsciiMNAC, a terminal-enabled Meta Noughts and Crosses.')

parser.add_argument('-m', '--middleStart', dest='middleStart', action='store_true',
                    help='Allow noughts to start in the middle. (Slightly less balanced.)')

if __name__ == '__main__':
    args = parser.parse_args()
    self = AsciiMNAC(args)
    self.loop()
