import pandas as pd
from . import helpers, Square

class Character(object):
    """
    The outer core class of the cipher

    If Helpers represents the core of the cipher, this is its counterpart

    The Character class takes a given input character and associated index, then maps it
    to one of 8 possible grid references, then from there chooses a single calculation
    method to turn that grid square into a potential plaintext character.

    It does this by following a complex set of rules defined in the `decipher` and `unpack_active`
    methods

    The `decipher` method defines 4 primary rules:

    - neither cipher or lacuna visible
    - cipher visible
    - lacuna visible
    - both visible

    Additionally a set of properties are available which adjust the directionality of the current position

    If neither cipher or lacuna are visible in the grids plotted to either table, the decipher method
    then defines an additional set of rules for choosing the correct cipher algorithm.

    If the inverse is true and one or both of the cipher/lacuna is visible, we then use the `unpack_active` method

    The `unpack_active` method takes the current square only if it has a ciphertext character
    and/or a lacuna text character visible in the same grid, then attempts to map the ciphertext
    character onto one of 4 possible deciphering algorithms.

    They both work on similar principles. First choosing the grid square, then applying rules to
    the value found in that square along with any boolean values generated from:

    - The polarity of the current character (is it an odd or even character)
    - an alternating binary flip-switch based on whether that cell was previously active.
    - Mod 2, 5, 15 on the current index
    """
    cipher = {
        True: None,
        False: None,
    }

    index         = 0
    character     = ''
    lacuna        = ''
    deciphered    = ''
    ciphertext    = ''
    binary        = None
    polarity      = False
    cipher_active = False
    lacuna_active = False
    map_cipher    = {}
    _algorithm    = 0
    _table        = False
    _position     = None
    _intermediate = None
    _char_index   = 0
    _lacuna_index = 0
    deciphered_lacuna = {}

    def __init__(self, character, index, polarity, ciphertext):
        self.index         = index
        self.character     = character.upper()
        self.lacuna        = helpers.distancefrom(self.character, 'Z')
        self.polarity      = polarity
        self._char_index   = helpers.a2i(self.character)
        self._lacuna_index = helpers.a2i(self.lacuna)
        self.binary        = self._char_index % 2 == 0
        self.ciphertext    = ciphertext

        self._intermediate = self.character

        # ------------------------------------------------------------
        # Create a Square object for each character in the cipher
        # ------------------------------------------------------------
        self.cipher = {
            key: Square(self.character, key, self.polarity, ciphertext)
            for key in self.cipher.keys()
        }

        # ------------------------------------------------------------
        # We set the current polarity against the cipher character
        # polarity, then build the tables and move to find the
        # intermediate character.
        # ------------------------------------------------------------
        _ = [table.plot() for _, table in self.cipher.items()]
        _ = self.decipher

    def __str__(self):
        return self.final[1]

    def __repr__(self):
        return str(self)

    @property
    def cindex(self):
        return self._char_index

    @property
    def lindex(self):
        return self._lacuna_index

    @property
    def table(self):
        return self._table

    @table.setter
    def table(self, table):
        self._table = table

    @property
    def algorithm(self):
        return self._algorithm

    @algorithm.setter
    def algorithm(self, which):
        self._algorithm = which

    @property
    def totals(self):
        a = sum(self.cipher[True].get())
        b = sum(self.cipher[False].get())
        return (
            a, b,
            (a + b),
            (a + b) % 26,
            (a + b) % 60,
            ((a + b) % 60) % 26,
        )

    @property
    def mapped(self):
        return all([self.cipher[True].mapped, self.cipher[False].mapped])

    def can_replace(self, what):
        return what in self.cipher[True].table.keys['replace'].keys()

    @property
    def properties_table(self):
        """
        Return the properties of the current object as a pandas DataFrame
        """
        return {
            'table'             : self.table,
            'binary'            : self.binary,
            'polarity'          : self.polarity,
            'mapped'            : self.mapped,
            'cipher_active'     : self.cipher_active,
            'lacuna_active'     : self.lacuna_active,
        }

    @property
    def properties_frame(self):
        return pd.DataFrame(list(self.properties_table.items()), columns=['Property', 'Value'])

    @property
    def condition_table(self):
        return [
            [
                (self.index         % 2 == 0),
                (self._char_index   % 2 == 0),
                (self._lacuna_index % 2 == 0),
            ],
            [
                (self.index         % 5 == 0),
                (self._char_index   % 5 == 0),
                (self._lacuna_index % 5 == 0),
            ],
            [
                (self.index         % 15 == 0),
                (self._char_index   % 15 == 0),
                (self._lacuna_index % 15 == 0),
            ],
        ]

    def all_positions_table(self, character):
        return [[
            self.transcribe(0, character),
            self.transcribe(1, character),
        ],[
            self.transcribe(3, character),
            self.transcribe(2, character),
        ]]

    def all_positions(self, character=None):
        """
        Get a dataframe containing all characters reachable from a given reference

        :param: char character
        :return: pandas.DataFrame

        If character is None, we use the current decipher character
        """
        if not character:
            character = self.decipher
        return pd.DataFrame(self.all_positions_table(character))

    def all_positions_as_set(self):
        tables = [
            self.all_positions_table(helpers.i2a(item))
            for item in self.cipher[True].get() + self.cipher[False].get()
        ]
        tables = [ item for sublist in tables for item in sublist]
        tables = [ item for sublist in tables for item in sublist]
        return sorted(set(tables))

    def all_positionsi_missing_as_set(self):
        tables = [
            self.all_positions_table(helpers.i2a(item))
            for item in self.cipher[True].get() + self.cipher[False].get()
        ]
        tables = [ item for sublist in tables for item in sublist]
        tables = [ item for sublist in tables for item in sublist]
        return set(helpers.alphabet) - sorted(set(tables))

    @property
    def condition_frame(self):
        df = pd.DataFrame(self.condition_table, columns=['index', 'cipher', 'lacuna',])
        df.index   = ['% 2', '% 5', '% 15']
        return df

    @property
    def columns(self):
        columns = list(self.properties_table['Property'])
        for i in ['index', 'cipher', 'lacuna']:
            for j in ['% 2', '% 5', '% 15']:
                x = '{} {}'.format(i[0].upper(), j)
                if x not in columns:
                    columns.append(x)
        return columns

    @property
    def cipher_active(self):
        return (
            self.cipher[True].cipher_active,
            self.cipher[False].cipher_active
        )

    @property
    def lacuna_active(self):
        return (
            self.cipher[True].lacuna_active,
            self.cipher[False].lacuna_active
        )

    @property
    def intermediate(self):
        return self._intermediate

    @property
    def position(self):
        return self._position

    @property
    def alphabet_even(self):
        return ((self.index // 26) + 1) % 2 == 0

    @property
    def upper_alphabet(self):
        return (self.index % 26 if self.index % 26 != 0 else 26) > 13

    @position.setter
    def position(self, where):
        self._position = where
        self.cipher[not self.table].clear_active()
        self._intermediate = helpers.i2a(
            self.cipher[
                self.table
            ].active(where)
        )
        self.deciphered_lacuna = {}
        for table in self.cipher.keys():
            value = helpers.distancefrom(self._intermediate, 'Z')
            if self.cipher[table].contains(value):
                self.deciphered_lacuna = {
                    'position': self.cipher[table].position(value),
                    'value': value,
                    'table': table,
                }
                break

    @property
    def decipher(self):
        """
        Main decipher method
        """
        if not self._intermediate:
            self._intermediate = helpers.rulesengine.apply_rules(self)
        return self._intermediate

    @property
    def final(self):
        self.algorithm = self.algorithm % 4
        if self.deciphered_lacuna:
            self.cipher[
                self.deciphered_lacuna['table']
            ].mark_lacuna(
                self.deciphered_lacuna['position']
            )
        return (
            self.algorithm,
            self.transcribe(self.algorithm, self.decipher)
        )

    def transcribe(self, position, character):
        """
        For a given table index, translate the position to the one directly between ciphertext and plaintext

        :param int: position

        :return: character

        Given ciphers as:

               QQPRNGKSSNYPVTTMZFPK     IIJHLSOGGLAJDFFMZTJO
            ------------------------------------------------
            1. DCBVPGCUTVWBVCXWNYQS  2. VWXDJSWEFDCXDWBCLAIG
            3. UTRNDNNNMJVRRWRJNEGD  4. EFHLVLLLMPDHHCHPLUSV

        If the deciphered character is in position 1, we add this to the cipher character to obtain cipher 3
        If cipher character is in cipher 2, we first subtract this from Z to obtain cipher 1, then add
        If cipher character is in cipher 3, we do nothing
        If cipher character is in cipher 4, we subtract this from Z.

        Ciphers are listed in the order 3, 1, 4, 2
        """
        return helpers.distancefrom(
            self.character,[
                lambda x, _: x,
                lambda x, c: helpers.i2a(
                    (helpers.a2i(c) + helpers.a2i(x)) % 26
                ),
                lambda x, _: helpers.distancefrom(x, 'Z'),
                lambda x, c: helpers.i2a(
                    (helpers.a2i(c) + helpers.a2i(helpers.distancefrom(x, 'Z'))) % 26
                ),
            ][position](character, self.character)
        )

    @property
    def current(self):
        return self.cipher[self.table].get()[
            Square.ORDER.index(self.position)
        ]

    @property
    def all_mod_2(self):
        return all([
            self.index % 2 == 0,
            self.cindex % 2 == 0,
            self.lindex % 2 == 0,
        ])

    @property
    def all_mod_5(self):
        return all([
            self.index  % 5 == 0,
            self.cindex % 5 == 0,
            self.lindex % 5 == 0,
        ])
    @property
    def all_mod_15(self):
        return all([
            self.index  % 15 == 0,
            self.cindex % 15 == 0,
            self.lindex % 15 == 0,
        ])

    @property
    def no_mod_2(self):
        return all([
            self.index  % 2 != 0,
            self.cindex % 2 != 0,
            self.lindex % 2 != 0,
        ])

    @property
    def no_mod_5(self):
        return all([
            self.index  % 5 != 0,
            self.cindex % 5 != 0,
            self.lindex % 5 != 0,
        ])

    @property
    def no_mod_15(self):
        return all([
            self.index  % 15 != 0,
            self.cindex % 15 != 0,
            self.lindex % 15 != 0,
        ])

    @property
    def all_off(self):
        return all([self.no_mod_2, self.no_mod_5, self.no_mod_15])

    @property
    def all_on(self):
        return all([self.all_mod_2, self.all_mod_5, self.all_mod_15])

