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

    index              = 0
    character          = ''
    lacuna             = ''
    deciphered         = ''
    table              = None
    xor                = None
    use_alt            = False
    cipher_active      = False
    lacuna_active      = False
    map_cipher         = {}
    _position          = None
    _intermediate      = None
    _calculation_index = 0
    _char_index        = 0
    _lacuna_index      = 0

    def __init__(self, character, index, use_alt, ciphertext):
        self.index     = index
        self.character = character.upper()
        self.lacuna    = helpers.distancefrom(self.character, 'Z')
        self.use_alt   = use_alt

        self._char_index   = helpers.a2i(self.character)
        self._lacuna_index = helpers.a2i(self.lacuna)

        # ------------------------------------------------------------
        # Create a Square object for each character in the cipher
        # ------------------------------------------------------------
        self.cipher = {
            key: Square(self.character, key, self.use_alt, ciphertext)
            for key in self.cipher.keys()
        }

        # ------------------------------------------------------------
        # We set the current polarity against the cipher character
        # polarity, then build the tables and move to find the
        # intermediate character.
        # ------------------------------------------------------------
        self.xor = self._char_index % 2 == 0
        _ = [table.plot() for _, table in self.cipher.items()]
        _ = self.decipher

    def __str__(self):
        return self.final[1]

    def __repr__(self):
        return str(self)

    @property
    def algorithm(self):
        return self._calculation_index

    @algorithm.setter
    def algorithm(self, which):
        self._calculation_index = which

    @property
    def final(self):
        self._calculation_index = self._calculation_index % 4
        for key in self.cipher.keys():
            self.cipher[key].mark_lacuna(self.intermediate)
        return (
            self._calculation_index,
            self.transcribe(self._calculation_index, self.decipher)
        )

    @property
    def uses_alt(self):
        return all([self.cipher[True].alt_active, self.cipher[False].alt_active])

    def can_replace(self, what):
        return what in self.cipher[True].table.keys['replace'].keys()

    @property
    def properties_table(self):
        """
        Return the properties of the current object as a pandas DataFrame
        """
        table = {
            'table'         : self.table,
            'xor'           : self.xor,
            'position'      : self.position,
            'use_alt'       : self.use_alt,
            'uses_alt'      : self.uses_alt,
            'cipher_active' : self.cipher_active,
            'lacuna_active' : self.lacuna_active,
        }
        return pd.DataFrame(list(table.items()), columns=['Property', 'Value'])

    @property
    def condition_table(self):
        df = pd.DataFrame([
            [
                (self.index % 2) == 0, (self._char_index % 2 == 0), (self._lacuna_index % 2 == 0),
            ],
            [
                (self.index % 5) == 0, (self._char_index % 5 == 0), (self._lacuna_index % 5 == 0),
            ],
            [
                (self.index % 15) == 0, (self._char_index % 15 == 0), (self._lacuna_index % 15 == 0),
            ],
        ])
        df.columns = ['index', 'cipher', 'lacuna']
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
    def rule(self):
        rule = [str(a) for a in list(self.properties_table['Value'])]
        for i in ['index', 'cipher', 'lacuna']:
            for j in ['% 2', '% 5', '% 15']:
                rule.append(str(self.condition_table[i][j]))
        return pd.DataFrame([rule], columns=self.columns).drop('position', axis=1)

    @property
    def cipher_active(self):
        table = (
            self.cipher[True].cipher_active,
            self.cipher[False].cipher_active
        )
        return table if any(table) else False

    @property
    def lacuna_active(self):
        table = (
            self.cipher[True].lacuna_active,
            self.cipher[False].lacuna_active
        )
        return table if any(table) else False

    @property
    def intermediate(self):
        return self._intermediate

    @property
    def position(self):
        return self._position

    @position.setter
    def position(self, where):
        self._position = where
        self.cipher[not self.table].clear_active()
        self._intermediate = helpers.i2a(
            self.cipher[
                self.table
            ].active(where)
        )

    @property
    def decipher(self):
        """
        Main decipher method
        """
        if not self._intermediate:
            # ============================================================================
            # RULES
            # ----------------------------------------------------------------------------
            # The following block sets the rules for the cipher location starting with the
            # principle conditions for execution.
            #
            # Deciphering starts in the top left corner and moves around the table according
            # to the rules matched for that character.
            # ============================================================================
            self.table = (self.index % 2 != 0)
            self.position = 'tl'
            # ------------------------------------------------------------
            # _calculation_index is used to select which deciphering
            #                    algorithm to choose from 4 possible
            #                    options.
            #
            # The order of the calculation index is fixed as this maps
            # directly to a list of  deciphering algorithms below.
            #
            # The order is as follows:
            #   - 0: Nothing
            #   - 1: (c + x) % 26
            #   - 2: distancefrom(x, 'Z')
            #   - 3: c + distancefrom(x, 'Z') % 26
            # ------------------------------------------------------------
            self._calculation_index = 1 if not self.table or (self.table and self.xor) else 0
            self._calculation_index = 0 if self.uses_alt else self._calculation_index
            self._calculation_index += 2 if self.can_replace(self.character) and not self.uses_alt else 0
            self._calculation_index += 1 if self.index % 15 == 0 else 0
            self._calculation_index += 1 if self._char_index % 5 == 0 else 0

            self.table = not self.table if (self._char_index % 2) == 0 else self.table

            """
            Condition 1. If we use the alternate character, change the nature of the table
            """
            if self.use_alt and self.uses_alt:
                self.table = not self.table if self.index % 2 == 0 else self.table
                self.position = 'tr'
                self.table, self.position = (not self.table, 'tl') if self.xor else (self.table, self.position)

            """
            Condition 2. If the current polarity of the character is True, flip positions
            """
            if self.xor:
                self.position = {
                    'tl': 'br',
                    'br': 'tl',
                    'tr': 'bl',
                    'bl': 'tr',
                }[self.position]

            """
            Primary Rule 1. If not cipher character visible and not lacuna character visible
            """
            if not self.cipher_active and not self.lacuna_active:
                # ------------------------------------------------------------
                # Sub rule 1 - Current characters Z Lacuna exists in either table
                # ------------------------------------------------------------
                c = (self._char_index + self._char_index) % 26
                l = (self._lacuna_index + self._lacuna_index) % 26
                pos = False
                if l in self.cipher[False].get():
                    pos = self.cipher[False].get().index(l)
                    if c in self.cipher[True].get():
                        pos = self.cipher[True].get().index(c)

                elif l in self.cipher[True].get():
                    pos = self.cipher[True].get().index(l)
                    if c in self.cipher[False].get():
                        pos = self.cipher[False].get().index(c)

                if pos:
                    self.table = not self.table
                    self.position = Square.ORDER[pos]

                # ------------------------------------------------------------
                # Go back to top left if we're XOR and in the mixed character table
                # then set a new calculation if we're not mod 5 (inverse 5 minute rule)
                # ------------------------------------------------------------
                if not self.table and self.xor:
                    self.position = 'tl'
                    self._calculation_index += 0 if self._char_index % 5 == 0 else 1

                # ------------------------------------------------------------
                # Map current position on to deciphering algorithm index
                # ------------------------------------------------------------
                five_minute = self.index % 5 == 0 and self.table
                tl_direction = self.table and not self.xor and not self.use_alt

                if self.use_alt and not self.uses_alt:
                    if self.can_replace(helpers.i2a(self.index % 26)):
                        self.table = not self.table
                        self._calculation_index += 3

                self._calculation_index += {
                    'tl': 2 if tl_direction and not five_minute else 0,
                    'br': 0 if self.table else 0,
                    'tr': 0 if self.table else 0,
                    'bl': 0 if self.table else 0,
                    False: 0,
                }[self.position]
            elif self.cipher_active and not self.lacuna_active:
                """
                Primary Rule 2. If cipher character is visible and lacuna character is not visible
                """
                self.position = self.unpack_active(
                    self.cipher[True].cipher_active,
                    self.cipher[False].cipher_active,
                )
            elif self.lacuna_active and not self.cipher_active:
                """
                Primary Rule 3. If lacuna character is visible and cipher character is not visible
                """
                self.position = self.unpack_active(
                    self.cipher[True].lacuna_active,
                    self.cipher[False].lacuna_active,
                    True
                )
            elif self.cipher_active and self.lacuna_active:
                """
                Primary Rule 4. If cipher character is visible and lacuna character is not visible
                """
                a = self.unpack_active(
                    self.cipher[True].cipher_active,
                    self.cipher[False].cipher_active,
                )
                b = self.unpack_active(
                    self.cipher[True].lacuna_active,
                    self.cipher[False].lacuna_active,
                    True
                )
                self.position = 'tl' if a == b else 'br'

            # ============================================================================
            # END RULES
            # ============================================================================
            self._intermediate = helpers.i2a(self.cipher[self.table].active(self.position))
            for key in self.cipher.keys():
                self.cipher[key].mark_lacuna(self._intermediate)
        return self._intermediate

    def unpack_active(self, even_active, mixed_active, lacuna=False):
        """
        Used to determine the additional rules surrounding any combination
        of cipher and lacuna visibility in the tables.

        :param: string|bool even_active   if not False, represents the visibility of the cipher
                                          or lacuna character in the even numbered table
        :param: string|bool lacuna:active if not False, represents the visibility of the cipher
                                          or lacuna character in the mixed polarity table

        :return: string

        The presence of one or both of these characters can drastically alter the result of the
        final cipher.

        This will return one of

        - `tl` Top left
        - `tr` Top right
        - `br` Bottom right
        - `bl` Bottom left
        """
        self.table = not self.table if self._char_index % 2 != 0 else self.table

        if not self.uses_alt:
            self.table = not self.table if self.lacuna_active \
                and (even_active and not mixed_active) \
                else self.table

        # ============================================================================
        # SECONDARY RULES
        # ============================================================================
        order_table_even = {
            'tl': 0 if lacuna and self.index % 2 == 0 else 1,
            'br': 2,
            'tr': 3 if lacuna and (self.index % 2) != 0 else 1,
            'bl': 2 if lacuna and (self.index % 2) != 0 \
                else 1 if not lacuna and (self.xor and not self.use_alt) and (self.index % 2) != 0 \
                else 1,
            False: 0,
        }[even_active]

        order_table_mixed = {
            'tl': 3 if self.xor and self.table and not self.use_alt and even_active \
                else 0 if self.index % 2 == 0 \
                else 3 if self.xor and self.use_alt else 2,
            'br': 2,
            'tr': 2 if self.table and not self.use_alt  else \
                0 if not lacuna else \
                1 if self.index % 5 == 0 else 3,
            'bl': 3 if self.table or not lacuna else 1 if self.xor and self.use_alt else 2,
            False: 0,
        }[mixed_active]

        self._calculation_index += sum([order_table_even, order_table_mixed]) % 4
        validate = even_active if not mixed_active else mixed_active

        if even_active and mixed_active:
            validate = even_active + mixed_active
            if validate in ['bltl',]:
                self.table = not self.table
            return {
                'tlbr': 'tl',
                'trbr': 'bl',
                'brtr': 'tl',
                'bltl': 'tr' if self.xor and self.use_alt else 'bl',
            }[validate]

        # 5 minute rule
        if self.index % 2 != 0 and self._char_index % 5 == 0:
            validate = 'br' if even_active and not mixed_active else validate

        even = even_active and not mixed_active
        even_table = even and self.table
        mixed_table = not even and self.table

        if self.index == 14:
            print(validate)

        return {
            'tl': 'bl' if self.index % 2 == 0 else 'br',
            'tr': 'bl',
            'bl': 'br' if (self.table and not self.uses_alt) else \
                'bl' if not self.use_alt and self.xor else 'tl',
            'br': 'tr',
        }[
            validate
            if not self.uses_alt or not self.xor else self.position
        ]

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

    def all_positions(self, character=None):
        """
        Get a dataframe containing all characters reachable from a given reference

        :param: char character
        :return: pandas.DataFrame

        If character is None, we use the current decipher character
        """
        if not character:
            character = self.decipher
        return pd.DataFrame(
            [[
                self.transcribe(0, character),
                self.transcribe(1, character),
            ],[
                self.transcribe(3, character),
                self.transcribe(2, character),
            ]]
        )
