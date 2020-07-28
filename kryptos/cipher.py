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

        helpers.initialise(self.ciphertext, self.lacunatext)

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
        self._vbox = VBox([self._html, self._inner])
        self._event = Event(source=self._vbox, watched_events=['keydown'])
        self._event.on_dom_event(self.handle_event)
        return self

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
            if event['shiftKey']:
                event['code'] = 'Shift+' + event['code']
            try:
                self.setposition(event['code'])
                self._draw()
            except IndexError:
                # If we're out of index, we're beyond the end of the cipher
                # simply call again to move to the bext row
                self.handle_event(event)

    def setposition(self, code):
        """
        Sets the current cipher position on the grids
        """
        pagesize = 10
        shiftpage = 5
        prevrow = ((26 - helpers.a2i(self._currentc)) + helpers.a2i(self._currentc))
        nextrow = helpers.a2i(self._currentc) + (26 - helpers.a2i(self._currentc))
        lastrow = (len(self) % 26) - nextrow if (len(self) % 26) - nextrow > 0 \
            else (len(self) - (26 * (len(self)  //  26)))

        primary = {
            'ArrowLeft':  self._cindex - 1 if self._cindex > 0 else len(self) - 1,
            'ArrowRight': self._cindex + 1 if self._cindex < len(self)-1 else 0,
            'PageDown': self._cindex + pagesize if (self._cindex + pagesize) < len(self)-1 \
                else 0 + ((self._cindex + pagesize) - len(self)),
            'PageUp': self._cindex - pagesize if (self._cindex - pagesize) >= 0 \
                else (len(self) - (pagesize - self._cindex)),
            'Shift+ArrowLeft': self._cindex - shiftpage if (self._cindex - shiftpage) >= 0 \
                else (len(self) - (shiftpage - self._cindex)),
            'Shift+ArrowRight': self._cindex + shiftpage if (self._cindex + shiftpage) < len(self)-1 \
                else 0 + ((self._cindex + shiftpage) - len(self)),
            'Home':  0,
            'End': len(self) - 1,
            'ArrowDown': (self._cindex + prevrow) if self._cindex + prevrow < len(self) \
                else helpers.a2i(self._currentc) - 1,
            'ArrowUp': helpers.a2i(self._currentc) - 1 + (
                (26 * (self._currentr - 1)) if self._currentr - 1 >= 0 else (26 * (len(self) // 26))
            )

        }
        self._cindex = primary[code] if code in primary.keys() else self._cindex
        self._currentr = self._cindex // 26
        self._currentc = helpers.i2a((self._cindex % 26) + 1)

    def _draw(self):
        """ Jupyter notebook code to draw widgets """
        left       = Output()
        right      = Output()
        properties = Output()
        conditions = Output()
        deciphered = Output()
        tablekey   = Output()
        original   = Output()

        tables = {
            True:  [],
            False: []
        }
        for key in self[self._cindex].cipher.keys():
            characters = self[self._cindex].cipher[key].get()
            for i, character in zip(range(len(characters)), characters):
                partial = Output()
                df = self[self._cindex].all_positions(helpers.i2a(character))
                style = df.style.set_caption(
                    '{} ({})'.format(character, helpers.i2a(character))
                ).set_table_attributes(
                    'style="font-size: 10px"'
                ).hide_index()
                if self[self._cindex].table == key and df.equals(self[self._cindex].all_positions()):
                    style.set_properties(**{'background-color': '#FF0000', 'color': '#FFFFFF'})

                with partial:
                    display.display(style)
                tables[key].append(partial)

        with properties:
            display.display(
                self[self._cindex].properties_frame
                    .style.set_caption('Properties')
                    .set_table_attributes(
                        'style="font-size: 10px"'
                    ).set_properties(
                        subset=['Value'],
                        **{'width': '120px'}
                    ).hide_index()
            )

        with conditions:
            df = self[self._cindex].condition_frame.reset_index()
            df.columns = ['', 'index', 'cipher', 'lacuna',]
            display.display(
                df.style.set_caption('Conditions')
                    .set_table_attributes(
                        'style="font-size: 10px"'
                    ).hide_index()
            )

        with original:
            display.display(self.as_dataframe(ciphertext=self.ciphertext, label='Original ciphertext'))

        with deciphered:
            display.display(self.as_dataframe())

        with tablekey:
            display.display(self.table_key)

        with left:
            display.display(self[self._cindex].cipher[True].apply)
        with right:
            display.display(self[self._cindex].cipher[False].apply)

        subtables = VBox()
        subtables.children = [HBox(tables[True]), HBox(tables[False])]

        self._hbox.children = [left, right]
        self._inner.children = [
            self._hbox,
            HBox([VBox([properties, conditions]), subtables, VBox([original, deciphered])]),
            globalout
        ]
        self._html.value = '<h3>Current character {} ({}), lacuna {} ({}) index {}, deciphered to {} algorithm {}</h3>'.format(
            self[self._cindex].character,
            self[self._cindex].cindex,
            self[self._cindex].lacuna,
            self[self._cindex].lindex,
            self._cindex + 1,
            str(self[self._cindex]),
            self[self._cindex].algorithm + 1
        )

    @property
    def table_key(self):
        key = pd.DataFrame([
            ['', 'Cipher character',],
            ['', 'Active character',],
            ['', 'Cipher lacuna',],
            ['', 'Active lacuna',],
            ['', 'Both match',],
            ['', 'Properties match',],
            ['', 'Contitions match',],
        ], columns=['Colour', 'Description'])
        return key.style.applymap(
                lambda _: 'background-color: #00FF00', pd.IndexSlice[0, 'Colour',]
            ).applymap(
                lambda _: 'background-color: #FF0000; color: #FFFFFF', pd.IndexSlice[1, 'Colour',]
            ).applymap(
                lambda _: 'background-color: #90EE90', pd.IndexSlice[2, 'Colour',]
            ).applymap(
                lambda _: 'background-color: #FBACA8', pd.IndexSlice[3, 'Colour',]
            ).applymap(
                lambda _: 'background-color: #EDC9AF', pd.IndexSlice[4, 'Colour',]
            ).applymap(
                lambda _: 'background-color: #D291BC', pd.IndexSlice[5, 'Colour',]
            ).applymap(
                lambda _: 'background-color: #85E3FF', pd.IndexSlice[6, 'Colour',]
            ).set_table_attributes(
                'style="font-size: 10px"'
            ).hide_index().set_caption('Key')

    def as_dataframe(self, ciphertext=False, label='Deciphered plaintext'):
        """
        display the finished cipher in a dataframe
        """
        n = 26
        ciphertext = [str(i) for i in self] if not ciphertext else [i for i in ciphertext]
        df = pd.DataFrame(
            [ciphertext[i:i + n] for i in range(0, len(ciphertext), n)]
        )
        mask = df.applymap(lambda x: x is None)
        cols = df.columns[(mask).any()]
        for col in df[cols]:
            df.loc[mask[col], col] = ''
        df.columns = helpers.alphabet
        style =  df.style.hide_index().set_caption(
            label
        ).set_table_attributes(
            'style="font-size: 10px"'
        ).applymap(
            Highlighter(None, None).highlightr,
            subset=pd.IndexSlice[self._currentr, self._currentc]
        )

        for i in range(len(self)):
            if i == self._cindex:
                continue
            row = i // 26
            col = helpers.i2a((i % 26) + 1)
            properties_match = self[i].properties_table == self[self._cindex].properties_table
            conditions_match = self[i].condition_table == self[self._cindex].condition_table
            if properties_match and conditions_match:
                style = style.applymap(
                    Highlighter(None, None).highlights,
                    subset=pd.IndexSlice[row, col]
                )
            elif properties_match:
                style = style.applymap(
                    Highlighter(None, None).highlightl,
                    subset=pd.IndexSlice[row, col]
                )
            elif conditions_match:
                style = style.applymap(
                    Highlighter(None, None).highlightb,
                    subset=pd.IndexSlice[row, col]
                )
        return style

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
