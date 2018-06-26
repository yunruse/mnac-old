'''Tkinter implementation of Meta Noughts and Crosses.
Requires Python >3.6, tkinter and mnac.

1.0: release
1.1: keyboard indicators / keyboard controls are like numpad
1.2: new status menu, controls, help menu
1.3: automatic keyboard/mouse selector, better mouse handling
'''

print(**{},end='') # If this line fails, you probably don't have Python 3.6

import random

import tkinter as tk
import numpy as np

from mnac import MoveError, MNAC, numpad
import render

TITLE = 'TkMNAC v1.3dev / yunru.se'

CROSS = np.array([
    (0, 0), (1, 0), (4.5, 3.5), (8, 0), (9, 0),
            (9, 1), (5.5, 4.5), (9, 8), (9, 9),
            (8, 9), (4.5, 5.5), (1, 9), (0, 9),
            (0, 8), (3.5, 4.5), (0, 1), (0, 0)]) / 9

MOUSE = np.array([
    ( 8,  0), ( 8, 28), (14, 22), (18, 32),
    (23, 30), (19, 19), (27, 20), ( 8,  0)
]) / 32
KEYBOARD_OUTER = np.array([
    (4, 2), (28, 2), (30, 4), (30, 28), (28, 30), (4, 30), (2, 28), (2, 4), (4, 2),
]) / 32
KEYBOARD_INNER = np.array([
    (7, 5), (25, 5), (27, 7), (27, 25), (25, 27), (7, 27), (5, 25), (5, 7), (7, 5),
]) / 32

class CanvasRender(render.Render):
    '''Tkinter Canvas-based renderer.'''

    font = 'Segoe UI'

    def __init__(self, app):
        self.app = app
        self.canvas = app.canvas
        self.coordinates = {}

    def draw(self):
        self.game = self.app.game
        self.error = self.app.error
        # determine colours and status
        
        P = lambda p: (('Noughts', render.NOUGHTMAIN) if p == 1 else ('Crosses', render.CROSSMAIN))
        player, bg = P(self.game.player)
        titlefill = render.NOUGHTLIGHT if player == 'Noughts' else render.CROSSLIGHT
        
        if self.error:
            text = self.error
            bg = render.NOUGHTDARK if player == 'Noughts' else render.CROSSDARK
        elif self.game.winner == 3:
            text = "It's a draw..."
            bg = 'gray'
        elif self.game.winner:
            text, bg = P(self.game.winner)
            text = '{} wins!'.format(text)
        else:
            if self.game.state == 'begin':
                status = 'grid to start in'
            elif self.game.state == 'inner':
                status = 'cell to play in'
            else:
                status = 'grid to send to'
            text = '{}, pick a {}'.format(player, status)

        
        # get canvas details

        w, h, self.size, self.topleft, header_height = self.app.coordinate()
        
        if w > h:
            self.topleft += ((w - h) / 2, 0)
        else:
            self.topleft += (0, (h - w) / 2)
    
        self.canvas.config(bg=bg)
        self.canvas.delete('status', 'backing', 'mark', 'play')
        self.canvas.tag_unbind('backing', '<Button-1>')

        font_size = int(self.size / 32)
        glyph_size = int(font_size * 1.5)

        leftText = 'tab: help'
        if self.app.showHelp:
            text = ''
            leftText = 'tab: back to game'
        
        header = (
            lambda x, y=header_height / 2, fill=titlefill, **kw:
            self.canvas.create_text(
                x, y, fill=fill,
                tags='status', font=(self.font, font_size), **kw))
        
        header(self.topleft[0] + 5,           anchor='w', text=leftText)
        header(self.topleft[0] + self.size/2, anchor='center', text=text)

        draw_glyph = lambda fromRight, glyph, fill: self.canvas.create_polygon(
            *(  glyph * glyph_size + (
                    self.topleft[0] + self.size + fromRight * glyph_size,
                    (header_height - glyph_size) / 2 + 2)).flatten(),
            width=0, fill=fill, tags='status')
        
        if self.app.mouseMayPlay:
            draw_glyph(-2, MOUSE, titlefill) 

        if self.app.keyboardMayPlay:
            draw_glyph(-1, KEYBOARD_OUTER, titlefill)
            draw_glyph(-1, KEYBOARD_INNER, bg)
            header(self.topleft[0] + self.size - glyph_size / 2, anchor='center', text='A')

        render.Render.draw(self)
    
        # draw beginning help in middle cell

        if self.app.showHelp:
            self.canvas.create_rectangle(
                *self.topleft, *(self.topleft + self.size),
                width=0, fill=titlefill, tags='status', stipple="gray50")
            for i, text in enumerate((
                'The board is 9 grids each with 9 cells. Play to win',
                'a grid, and win the larger grids to win the game.',
                '',
                'Place a tile in the tile and you will put your opponent',
                'into the equivalent grid. For example, if you are in the',
                'top left grid and play the bottom cell, your opponent',
                'will have to play in the bottom grid, and so on.',
                '',
                'One exception is that you may never send your',
                'opponent to your own grid, or one that is captured -',
                'tiles that would do so are marked as green, and are',
                "'teleporters' allowing you to choose where to send",
                'your opponent. As grids become taken, there is less',
                'choice, so be careful to tactically set up traps!',
                '',
                'CONTROLS:',
                'Control-R: Restart the game',
                'Control-P: Change which players are controlled by',
                'keyboard and mouse (indicated by the top right icons)',
                'Keys 1-9 and mouse/touch:  Play in cell / grid'
                ), start=1):
                header(w/2, self.topleft[1] + i * 1.5 * font_size, fill='black', text=text)
        

    def cell(self, grid, cell, tl, size, fill):
        tl += self.topleft
        coords = (*tl, *(tl+size))
        backing = self.canvas.create_rectangle(
            *coords, width=0, fill=fill, tags='backing')

        self.coordinates[grid+1, cell+1] = coords

    def ellipse(self, coords, outline, width):
        coords += (*self.topleft, *self.topleft)
        self.canvas.create_oval(
            *coords, width=width, outline=outline, tags='mark')

    def polygon(self, coords, fill):
        coords += self.topleft
        self.canvas.create_polygon(
            *coords.flatten(), fill=fill, width=0, tags='mark')

    def text(self, coords, isLarge, text, size, fill):
        coords += self.topleft
        fiddle = (1/9, -7/6) if isLarge else (-2/9, -2/3)
        coords += np.array(fiddle) * self.size / (9 + 2 * self.SEPARATION)
        self.canvas.create_text(
            *coords, text=text, fill=fill, font=(self.font, size), anchor='nw', tags='play')

