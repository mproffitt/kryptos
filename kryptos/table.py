import pandas as pd
from . import helpers

class Table(object):
    """
    The Table class is a wrapper for a pandas DataFrame class with functionality
    to load the table, sort it and create the keys on it.
    """
    table = None
    polarity = ''
    ciphertext = None
    lacuna     = None
    poles      = None

    keys = {}

    _order = [14, 6, 6, 12,]

    def __init__(self, ciphertext, polarity):
        self.ciphertext = ciphertext
        self.lacuna = ''.join([helpers.distancefrom(c, 'Z') for c in ciphertext])
        self.polarity = polarity
        self.table = []

        self.poles = {
            True: 'E',
            False: 'M',
        }

    def create(self):
        """
        Creates A pandas DataFrames from the current instance

        This table will either be 13x13 in size if all rows are even, or
        13x26 in size if the rows are a mixture of odd and even characters.
        """
        for distance, pole in helpers.initialise(self.ciphertext, self.lacuna):
            if pole == self.poles[self.polarity]:
                self.table.append([helpers.a2i(c) for c in distance])

        self.table = pd.DataFrame(self.table)
        self.table.columns = [helpers.alphabet[(i-1)] for i in self.table.iloc[0]]
        if self.table.shape[0] < 13:
            self.table.loc[len(self.table)] = [
                26 if i % 2 == 0 else 13 for i in self.table.iloc[0]
            ]
        self.table = self.table.loc[
            :,~self.table.columns.duplicated()
        ].sort_values(by=0, axis=1)
        self.table.columns = [i for i in range(1, self.table.shape[1] + 1)]
        self.table.index   = [i for i in range(1, self.table.shape[0] + 1)]
        self.keys = self.create_keys()

    def create_keys(self):
        """
        Creates a set of keys for the current table.

        This method hard-wires a set of replacement characters which may well belong as a
        definition in the helpers class.
        """
        keys = {
            'replace': {
                'M': 'K',
                'V': 'J',
                'Z': 'V',
                'K': 'V',

                'E': 'I',
                'Q': 'L',
                'U': 'O',
                'A': 'E',
                'W': 'H',
                'H': 'A',
                'O': 'N',
                'R': 'Q',
            }
        }
        pairings = [
            (helpers.i2a(x), helpers.i2a(x+13)) for x in range(1, 14)
        ]

        keys['top']    = helpers.alphabet
        keys['bottom'] = helpers.alphabet[::-1]
        keys['left']   = self.order(self._order[0], pairings)
        keys['right']  = self.order(self._order[1], pairings)

        if self.polarity:
            keys['top']    = self.order(self._order[2], pairings)
            keys['bottom'] = self.order(self._order[3], pairings)

        return keys

    def order(self, start, pairings, axis=1):
        """
        Orders the current keys into a set order

        :param: int   start    The index to start the order sequence from
        :param: list  pairings A list of tuples representing (character, (character+13))

        :return: list
        """
        keys = []
        increment = start
        for _ in range(self.table.shape[axis]):
            for pair in pairings:
                if helpers.i2a(start) in pair:
                    keys.append(pair)
                    break
            start = (start + increment) % 26
        return keys

    def __getattr__(self, what):
        """
        We pass most calls to the dataframe here.
        """
        try:
            return getattr(self.__class__, what)
        except AttributeError:
            pass
        return getattr(self.table, what)
