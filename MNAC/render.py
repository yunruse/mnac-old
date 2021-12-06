from ast import literal_eval
import os
import re

from PIL import Image, ImageDraw, ImageFont
import numpy as np

import mnac

FONT = 'arial.ttf'

is_dark = True

with open('theme.less') as f:
    file = f.read(-1)
    for a, b in (
        (r'/\*.+?\*/', ''),
        (r'\s+', ''),
        (r'\}', '},'),
        ('\.([a-z]+)\{', r'"\1":{'),
        ('\{color:(#[a-zA-Z0-9]+)\}', r'"\1"')
    ):
        file = re.sub(a, b, file)

    THEMES = literal_eval('{' + file + '}')

CORNER = np.array([
    (0, 0), (0, 50), (1, 41), (3, 32), (21, 9),
    (15, 15), (9, 21), (32, 3), (41, 1), (50, 0), (0, 0)]) / 50

CROSS = np.array([
    (0, 0), (1, 0), (4.5, 3.5), (8, 0), (9, 0),
    (9, 1), (5.5, 4.5), (9, 8), (9, 9),
    (8, 9), (4.5, 5.5), (1, 9), (0, 9),
    (0, 8), (3.5, 4.5), (0, 1), (0, 0)]) / 9


class Render:
    def __init__(self, game, size=450, theme='dark'):
        if not isinstance(game, mnac.MNAC):
            raise TypeError('Game must be MNAC or subclass')
        self.game = game
        self.size = size
        self.theme = THEMES[theme]
        self.error = False

    # Relative to width of one cell, size of grid gaps
    SEPARATION = 1/4
    # Grid rounding, relative to cell width
    ROUNDING = 1/10

    def background(self):
        players = ['', 'nought', 'cross', 'gray']
        if self.game.winner:
            return self.theme[players[self.game.winner]]['main']
        else:
            return self.theme[players[self.game.player]]['dark' if self.error else 'main']

    def draw(self):
        skipDraw = self.onStart()
        if skipDraw:
            return self.drawn()

        theme = self.theme
        game = self.game
        cell = self.size / (9 + 2 * self.SEPARATION)

        for g in range(9):
            gxy = np.array((g % 3, g // 3))
            gridtl = gxy * cell * (3 + self.SEPARATION)
            gridStatus = game.gridStatus[g]
            gridTaken = (gridStatus in (1, 2))

            if not gridTaken:
                for c in range(9):
                    gridcol = ['light', 'main', 'dark'][(g % 2) + (c % 2)]
                    color = theme['grid'][gridcol]
                    xy = np.array((c % 3, c // 3))
                    celltl = gridtl + (xy * cell)
                    self.cell(g, c, celltl, cell, fill=color)

                # %% cell markers
                    cellStatus = game.grids[g][c]
                    xy = np.array((c % 3, c // 3))
                    celltl = gridtl + xy * cell
                    wasLast = (game.lastPlacedGrid,
                               game.lastPlacedCell) == (g, c)
                    if cellStatus == 1:
                        color = theme['cross']['light' if wasLast else 'main']
                        top_left = celltl + cell / 18
                        bottom_right = celltl + cell - cell / 18
                        coords = np.array((*top_left, *bottom_right))
                        self.ellipse(coords, outline=color, width=cell/9)

                    elif cellStatus == 2:
                        coords = celltl + CROSS * cell
                        color = theme['nought']['light' if wasLast else 'main']
                        self.polygon(coords, fill=color)

                    elif game.grid == g and game.state == 'inner':
                        # keyboard selector for cell
                        canTeleport = (c == g or game.gridStatus[g] != 0)
                        textcol = theme['tele']['main'] if canTeleport else theme['gray']['dark']
                        self.text(
                            celltl + cell/2, isLarge=False, fill=textcol,
                            size=int(cell * 2/3), text=str(mnac.numpad(c + 1))
                        )

            # %% grid markers - nought, cross

            if gridStatus == 1:
                top_left = gridtl + cell / 6
                bottom_right = gridtl + cell * (3 - 1/6)
                coords = np.array((*top_left, *bottom_right))
                self.ellipse(
                    coords, outline=theme['cross']['light'], width=cell/3)

            elif gridStatus == 2:
                coords = gridtl + (CROSS * cell * 3)
                self.polygon(coords, fill=theme['nought']['light'])

            elif game.grid == g or gridStatus == 3:
                pass

            else:
                color = None
                if game.state == 'inner':
                    # keyboard selector to show where placing a cell would send one.
                    # cannot be self, or a taken grid
                    if not (game.grid == g or game.grids[game.grid][g]):
                        color = theme['gray']['light']

                # keyboard selector for what grid to send / be in
                elif not (not game.middleStart and game.state == 'begin' and g == 4):
                    color = theme['tele']['main']

                if color:
                    self.text(
                        gridtl + cell * 6/9, isLarge=True,
                        text=str(mnac.numpad(g+1)), size=int(cell * 2),
                        fill=color)

        # corners, with x, y and reversing of corner coords
        for x, y, xr, yr in (
            (0, 0, 1,  1), (1, 0, -1,  1),
                (0, 1, 1, -1), (1, 1, -1, -1)):
            rel = cell * 3 * np.array((x, y))
            size = cell * self.ROUNDING * np.array((xr, yr))
            for i in range(9):
                gxy = np.array((i % 3, i // 3))
                coord = gxy * cell * (3 + self.SEPARATION) + rel
                shape = coord + CORNER * size
                self.polygon(shape, fill=self.background())

        return self.drawn()

    def onStart(self):
        '''Callback before rendering starts.'''

    def cell(self, grid, cell, tl, size, fill):
        '''Draw a cell backing.'''

    def ellipse(self, coords, outline, width):
        '''Draw an ellipse (typically noughts).'''

    def polygon(self, coords, fill):
        '''Draw a polygon (typically crosses).'''

    def text(self, coords, isLarge, text, size, fill):
        '''Draw a numerical indicator.'''

    def drawn(self):
        '''Finalise and return complete render.'''


class ImageRender(Render):
    '''Python Imaging Library-based image renderer.'''

    font = 'arial.ttf'

    def onStart(self):
        self.image = Image.new(
            'RGB', (self.size, self.size), color=self.background())
        self.imdraw = ImageDraw.Draw(self.image)

    def cell(self, i, j, cell, size, fill):
        self.imdraw.rectangle((*cell, *(cell + size)), fill=fill)

    def ellipse(self, bounds, outline, width):
        # Totally stolen from Håken Lid! stackoverflow.com/a/34926008

        # Single channel mask to apply colour with, initially black (transparent)
        mask = Image.new(size=self.image.size, mode='L', color='black')
        draw = ImageDraw.Draw(mask)

        # draw outer shape in white (color) and inner shape in black (transparent)
        for offset, fill in (width/-2.0, 'white'), (width/2.0, 'black'):
            left, top = [(value + offset) for value in bounds[:2]]
            right, bottom = [(value - offset-1) for value in bounds[2:]]
            draw.ellipse([left, top, right, bottom], fill=fill)

        self.image.paste(outline, mask=mask)

    def polygon(self, coords, fill):
        self.imdraw.polygon(tuple(coords.flatten()), fill=fill)

    def text(self, coords, isLarge, text, size, fill):
        # fiddle factors for text coords
        fiddle = (1/3, -1/6) if isLarge else (-1/6, -1/3)
        coords += np.array(fiddle) * self.size / (9 + 2 * self.SEPARATION)

        font = ImageFont.truetype(self.font, size)
        self.imdraw.text(coords, text=text, font=font, fill=fill)

    def drawn(self):
        return self.image


if __name__ == '__main__':
    import random
    import timeit
    game = mnac.MNAC()
    plays = random.randrange(3, 40)
    plays = 50
    game.stressTest(plays)
    r = ImageRender(game, size=450)
    r.draw().save('test_image.png')
    #draw_game(game, size=1024).save('test_image.png')
