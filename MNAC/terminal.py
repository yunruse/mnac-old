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
NORMAL = colourify()


class AsciiMNAC(mnac.MNAC):
    def _grid(self, index, c=False):
        normal = NORMAL if c else ''
        noughts = NOUGHTS if c else ''
        crosses = CROSSES if c else ''
        taken = self.gridStatus[index]
        if taken == 1:
            return [noughts + '/-\\', '| |', '\\-/']
        elif taken == 2:
            return [crosses + '\\ /', ' x ', '/ \\']

        symbols = [
            {1: (noughts + 'x'), 2: (crosses + 'o')}.get(cell) or (normal + '.')
            for n, cell in enumerate(self.grids[index])]
        selector = (
            '   ' if self.noMiddleStart and self.state == 'begin' and index == 4 else
            normal + ('[{}]' if self.grid == index else ' {} ').format(mnac.numpad(index + 1)))
        return [''.join(symbols[0:3]), ''.join(symbols[3:6]), ''.join(symbols[6:9]), selector]

    def __repr__(self, showColors=False):
        rows = []
        for row in range(3):
            # transpose
            chars = zip(*(self._grid(row * 3 + col, showColors)
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

    def _loop(self, showColors=False):
        self._last_error = ''
        if os.name == 'nt':
            os.system('title Meta Noughts and Crosses')

        while True:
            os.system('cls' if os.name == 'nt' else 'clear')

            # printing with colour

            error = '{}[ {} ]{}'.format(
                ERROR, mnac.ERRORS[self._last_error], colourify()) if self._last_error else ''
            self._last_error = ''
            print('{}Meta Noughts and Crosses\n\n{}\n\n{}'.format(
                INFO, self.__repr__(showColors), error))

            if self.winner:
                print('GAME OVER! {}!'.format(
                    ['Noughts wins', 'Crosses wins', "It's a draw"][self.winner-1]))
                sys.exit(self.winner)

            prompt = ('{}{}{}: {}... > '.format(
                NOUGHTS + 'Noughts' if self.player == 1 else CROSSES + 'Crosses', NORMAL,
                ' in {} grid'.format(
                    mnac.DIRECTIONS[self.grid][1]) if self.grid is not None else '',
                self.action))

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
                self._last_error = e.args[0]
                continue
            error = ''

    def loop(self, showColors=False):
        try:
            self._loop(showColors=showColors)
        except KeyboardInterrupt:
            sys.exit(0)


parser = argparse.ArgumentParser(
    description='AsciiMNAC, a terminal-enabled Meta Noughts and Crosses.')

parser.add_argument('-m', '--middlestart', dest='middleStart', action='store_false',
                    help='Allow noughts to start in the middle. (Slightly less balanced.)')
parser.add_argument('-c', '--colors', dest='showColors', action='store_true',
                    help='Display UNIX terminal colors.')

if __name__ == '__main__':
    args = parser.parse_args()
    self = AsciiMNAC(noMiddleStart=args.middleStart)
    self.loop(showColors=args.showColors)
