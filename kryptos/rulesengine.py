from . import helpers
from . import Square

class RulesEngine:
    @staticmethod
    def apply_rules(character):
        # ============================================================================
        # RULES
        # ----------------------------------------------------------------------------
        # The following block sets the rules for the cipher location starting with the
        # principle conditions for execution.
        #
        # Deciphering starts in the top left corner and moves around the table according
        # to the rules matched for that character.
        # ============================================================================
        character.table = (character.index % 2 != 0)
        character.table = not character.table if (character.cindex % 2) == 0 else character.table

        # I really do not like these next few rules. They seem **too** convoluted...
        character.table = not character.table if not character.table \
                and character.binary \
                and character.polarity \
                and all(character.cipher_active) \
                and not any(character.lacuna_active) \
            else character.table

        if any(character.cipher_active) and not any(character.lacuna_active):
            character.table = not character.table if character.lindex % 2 == 0 \
                    and character.lindex % 5 == 0 \
                    and not character.polarity \
                else character.table

        character.table = not character.table if all([
            not character.binary,
            not character.polarity,
            character.index  % 2  == 0,
            character.lindex % 5  == 0,
            character.lindex % 15 == 0,
            character.alphabet_even,
        ]) else character.table

        # this next rule is very specific to switch table
        # in a single instance when no other rule suffices
        character.table = not character.table if all([
            not character.binary,
            not character.polarity,
            not character.mapped,
            not any(character.cipher_active),
            not any(character.lacuna_active),
            not character.deciphered_lacuna,
            character.alphabet_even,
            character.upper_alphabet,
            character.all_off,
        ]) else character.table

        character.table = not character.table if all([
            character.table,
            character.binary,
            character.polarity,
            all([
                any(character.cipher_active),
                not all(character.cipher_active),
                not any(character.lacuna_active),
            ]),
            not character.alphabet_even,
            character.all_mod_2,
        ]) else character.table

        character.table = not character.table if all([
                not all(character.lacuna_active),
                not any(character.cipher_active),
            character.table,
            character.binary,
            character.polarity,
            all([
                any(character.lacuna_active),
                not all(character.lacuna_active),
                not any(character.cipher_active),
            ]),
            character.alphabet_even,
            not character.all_mod_2,
        ]) else character.table

        character.position = 'tl'
        # ------------------------------------------------------------
        # algorithm is used to select which deciphering
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
        character.algorithm = 1 if not character.table or (character.table and character.binary) else 0
        character.algorithm = 0 if character.mapped else character.algorithm
        character.algorithm += 2 if character.can_replace(character.character) and not character.mapped else 0
        character.algorithm += 1 if character.index % 15 == 0 else 0
        character.algorithm += 1 if character.cindex % 5 == 0 else 0

        """
        Condition 1. If we use the alternate character, change the nature of the table
        """
        if character.polarity and character.mapped:
            character.table = not character.table if character.index % 2 == 0 else character.table
            character.position = 'bl' if all([
                not character.alphabet_even,
                character.lindex %  2 != 0,
                character.lindex % 15 == 0,
            ]) else 'tl' if all ([
                character.table,
                not character.binary,
                character.polarity,
                character.index  %  2 == 0,
                character.lindex % 15 == 0,
                character.upper_alphabet,
            ]) else 'tr'
            character.table, character.position = (not character.table, 'tl') if character.binary else (character.table, character.position)

        """
        Condition 2. If the current polarity of the character is True, flip positions
        """
        if character.binary:
            character.position = {
                'tl': 'br',
                'br': 'tl',
                'tr': 'bl',
                'bl': 'tr',
            }[character.position]

        """
        Primary Rule 1. If not cipher character visible and not lacuna character visible
        """
        if not any(character.cipher_active) and not any(character.lacuna_active):
            # ------------------------------------------------------------
            # Sub rule 1 - Current characters Z Lacuna exists in either table
            # ------------------------------------------------------------
            c = (character.cindex + character.cindex) % 26
            l = (character.lindex + character.lindex) % 26
            pos = False
            if l in character.cipher[False].get():
                pos = character.cipher[False].get().index(l)
                if c in character.cipher[True].get():
                    pos = character.cipher[True].get().index(c)

            elif l in character.cipher[True].get():
                pos = character.cipher[True].get().index(l)
                if c in character.cipher[False].get():
                    pos = character.cipher[False].get().index(c)

            if pos:
                character.table = not character.table
                character.position = Square.ORDER[pos]

            if character.index % 15 == 0 and character.index % 2 == 0:
                character.position = 'bl'
            elif not character.binary and not character.polarity:
                if any([
                    all([
                        character.index      % 2  == 0,
                        not character.lindex % 5  == 0,
                        not character.lindex % 15 == 0
                    ]),
                    all([
                        character.index  % 5  == 0,
                        character.index  % 15 == 0,
                        character.cindex % 5  == 0,
                        character.cindex % 15 != 0,
                    ]),
                ]):
                    character.position = 'tl'
                elif all([
                    not character.table,
                    character.alphabet_even,
                    character.upper_alphabet,
                    character.all_off,
                ]):
                    character.position = 'br'
                elif any([
                    character.index % 15 == 0,
                    all([
                        character.all_off,
                        any([
                            not character.deciphered_lacuna,
                            character.alphabet_even
                        ]),
                        #character.cindex > 13,
                        character.upper_alphabet,
                    ]),
                    all([
                        not character.binary,
                        not character.polarity,
                        character.index  %  2 == 0,
                        character.lindex %  5 == 0,
                        character.lindex % 15 == 0,
                    ]),
                    all([
                        character.alphabet_even,
                        character.all_off,
                        character.cindex > 13,
                    ]),
                ]):
                    character.position = 'tr'
                elif all([
                    character.table,
                    not character.binary,
                    not character.polarity,
                    character.alphabet_even,
                ]):
                    character.position = 'bl'

            # ------------------------------------------------------------
            # Go back to top left if we're XOR and in the mixed character table
            # then set a new calculation if we're not mod 5 (inverse 5 minute rule)
            # ------------------------------------------------------------
            if not character.table and character.binary:
                character.position = 'tl'
                character.algorithm += 0 if character.cindex % 5 == 0 else 1
                character.algorithm += 1 if character.index % 2 != 0 and character.index % 5 == 0 else 0

            # ------------------------------------------------------------
            # Map current position on to deciphering algorithm index
            # ------------------------------------------------------------
            five_minute = character.index % 5 == 0 and character.table
            tl_direction = character.table and not character.binary and not character.polarity

            if character.polarity and not character.mapped:
                if character.can_replace(helpers.i2a(character.index % 26)):
                    character.table = not character.table
                    character.position = 'tl' if character.lindex % 5 == 0 else 'br'
                    character.algorithm += 3

            if all([
                not character.binary,
                not character.polarity,
                not character.mapped,
                character.alphabet_even,
                not character.all_mod_2,
                character.lindex % 5 == 0,
                character.lindex % 15 == 0,
                not character.upper_alphabet,
            ]):
                character.table = not character.table
                character.position = 'br'
            elif all([
                character.table,
                not character.binary,
                character.polarity,
                not character.mapped,
                not character.upper_alphabet,
                character.alphabet_even,
                any([
                    all([
                        not character.all_mod_2,
                        not character.all_mod_15,
                        all([
                            character.index % 5 == 0,
                            not character.cindex % 5 == 0,
                            not character.lindex % 5 == 0,
                        ]),
                    ]),
                    all([
                        not character.all_mod_5,
                        not character.all_mod_15,
                        all([
                            character.index % 2 == 0,
                            not character.cindex % 2 == 0,
                            not character.lindex % 2 == 0,
                        ]),
                    ]),
                ])
            ]):
                character.position = 'bl'

            character.algorithm += {
                'tl': 3 if any([
                        all([
                            character.index  % 5  == 0,
                            character.index  % 15 == 0,
                            character.cindex % 5  == 0,
                            character.cindex % 15 != 0,
                        ]),
                    ])
                    else 2 if any([
                        all([
                            tl_direction,
                            not five_minute,
                            character.index % 2 != 0,
                        ]),
                    ])
                    else 1 if any([
                        all([
                            tl_direction,
                            character.index % 2 == 0,
                        ]),
                        all([
                            not character.binary,
                            not character.mapped,
                            character.polarity,
                            character.index  % 2 == 0,
                            character.lindex % 5 == 0,
                        ]),
                    ])
                    else 0,
                'br': 2 if all([
                        character.upper_alphabet,
                        character.all_off,
                    ])
                    else 0,
                'tr': 3 if any([
                        character.index % 15 == 0,
                        all([
                            not character.table,
                            character.index % 2   == 0,
                            character.lindex % 5  == 0,
                            character.lindex % 15 == 0,
                        ]),
                    ])
                    else 2 if any([
                        all([
                            character.index % 5 == 0,
                            not tl_direction,
                        ]),
                        all([
                            character.table,
                            not character.binary,
                            not character.polarity,
                            character.all_off,
                            character.alphabet_even,
                        ]),
                        all([
                            not character.binary,
                            not character.polarity,
                            not character.mapped,
                            character.alphabet_even,
                            not character.all_mod_2,
                            character.lindex % 5 == 0,
                            character.lindex % 15 == 0,
                            not character.upper_alphabet,
                        ]),

                    ])
                    else 1 if all([
                        character.deciphered_lacuna,
                        not character.alphabet_even
                    ])
                    else 0,
                'bl': 1 if any([
                        all([
                            all([
                                character.index %  2 == 0,
                                character.index %  5 == 0,
                                character.index % 15 == 0,
                            ]),
                            all([
                                character.cindex %  2 != 0,
                                character.cindex %  5 != 0,
                                character.cindex % 15 != 0,
                            ]),
                            all([
                                character.lindex %  2 != 0,
                                character.lindex % 15 != 0,
                            ]),
                        ])
                    ])
                    else 2 if any([
                        all([
                            not character.all_mod_2,
                            all([
                                character.index  % 5 != 0,
                                character.cindex % 5 != 0,
                                character.lindex % 5 == 0,
                            ]),
                            all([
                                character.index  % 15 != 0,
                                character.cindex % 15 != 0,
                                character.lindex % 15 == 0,
                            ]),
                        ]),
                        all([
                            all([
                                character.index  % 2 == 0,
                                character.cindex % 2 != 0,
                                character.lindex % 2 != 0,
                            ]),
                            all([
                                character.index  % 5 != 0,
                                character.cindex % 5 != 0,
                                character.lindex % 5 != 0,
                            ]),
                        ]),
                    ])
                    else 0 if any([
                        character.all_off,
                        all([
                            not character.all_mod_2,
                            all([
                                character.index  % 5 == 0,
                                character.cindex % 5 != 0,
                                character.lindex % 5 != 0,
                            ]),
                            not character.all_mod_15,
                        ]),
                    ])
                    else 3,
                False: 0,
            }[character.position]
        elif any(character.cipher_active) and not any(character.lacuna_active):
            """
            Primary Rule 2. If cipher character is visible and lacuna character is not visible
            """
            character.position = RulesEngine.unpack(
                character,
                character.cipher[True].cipher_active,
                character.cipher[False].cipher_active,
            )
        elif any(character.lacuna_active) and not any(character.cipher_active):
            """
            Primary Rule 3. If lacuna character is visible and cipher character is not visible
            """
            character.position = RulesEngine.unpack(
                character,
                character.cipher[True].lacuna_active,
                character.cipher[False].lacuna_active,
                True
            )
        elif any(character.cipher_active) and any(character.lacuna_active):
            """
            Primary Rule 4. If cipher character is visible and lacuna character is not visible
            """
            a = RulesEngine.unpack(
                character,
                character.cipher[True].cipher_active,
                character.cipher[False].cipher_active,
            )
            b = RulesEngine.unpack(
                character,
                character.cipher[True].lacuna_active,
                character.cipher[False].lacuna_active,
                True
            )
            character.position = 'tl' if a == b else 'br'

        # ============================================================================
        # END RULES
        # ============================================================================
        character._intermediate = helpers.i2a(character.cipher[character.table].active(character.position))
        return character._intermediate

    @staticmethod
    def unpack(character, even_active, mixed_active, lacuna=False):
        """
        Used to determine the additional rules surrounding any combination
        of cipher and lacuna visibility in the tables.

        :param: string|bool even_active   if not False, represents the visibility of the cipher
                                          or lacuna character in the even numbered table
        :param: string|bool lacuna_active if not False, represents the visibility of the cipher
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
        character.table = not character.table if any([
            character.cindex % 2 != 0,
            all([
                character.binary,
                character.polarity,
                character.alphabet_even,
                character.upper_alphabet,
                character.index  % 2 != 0,
                character.cindex % 2 == 0,
                character.lindex % 2 == 0,
            ])
        ]) else character.table

        if not character.mapped:
            character.table = not character.table if any(character.lacuna_active) \
                and (even_active and not mixed_active) \
                else character.table

        even = even_active and not mixed_active
        even_table = even and character.table
        mixed_table = not even and character.table
        validate = even_active if not mixed_active else mixed_active

        if all([
            even_active,
            mixed_active,
            (str(even_active) + str(mixed_active)) in ['bltl',]
        ]):
            character.table = not character.table

        if character.index % 2 != 0 and character.cindex % 5 == 0:
            validate = 'br' if even_active and not mixed_active else validate

        if character.all_mod_2 and character.binary and character.cindex % 5 == 0:
            character.table = not character.table if not character.polarity else character.table

        value = {
            'tl': 'tl' if any([
                    all([
                        character.index  %  2 == 0,
                        character.index  %  5 == 0,
                        character.index  % 15 != 0,
                        character.lindex %  5 == 0
                    ]),
                ])
                else 'bl' if any([
                    character.index % 2 == 0,
                ])
                else 'br',
            'tr': 'bl' if not character.binary else 'tl',
            'tr': 'tl' if any([
                    all([
                        character.table,
                        not character.binary,
                        character.polarity,
                        character.alphabet_even,
                        character.index % 5 == 0,
                    ])
                ])
                else 'br' if all([
                    not character.table,
                    not character.binary,
                    not character.polarity,
                    character.all_off
                ])
                else 'bl' if not character.binary
                else 'tr',
            'bl': 'br' if any([
                        all([
                            character.table,
                            not character.mapped,
                            all([
                                not character.all_mod_2,
                                character.cindex % 5 != 0,
                                all([
                                    any([
                                        character.binary,
                                        character.polarity,
                                    ]),
                                ]),
                            ])
                        ])
                    ])
                    else 'tr' if any([
                        all([
                            character.binary,
                            not character.polarity,
                            character.all_mod_2,
                            character.cindex < 13, # This is very specific. Maybe too much so...
                            not character.alphabet_even,
                        ]),
                    ])
                    else 'bl' if any([
                        all([
                            character.binary,
                            not character.polarity,
                            any([
                                all([
                                    character.all_mod_2,
                                    character.cindex > 13,
                                ]),
                                all([
                                    character.index  % 2 != 0,
                                    character.cindex % 2 == 0,
                                    character.lindex % 2 == 0,
                                ]),
                            ])
                        ]),
                        all([
                            character.binary,
                            character.polarity,
                            character.index  % 2 != 0,
                            character.cindex % 2 == 0,
                            character.lindex % 2 == 0,
                        ]),
                    ])
                    else 'tl',
            'br': 'tr' if any([
                    all([
                        not character.binary,
                        lacuna
                    ]),
                    all([
                        character.binary,
                        not character.polarity,
                        any(character.lacuna_active),
                        character.cindex % 2 == 0,
                        character.lindex % 2 == 0,
                        character.cindex % 5 == 0,
                        not character.alphabet_even,
                    ]),
                ])
                else 'tl' if any([
                    all([
                        lacuna,
                        character.binary,
                        not character.polarity,
                        character.cindex % 2 == 0,
                        character.cindex % 5 == 0,
                    ])
                ])
                else 'bl',
        }[
            validate
            if not character.mapped or not character.binary else character.position
        ]

        if all([even_active, mixed_active]):
            validate = even_active + mixed_active
            if all([
                character.table,
                character.binary,
                character.polarity,
                character.mapped,
                character.all_mod_2,
            ]):
                character.algorithm += 1
            value = {
                'tlbr': 'tl',
                'trbr': 'bl',
                'brtr': 'tl',
                'bltl': 'tr' if any([
                        all([
                            character.upper_alphabet,
                            character.binary,
                            character.polarity
                        ]),
                        all([
                            character.table,
                            character.binary,
                            not any(character.lacuna_active)
                        ])
                    ])
                    else 'br' if any([
                        all([
                            character.binary,
                            character.polarity,
                            not character.alphabet_even,
                            not character.upper_alphabet,
                            character.all_mod_2,
                        ]),
                    ])
                    else 'bl',
            }[validate]

        # ============================================================================
        # SECONDARY RULES
        # ============================================================================
        order_table_even = {
            'tl': 1 if lacuna and character.index % 2 == 0 \
                    else 1,
            'br': 2,
            'tr': 3 if any([
                        all([
                            lacuna,
                            (character.index % 2) != 0,
                        ]),
                    ])
                    else 2 if any([
                        all([
                            character.binary,
                            character.polarity,
                            all([
                                any(character.cipher_active),
                                not all(character.cipher_active),
                            ]),
                            character.all_mod_2,
                            character.cindex % 5 == 0,
                        ]),
                        all([
                            character.binary,
                            not character.polarity,
                            character.all_mod_2,
                            character.cindex % 5 == 0,
                        ]),
                    ])
                    else 1,
            'bl':  3 if any([
                        all([
                            character.table,
                            character.binary,
                            not character.polarity,
                            not all(character.lacuna_active),
                            character.all_mod_2,
                        ]),
                        all([
                            character.table,
                            character.binary,
                            character.polarity,
                            character.alphabet_even,
                            character.cindex % 2 == 0,
                            character.cindex % 5 == 0,
                            character.lindex % 2 == 0,
                        ]),
                    ])
                    else 2 if any([
                        all([
                            character.binary,
                            not character.polarity,
                            all([
                                any(character.lacuna_active),
                                not all(character.lacuna_active),
                            ]),
                            all([
                                character.alphabet_even,
                                any([
                                    all([
                                        character.all_mod_2,
                                        character.cindex % 5 == 0,
                                    ]),
                                    all([
                                        character.index  % 2 != 0,
                                        character.cindex % 2 == 0,
                                        character.lindex % 2 == 0,
                                        character.cindex % 5 != 0,
                                    ]),
                                ])
                            ]),
                        ]),
                        all([
                            character.table,
                            character.binary,
                            character.polarity,
                            character.all_mod_2,
                            character.index % 5 == 0,
                        ]),
                        all([
                            character.table,
                            character.binary,
                            not character.polarity,
                            not character.alphabet_even,
                            character.index % 2 != 0,
                            character.cindex % 2 == 0,
                            character.lindex % 2 == 0,
                            character.cindex % 5 == 0,
                        ]),
                        all([
                            character.binary,
                            not character.polarity,
                            all([
                                any(character.lacuna_active),
                                not all(character.lacuna_active),
                                not any(character.cipher_active),
                            ]),
                            character.cindex <= 13,
                            not character.alphabet_even,
                        ]),
                        all([
                            character.binary,
                            character.polarity,
                            character.alphabet_even,
                            character.index  % 2 != 0,
                            character.cindex % 2 == 0,
                            character.lindex % 2 == 0,
                        ]),
                    ])
                    else 1 if any([
                        all([
                            character.binary,
                            not character.polarity,
                            any([
                                all([
                                    any(character.lacuna_active),
                                    not all(character.lacuna_active),
                                ]),
                                any(character.cipher_active),
                            ]),
                            character.index  % 2 != 0,
                            character.cindex % 2 == 0,
                            character.lindex % 2 == 0,
                        ]),
                        all([
                            character.binary,
                            all([
                                any([
                                    character.polarity,
                                    not all(character.lacuna_active),
                                ]),
                            ]),
                            character.all_mod_2,
                        ]),
                        all([
                            character.binary,
                            not character.polarity,
                            any([
                                all(character.cipher_active),
                                all(character.lacuna_active),
                            ]),
                            character.index  % 2 != 0,
                            character.cindex % 2 == 0,
                            character.lindex % 2 == 0,
                        ]),
                        all([
                            character.binary,
                            character.cindex % 2 == 0,
                            character.lindex % 2 == 0,
                            character.cindex % 5 == 0,
                        ]),
                    ])
                    else 0,
            False: 0,
        }[even_active]

        order_table_mixed = {
            'tl': 3 if any([
                    all([
                        character.table,
                        character.binary,
                        not character.polarity,
                        all(character.lacuna_active)
                    ]),
                    all([
                        character.binary,
                        character.polarity,
                        character.index % 2 != 0
                    ]),
                    all([
                        character.table,
                        character.binary,
                        not character.polarity,
                        not any(character.cipher_active),
                        all(character.lacuna_active),
                        not character.all_mod_2,
                    ]),
                    all([
                        character.index  %  2 == 0,
                        character.index  %  5 == 0,
                        character.index  % 15 != 0,
                        character.lindex %  5 == 0
                    ]),
                    all([
                        character.table,
                        not character.binary,
                        character.polarity,
                        all([
                            any(character.cipher_active),
                            not all(character.cipher_active),
                        ]),
                        character.index % 2 == 0,
                        character.lindex % 5 == 0,
                        character.upper_alphabet,
                    ])
                ])
                else 2 if any([
                    all([
                        character.binary,
                        not character.polarity,
                        character.index  % 2 == 0,
                        character.lindex % 5 == 0,
                    ]),
                    all([
                        not character.table,
                        character.binary,
                        not character.polarity,
                        character.cindex % 2 == 0,
                        character.lindex % 2 == 0,
                        not all(character.lacuna_active),
                    ])
                ])
                else 1 if all([
                    character.table,
                    not character.binary,
                    character.polarity,
                    any(character.cipher_active),
                    character.index  % 2 == 0,
                    character.lindex % 5 == 0,
                ])
                else 0,
            'br': 2,
            'tr': 3 if any([
                    all([
                        not character.table,
                        not character.binary,
                        not character.polarity,
                        any([
                            character.index  %  5 != 0,
                            character.cindex % 15 == 0,
                        ]),
                    ]),
                    all([
                        character.table,
                        not character.binary,
                        character.polarity,
                    ]),
                ])
                else 2 if any([
                    all([
                        character.table,
                        not character.polarity
                    ]),
                    all([
                        not character.binary,
                        not character.polarity,
                        any(character.lacuna_active),
                        character.cindex % 2 != 0,
                        character.cindex % 15 == 0
                    ]),
                ])
                else 1 if any([
                    all([character.index % 5 == 0,]),
                ])
                else 0,
            'bl': 3 if any([
                        character.table,
                        not lacuna,
                    ])
                    else 1 if any([
                        all([
                            character.binary,
                            character.polarity
                        ]),
                        all([
                            character.table,
                            character.polarity
                        ])
                    ])
                    else 1,
            False: 0,
        }[mixed_active]

        character.algorithm += sum([order_table_even, order_table_mixed]) % 4
        return value
