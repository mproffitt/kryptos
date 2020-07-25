import pandas as pd

class Highlighter(object):
    """
    Applies grid formatting to a pandas dataframe object

    This is a helper class which draws up the grid.
    """
    _df         = None
    _applied    = None
    _grid       = None
    _active_pos = None
    _cipher_pos = None

    def __init__(self, df, grid):
        self._df            = df
        self._grid          = grid
        self._active_pos    = None
        self._cipher_pos    = None
        self._active_lacuna = None
        self._cipher_lacuna = None

    def highlighty(self, df, color='yellow'):
        """ helper method for colouring grid cells in yellow """
        return 'background-color: {}'.format(color)

    def highlightr(self, df, color='#FF0000'):
        """ helper method for colouring grid cells in red """
        return 'background-color: {}; color: #FFFFFF'.format(color)

    def highlightlr(self, df, color='#FBACA8'):
        """ helper method for colouring grid cells in red """
        return 'background-color: {}; color: #FFFFFF'.format(color)

    def highlightb(self, df, color='#85E3FF'):
        """ helper method for colouring grid cells in blue """
        return 'background-color: {};'.format(color)

    def highlightl(self, df, color='#D291BC'):
        """ helper method for colouring grid cells in lilac """
        return 'background-color: {};'.format(color)

    def highlights(self, df, color='#EDC9AF'):
        """ helper method for colouring grid cells in sand """
        return 'background-color: {};'.format(color)

    def highlightg(self, df, color='#00FF00'):
        """ helper method for colouring grid cells in green """
        return 'background-color: {}'.format(color)

    def highlightlg(self, df, color='#90EE90'):
        """ helper method for colouring grid cells in green """
        return 'background-color: {}'.format(color)

    def apply_grid(self):
        """ Draws a grid on the dataframe and returns the style object """
        return self._df.style.applymap(
            self.highlighty, subset=pd.IndexSlice[:, self._grid[0]]
        ).applymap(
            self.highlighty, subset=pd.IndexSlice[self._grid[1], :]
        ).applymap(
            self.highlighty, subset=pd.IndexSlice[:, self._grid[2]]
        ).applymap(
            self.highlighty, subset=pd.IndexSlice[self._grid[3], :]
        ).set_table_attributes(
            'style="font-size: 10px"'
        )

    def active(self, pos):
        """
        Set a given position active

        :param: string pos

        This will set a given gridref as being an active cell for the ciphertext,
        colouring it red on the grid
        """
        self._active_pos = pos

    def active_lacuna(self, pos):
        self._active_lacuna = pos

    def cipher_lacuna(self, pos):
        self._cipher_lacuna = pos

    def cipher(self, pos):
        """
        marks a given cell as containing the current cipher character

        :param: string pos
        """
        self._cipher_pos = pos

    def _active(self, pos, function=None):
        if not function:
            function=self.highlightr
        {
            'tl': lambda m: m.applymap(function, subset=pd.IndexSlice[self._grid[1], self._grid[0]]),
            'tr': lambda m: m.applymap(function, subset=pd.IndexSlice[self._grid[1], self._grid[2]]),
            'bl': lambda m: m.applymap(function, subset=pd.IndexSlice[self._grid[3], self._grid[0]]),
            'br': lambda m: m.applymap(function, subset=pd.IndexSlice[self._grid[3], self._grid[2]]),
        }[pos](self._applied)

    def apply(self):
        """
        Applies the current grid to the dataframe and returns the style object for rendering.
        """
        self._applied = self.apply_grid()
        # Set the active corner in red
        if self._active_pos:
            self._active(self._active_pos, function=self.highlightr)

        # cipher goes green if available
        if self._cipher_pos:
            self._active(self._cipher_pos, function=self.highlightg)

        # light red for active_lacuna if set
        if self._active_lacuna:
            self._active(self._active_lacuna, function=self.highlightlr)

        # light green for cipher_lacuna
        if self._cipher_lacuna:
            self._active(self._cipher_lacuna, function=self.highlightlg)

        return self._applied
