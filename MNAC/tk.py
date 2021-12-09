'''
Tkinter implementation of Meta Noughts and Crosses.
Requires Python >3.6, tkinter and mnac.

1.0: release
1.1: keyboard indicators / keyboard controls are like numpad
1.2: new status menu, controls, help menu
1.3: better mouse handling
'''

import random

import tkinter as tk
import numpy as np

import mnac
import render

TITLE = 'TkMNAC v1.3dev / yunru.se'



class CanvasRender(render.Render):
    '''Tkinter Canvas-based renderer.'''

    font = 'Segoe UI'

    def __init__(self, app, theme='light'):
        self.app = app
        self.canvas = app.canvas
        self.coordinates = {}
        self.theme = render.THEMES[theme]
        self.error = False

    def draw(self):
        self.game = self.app.game
        self.error = self.app.error

        # determine colours and status
        players = [
            ('gray', 'Unknown error', 'Unknown error'),
            ('nought', 'Noughts', 'Noughts wins!'),
            ('cross', 'Crosses', 'Crosses wins!'),
            ('gray', 'Neutral', "It's a draw...")
        ]

        code, name, _ = players[self.game.player]

        titlefill = self.theme[code]['light']

        if self.error:
            text = self.error
        elif self.game.winner:
            text = players[self.game.winner][2]
        else:
            statuses = {
                'begin': 'grid to start in',
                'inner': 'cell to play in',
                'outer': 'grid to send to',
            }
            text = '{}, pick a {}'.format(name, statuses[self.game.state])

        # get canvas details

        w, h, self.size, self.topleft, header_height = self.app.coordinate()

        if w > h:
            self.topleft += ((w - h) / 2, 0)
        else:
            self.topleft += (0, (h - w) / 2)

        self.canvas.config(bg=self.background())
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

        def draw_glyph(fromRight, glyph, fill): return self.canvas.create_polygon(
            *(glyph * glyph_size + (
                self.topleft[0] + self.size + fromRight * glyph_size,
                (header_height - glyph_size) / 2 + 2)).flatten(),
            width=0, fill=fill, tags='status')

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
                'Keys 1-9 and mouse/touch:  Play in cell / grid'
            ), start=1):
                header(w/2, self.topleft[1] + i * 1.5 *
                       font_size, fill='black', text=text)

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
        self.bind_all('<Control-r>', self.restart)
        self.bind_all('<Tab>', self.toggleHelp)
        self.bind_all('<Escape>', self.clearError)
        self.canvas.bind('<Button-1>', self.onClick)

        def callbacker(i): return lambda *event: self.play(mnac.numpad(i))
        for i in range(1, 10):
            self.bind_all(str(i), callbacker(i))
        self.restart()

    def restart(self, *event):
        self.showHelp = False
        self.error = ''

        self.game = mnac.MNAC(middleStart=False)
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
        if self.game.winner:
            return
        
        w, h, s, tl, header_height = self.coordinate()
        x = (event.x - tl[0]) * 9 / s

        if (0 < event.y < header_height) and (0 < x < 9):
            # status bar click
            if x < 2 or self.showHelp:
                self.toggleHelp()
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

        if self.game.state in ('outer', 'begin'):
            self.play(grid)
        elif self.game.state == 'inner':
            if grid == (self.game.grid + 1):
                self.play(cell)
            else:
                self.play(grid)

    def play(self, index):
        if self.game.winner:
            return
        
        self.error = ''
        try:
            self.game.play(index)
        except mnac.MoveError as e:
            self.error = mnac.ERRORS[e.args[0]]
        self.redraw()

    def test_turn(self, *event):
        '''debug: play random moves'''
        choices = list(range(9))
        random.shuffle(choices)
        for i in choices:
            try:
                self.game.play(i + 1)
                break
            except mnac.MoveError:
                continue

        self.render.draw()

        if not self.game.winner:
            self.after(500, self.test_turn)


if __name__ == '__main__':
    self = UIMNAC()
    self.mainloop()
