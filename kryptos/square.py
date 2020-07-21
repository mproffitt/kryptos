import pandas as pd
from . import Table, Highlighter, helpers

class Square(object):
    """
    Used to calculate the shape of the grid to plot on the dataframe
    """
    tl            = ''
    bl            = ''
    tr            = ''
    br            = ''
    replace       = None
    character     = ''
    _grid         = []
    _highlight    = None
    _lacuna       = None
    _cipher       = None
    _active       = None

    lacuna_active = False
    cipher_active = False
    mapped    = False
    map       = False

    polarity      = False
    table         = None
    ORDER         = [
        'tl', 'tr', 'br', 'bl'
    ]

    def __init__(self, character, polarity, map, ciphertext):
        self.character = character
        character_index = helpers.a2i(character)
        self.table = Table(ciphertext, polarity)
        self.map = map
        self.tl = self.bl = self.tr = self.br = ''

    def plot(self):
        """
        Plot the grid using the current character, the polarity and whether the
        current character is to be replaced or not
        """
        self.table.create()
        self.replace = self.table.keys['replace']

        mapchar = self.replace[self.character] \
            if self.map and self.character in self.replace.keys() \
            else self.character

        self.mapped = mapchar != self.character

        top    = [
            i for i in range(
                len(self.table.keys['top'])
            ) if mapchar in self.table.keys['top'][i]
        ][0] + 1

        right  = [
            i for i in range(
                len(self.table.keys['right'])
            ) if mapchar in self.table.keys['right'][i]
        ][0] + 1

        bottom = [
            i for i in range(
                len(self.table.keys['bottom'])
            ) if self.character in self.table.keys['bottom'][i]
        ][0] + 1

        left   = [
            i for i in range(
                len(self.table.keys['left'])
            ) if self.character in self.table.keys['left'][i]
        ][0] + 1

        self._grid = [
            top     if top < bottom else bottom,
            left    if left < right else right,
            bottom  if bottom > top else top,
            right   if right > left else left
        ]

        self.tl = self.table.loc[self._grid[1], self._grid[0]]
        self.tr = self.table.loc[self._grid[1], self._grid[2]]
        self.bl = self.table.loc[self._grid[3], self._grid[0]]
        self.br = self.table.loc[self._grid[3], self._grid[2]]
        self._highlight = Highlighter(self.table, self.gridref)
        self.markcipher(self.character)

    def get(self):
        """
        Return the current grid, clockwise from top left
        """
        return [self.tl, self.tr, self.br, self.bl]

    def markcipher(self, char, recurse=True):
        """
        Marks a given grid square as a cipher characer

        :param: char char
        :param: bool recurse

        :If recurse is True, will call itself with the inverse position
        """
        inverse = helpers.distancefrom(char, 'Z')
        char = helpers.a2i(char)
        pos = ''
        if char in self.get():
            pos = Square.ORDER[self.get().index(char)]
            self._highlight.cipher(pos)

            if recurse:
                self.cipher_active = pos
                self._cipher = char
            else:
                self.lacuna_active = pos
                self.mark_lacuna(char)
        if recurse:
            self.markcipher(inverse, False)

    def clear_active(self):
        self._active = None

    def active(self, corner):
        """ Wrapper for Highlight.active """
        if isinstance(corner, int):
            corner = Square.ORDER[self.get().index(corner)]
        self._active = corner
        return self.active_char(corner)

    def active_char(self, pos):
        """
        Find the active character at a given position

        :param: string pos

        :return: int
        """
        return {
            'tl': self.table.loc[self._grid[1], self._grid[0]],
            'tr': self.table.loc[self._grid[1], self._grid[2]],
            'bl': self.table.loc[self._grid[3], self._grid[0]],
            'br': self.table.loc[self._grid[3], self._grid[2]],
        }[pos]

    def contains(self, what):
        """ Test if a given character exists here """
        return helpers.a2i(what) in self.get()

    def mark_lacuna(self, character):
        """ Wrapper for Highlight.lacuna """
        if isinstance(character, int):
            character = helpers.i2a(character)
        position = helpers.distancefrom(character, 'Z')
        if self.contains(position):
            position = Square.ORDER[self.get().index(helpers.a2i(position))]
            self._lacuna = position

    @property
    def gridref(self):
        return self._grid

    @property
    def apply(self):
        self._highlight.cipher(self.cipher_active)
        self._highlight.lacuna(self.lacuna_active)
        if self._active:
            self._highlight.active(self._active)
        return self._highlight.apply()