class UIMNAC(tk.Tk):
    def __init__(self, **kwargs):
        '''Initialise frame. Set players to None or a number.'''

        # None (both input kinds) or 1 or 2
        self._keyboardPlayer = kwargs.get('keyboardPlayer', None)
        
        tk.Tk.__init__(self)
        self.title(TITLE)
        self.minsize(400, 424)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(1, weight=1)
        
        self.canvas = tk.Canvas(
            self, height=0, width=0,
            bd=0, highlightthickness=0, relief='ridge')
        self.canvas.grid(row=1, column=1, columnspan=3, sticky='news')

        self.render = CanvasRender(self)
        
        self.bind_all('<Configure>', self.redraw)
        self.bind_all('<Control-p>', self.changePlayer)
        self.bind_all('<Control-r>', self.restart)
        self.bind_all('<Tab>', self.toggleHelp)
        self.bind_all('<Escape>', self.clearError)
        self.canvas.bind('<Button-1>', self.onClick)
        
        callbacker = lambda i: lambda *event: self.onKey(i)
        for i in range(1, 10):
            self.bind_all(str(i), callbacker(i))
        self.restart()
    
    def restart(self, *event):
        self.showHelp = False
        self.error = ''
        
        self.game = MNAC(noMiddleStart=True)
        self.game.onPlace = self.onPlace
        self.redraw()
    
    keyboardMayPlay = property(lambda s: not s.showHelp and (
        s._keyboardPlayer is None or s._keyboardPlayer == s.game.player))

    mouseMayPlay = property(lambda s: not s.showHelp and (
        s._keyboardPlayer is None or s._keyboardPlayer != s.game.player))
     
    def changePlayer(self, *event):
        k = self._keyboardPlayer
        if k is None:
            self._keyboardPlayer = 1
        elif k == 1:
            self._keyboardPlayer = 2
        else:
            self._keyboardPlayer = None
        self.redraw()

    def clearError(self, *event):
        self.error = ''
        self.redraw()

    def toggleHelp(self, *event):
        self.showHelp = not self.showHelp
        self.redraw()

    def coordinate(self):
        w, h = self.canvas.winfo_width(), self.canvas.winfo_height()
        header_height = h / 18
        h -= header_height
        s = min(w, h)
        tl = np.array((0, header_height), dtype=float)

        return w, h, s, tl, header_height

    def redraw(self, *event):
        self.render.draw()
    
    def onClick(self, event):
        w, h, s, tl, header_height = self.coordinate()
        x = (event.x - tl[0]) / (s * 9)
        
        if (0 < event.y < header_height) and (0 < x < 9):
            # status bar click
            if x < 2 or self.showHelp:
                self.toggleHelp()
            elif x > 8:
                self.changePlayer()
            else:
                self.clearError()

        # Iterate through all coordinates the renderer claims
        # each cell was at
        for coord, bounds in self.render.coordinates.items():
            x1, y1, x2, y2 = bounds
            if x1 <= event.x <= x2 and y1 <= event.y <= y2:
                grid, cell = coord
                break
        else:
            return
        
        if self.game.winner:
            return self.restart()

        if self.mouseMayPlay:
            if self.game.state in ('outer', 'begin'):
                self.play(grid)
            elif self.game.state == 'inner':
                if grid == (self.game.grid + 1):
                    self.play(cell)
                else:
                    self.play(grid)

    def onKey(self, index):
        if self.game.winner:
            return self.restart()
        
        if self.keyboardMayPlay:
            self.play(numpad(index))

    def play(self, index):
        if self.game.winner:
            return self.restart()
        self.error = ''
        try:
            self.game.play(index)
        except MoveError as e:
            self.error = e.args[0]
        self.redraw()

    def test_turn(self, *event):
        '''debug: play random moves'''
        choices = list(range(9))
        random.shuffle(choices)
        for i in choices:
            try:
                self.game.play(i + 1)
                break
            except MoveError:
                continue

        self.render.draw()
        
        if not self.game.winner:
            self.after(500, self.test_turn)
        

if __name__ == '__main__':
    self = UIMNAC()
    #self.mainloop()
