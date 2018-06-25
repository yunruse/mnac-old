import os
from PIL import Image, ImageDraw, ImageFont
import numpy as np

from mnac import MNAC, numpad

FONT = 'arial.ttf'

BACKGROUND = '#444444'

if True:
    BACKGROUND = '#36393E'
    GRID = [0xcc, 0xdd, 0xee]

    NOUGHTS = np.array((0, -0x11, -0x22))
    CROSSES = np.array((-0x11, -0x11, 0))

    # Noughts: Blue / Crosses: Orange / Teleport: Green
    CROSSLIGHT = '#e1ae7b' # status messages
    CROSSMAIN  = '#874400' # main  background and tiles
    CROSSDARK  = '#5d3001' # error background and tiles in taken grids

    NOUGHTLIGHT = '#8fc2f5'
    NOUGHTMAIN  = '#1a5ea1'
    NOUGHTDARK  = '#004588'

    # green / gray used for gameplay indicators

    TELELIGHT = '#7ae089' # grid for teleport choice
    TELEMAIN  = '#018514' # tile placement + teleport
    TELEDARK  = '#015d0e'

    GRAYLIGHT = '#b8b8b8'
    GRAYMAIN  = '#515151' # grid where tile will send
    GRAYDARK  = '#383838' # tile placement + send
else:
    
    BACKGROUND = '#777777'
    GRID = [0x33, 0x44, 0x55]

    NOUGHTS = np.array((0x22, 0, 0))
    CROSSES = np.array((0, 0x33, 0))

    # Noughts: Red / Crosses: Green / Teleport: Blue
    CROSSLIGHT = '#f5a08f' # status messages
    CROSSMAIN  = '#a1301a' # main  background and tiles
    CROSSDARK  = '#881600' # error background and tiles in taken grids

    NOUGHTLIGHT = '#7ae089'
    NOUGHTMAIN  = '#018514'
    NOUGHTDARK  = '#015d0e'

    # green / gray used for gameplay indicators

    TELELIGHT = '#7bcfe1' # grid for teleport choice
    TELEMAIN  = '#007087' # tile placement + teleport
    TELEDARK  = '#014c5d'

    GRAYLIGHT = '#b8b8b8'
    GRAYMAIN  = '#515151' # grid where tile will send
    GRAYDARK  = '#666666' # tile placement + send

CORNER = np.array([
    (0, 0), (0, 50), (1, 41), (3, 32), (21, 9),
    (15, 15), (9, 21), (32, 3), (41, 1), (50, 0), (0, 0)]) / 50

CROSS = np.array([
    (0, 0), (1, 0), (4.5, 3.5), (8, 0), (9, 0),
            (9, 1), (5.5, 4.5), (9, 8), (9, 9),
            (8, 9), (4.5, 5.5), (1, 9), (0, 9),
            (0, 8), (3.5, 4.5), (0, 1), (0, 0)]) / 9

class Render:
    def __init__(self, game, size=450):
        if not isinstance(game, MNAC):
            raise TypeError('Game must be MNAC or subclass')
        self.game = game
        self.size = size

    # Relative to width of one cell, size of grid gaps
    SEPARATION = 1/4
    # Grid rounding, relative to cell width
    ROUNDING = 1/10
    
    def draw(self):
        skipDraw = self.onStart()
        if skipDraw:
            return self.drawn()

        
        game = self.game
        cell = self.size / (9 + 2 * self.SEPARATION)
        
        for i in range(9):
            gxy = np.array((i % 3, i // 3))
            gridtl = gxy * cell * (3 + self.SEPARATION)
            for j in range(9):
                rgb = np.repeat(GRID[(i % 2) + (j % 2)], 3)
                
                if game.grid == i:
                    if game.player == 1:
                        rgb += NOUGHTS
                    else:
                        rgb += CROSSES
                else:
                    if game.gridStatus[i] == 1:
                        rgb += NOUGHTS * 4
                    elif game.gridStatus[i] == 2:
                        rgb += CROSSES * 4
                color = '#{:02x}{:02x}{:02x}'.format(*rgb)
                xy = np.array((j % 3, j // 3))
                celltl = gridtl + (xy * cell)
                self.cell(i, j, celltl, cell, fill=color)
        
            gridStatus = game.gridStatus[i]
            gridTaken = (gridStatus in (1, 2))
            
            # %% cell markers
            
            for j in range(9):
                cellStatus = game.grids[i][j]
                xy = np.array((j % 3, j // 3))
                celltl = gridtl + xy * cell
                wasLast = (game.lastPlacedGrid, game.lastPlacedCell) == (i, j)
                if cellStatus == 1:
                    color = TELEMAIN if wasLast else CROSSMAIN
                    top_left = celltl + cell / 18
                    bottom_right = celltl + cell - cell / 18
                    self.ellipse((*top_left, *bottom_right),
                        outline=color, width=cell/9)
                
                elif cellStatus == 2:
                    coords = celltl + CROSS * cell
                    color = TELEMAIN if wasLast else NOUGHTMAIN
                    self.polygon(coords, fill=color)
                
                elif game.grid == i and game.state == 'inner':
                    # keyboard selector for cell
                    canTeleport = (i == j or game.gridStatus[j] != 0)
                    self.text(
                        celltl + cell/2, isLarge=False,
                        size=int(cell * 2/3), text=str(numpad(j + 1)),
                        fill=TELEMAIN if canTeleport else GRAYDARK)
            
            # %% grid markers - nought, cross
            
            if gridStatus == 1:
                self.ellipse((*(gridtl + cell/6), *(gridtl + cell*3 - cell/6)),
                    outline=CROSSMAIN, width=cell/3)
            
            elif gridStatus == 2:
                coords = gridtl + (CROSS * cell * 3)
                self.polygon(coords, fill=NOUGHTMAIN)

            elif game.grid == i or gridStatus == 3:
                pass

            else:
                color = None
                if game.state == 'inner':
                    # keyboard selector to show where placing a cell would send one.
                    # cannot be self, or a taken grid
                    if not (game.grid == i or game.grids[game.grid][i]):
                        color = GRAYLIGHT

                # keyboard selector for what grid to send / be in
                elif not (game.noMiddleStart and game.state == 'begin' and i == 4):
                    color = TELEMAIN

                if color:
                    self.text(
                        gridtl + cell * 6/9, isLarge=True,
                        text=str(numpad(i+1)), size=int(cell * 2),
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
                self.polygon(shape, fill=BACKGROUND)

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
        self.image = Image.new('RGB', (self.size, self.size), color=BACKGROUND)
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
    game = MNAC()
    plays = random.randrange(3, 40)
    plays = 50
    game.stressTest(plays)
    r = ImageRender(game, size=450)
    r.draw().save('test_image.png')
    #draw_game(game, size=1024).save('test_image.png')
