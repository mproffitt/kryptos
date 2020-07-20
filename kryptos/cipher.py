import pandas as pd
from IPython import display
from ipywidgets import Label, HTML, VBox, HBox, Output
from ipyevents import Event
from . import helpers, Character, Highlighter

globalout = Output()
class Cipher(object):
    """
    Main cipher class

    Creates a list Character objects used to map the cipher into plaintext
    """
    cipher    = None
    alphabet  = None
    _vbox     = None
    _hbox     = None
    _label    = None
    _event    = None
    _html     = None
    _use      = 'cipher'
    _cindex   = 0
    _currentr = 0
    _currentc = 0

    def __init__(self, ciphertext, invert=False):
        self.cipher = []
        self.ciphertext = ciphertext.upper()

        # ------------------------------------------------------------
        # `lacunatext` is the full ciphertext, each character removed
        # from Z.
        # ------------------------------------------------------------
        self.lacunatext = ''.join(
            [helpers.distancefrom(c, 'Z') for c in self.ciphertext]
        )
        if invert:
            self.ciphertext = self.lacunatext
            self.lacunatext = ciphertext

        helpers.distance_calculator(self.ciphertext, self.lacunatext)

        # ------------------------------------------------------------
        # A polarity table is formed. This is used to help determine
        # the rules. As each character is found, the polarity of that
        # character changes
        # ------------------------------------------------------------
        self.alphabet = {
            character: False for character in helpers.alphabet
        }

        # ------------------------------------------------------------
        # Create an object for each character setting the value of
        # 'use_alt' to the current value of the boolean alphabet.
        # We then  invert the alphabet flag for the next occurance of
        # that character.
        # ------------------------------------------------------------
        for i, c, l in zip(range(1, self.length + 1), self.ciphertext, self.lacunatext):
            cipher_flag = self.alphabet[c] if c not in ['M', 'Z'] else True
            lacuna_flag = self.alphabet[c] if l not in ['M', 'Z'] else True
            self.cipher.append(
                Character(c, i, cipher_flag, self.ciphertext)
            )
            self.alphabet[c] = not self.alphabet[c]

        # Used for displaying the current position on the ciphergrid
        self._currentc = 'A'
        self._currentr = 0

    def setup_jupyter(self):
        """
        Sets up elements on the page for use with a Jupyter notebook.
        """
        self._label = Label('Move the cursor over the cell and use the left and right arrow keys to navigate')
        self._hbox = HBox()
        self._html = HTML('<h3>Label position?</h3>')

        self._inner = VBox()
        self._vbox = VBox([self._html, self._inner, self._label])
        self._event = Event(source=self._vbox, watched_events=['keydown'])
        self._event.on_dom_event(self.handle_event)

    @property
    def length(self):
        """ Return the length of the current cipher """
        return len(self.ciphertext)

    def intermediate(self, pos):
        """ Get the intermediate character from the cipher """
        return self[pos].decipher

    def __str__(self):
        return ''.join([str(c) for c in self])

    def __iter__(self):
        return getattr(self, self._use).__iter__()

    def __getitem__(self, key):
        return getattr(self, self._use).__getitem__(key)

    def __len__(self):
        return self.length

    @globalout.capture()
    def handle_event(self, event):
        """ Jupyter ipyevents binding code """
        if 'code' in event.keys():
            self.setposition(event['code'])
            self._draw()

    def setposition(self, code):
        """
        Sets the current cipher position on the grids
        """
        pagesize = 5
        if code == 'ArrowLeft':
            self._cindex = self._cindex - 1 if self._cindex > 0 else len(self)-1
        elif code == 'ArrowRight':
            self._cindex = self._cindex + 1 if self._cindex < len(self)-1 else 0
        elif code == 'ArrowUp':
            self._cindex = self._cindex + pagesize if (self._cindex + pagesize) < len(self)-1 \
                else 0 + ((self._cindex + pagesize) - len(self))
        elif code == 'ArrowDown':
            self._cindex = self._cindex - pagesize if (self._cindex - pagesize) >= 0 \
                else (len(self) - (pagesize - self._cindex))
        self._currentc = helpers.i2a((self._cindex % 26) + 1)
        self._currentr = self._cindex // 26

    def _draw(self):
        """ Jupyter notebook code to draw widgets """
        left       = Output()
        right      = Output()
        properties = Output()
        conditions = Output()
        decipher   = Output()
        deciphered = Output()

        tables = {
            True:  [],
            False: []
        }
        for key in self[self._cindex].cipher.keys():
            characters = self[self._cindex].cipher[key].get()
            for i, character in zip(range(len(characters)), characters):
                partial = Output()
                df = self[self._cindex].all_positions(helpers.i2a(character))
                df = df.style.set_caption(
                    '{} ({})'.format(character, helpers.i2a(character))
                ).set_table_attributes(
                    'style="font-size: 10px"'
                )

                with partial:
                    display.display(df)
                tables[key].append(partial)

        with left:
            display.display(self[self._cindex].cipher[True].apply)
        with right:
            display.display(self[self._cindex].cipher[False].apply)

        with properties:
            display.display(
                self[self._cindex].properties_table
                    .style.set_caption('Properties')
                    .set_table_attributes(
                        'style="font-size: 10px"'
                    ).set_properties(
                        subset=['Value'],
                        **{'width': '60px'}
                    )
            )

        with conditions:
            display.display(
                self[self._cindex].condition_table
                    .style.set_caption('Conditions')
                    .set_table_attributes(
                        'style="font-size: 10px"'
                    )
            )

        with decipher:
            display.display(
                self[self._cindex]
                    .all_positions()
                    .style.set_caption('Selected')
                    .set_table_attributes(
                        'style="font-size: 10px"'
                    )
            )

        with deciphered:
            display.display(self.as_dataframe())

        subtables = VBox()
        subtables.children = [HBox(tables[True]), HBox(tables[False])]

        self._hbox.children = [left, right]
        self._inner.children = [
            self._hbox,
            HBox([VBox([properties, conditions]), decipher, subtables, deciphered]),
            globalout
        ]
        self._html.value = '<h3>Current character {}, index {}, deciphered to {}</h3>'.format(
            self[self._cindex].character,
            self._cindex + 1,
            str(self[self._cindex])
        )

    def as_dataframe(self, ciphertext=False):
        """
        display the finished cipher in a dataframe
        """
        n = 26
        ciphertext = [str(i) for i in self] if not ciphertext else [i for i in ciphertext]
        df = pd.DataFrame(
            [self[i:i + n] for i in range(0, len(ciphertext), n)]
        )
        mask = df.applymap(lambda x: x is None)
        cols = df.columns[(mask).any()]
        for col in df[cols]:
            df.loc[mask[col], col] = ''
        df.columns = helpers.alphabet
        return df.style.hide_index().set_caption(
            'Deciphered plaintext'
        ).set_table_attributes(
            'style="font-size: 10px"'
        ).applymap(
            Highlighter(None, None).highlightg,
            subset=pd.IndexSlice[self._currentr, self._currentc]
        )

    def display(self, index=1):
        """
        Display a given character in a Jupyter cell
        """
        index = 1 if index == 0 else index
        display.clear_output(wait=True)
        if index is not None:
            self._cindex = (index - 1)
            self._currentc = helpers.i2a((self._cindex % 26)+1)
        self._currentr = self._cindex // 26
        self._draw()
        display.display(self._vbox)
