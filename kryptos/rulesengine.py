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

        # I really do not like these next two rules. They seem **too** convoluted...
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
            character.position = 'tr'
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

            character.algorithm += {
                'tl': 2 if tl_direction and not five_minute else  0,
                'br': 0,
                'tr': 2 if character.index % 5 == 0 else 0,
                'bl': 0,
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
        for key in character.cipher.keys():
            character.cipher[key].mark_lacuna(character._intermediate)
        return character._intermediate

    @staticmethod
    def unpack(character, even_active, mixed_active, lacuna=False):
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
        character.table = not character.table if character.cindex % 2 != 0 else character.table

        if not character.mapped:
            character.table = not character.table if any(character.lacuna_active) \
                and (even_active and not mixed_active) \
                else character.table

        # ============================================================================
        # SECONDARY RULES
        # ============================================================================
        order_table_even = {
            'tl': 1 if lacuna and character.index % 2 == 0 \
                    else 1,
            'br': 2,
            'tr': 3 if lacuna and (character.index % 2) != 0 \
                    else 1,
            'bl': 2 if lacuna and (character.index % 2) != 0 \
                    else 1 if not lacuna and (
                        character.binary and not character.polarity
                    ) and (character.index % 2) != 0 \
                    else 1,
            False: 0,
        }[even_active]


        not_fifteen = (character.index % 5 == 0) and (character.index % 15 != 0)
        order_table_mixed = {
            'tl': 3 if character.binary and character.table and not character.polarity and even_active \
                else 0 if character.index % 2 == 0 \
                else 3 if character.binary and character.polarity \
                else 2,
            'br': 2,
            'tr': 2 if (character.table and not character.polarity)
                    else 0 if not lacuna \
                    else 1 if character.index % 5 == 0 \
                    else 3,
            'bl': 3 if character.table or not lacuna \
                    else 1 if character.binary and character.polarity \
                    else 2,
            False: 0,
        }[mixed_active]

        character.algorithm += sum([order_table_even, order_table_mixed]) % 4
        validate = even_active if not mixed_active else mixed_active

        if even_active and mixed_active:
            validate = even_active + mixed_active
            if validate in ['bltl',]:
                character.table = not character.table
            return {
                'tlbr': 'tl',
                'trbr': 'bl',
                'brtr': 'tl',
                'bltl': 'tr' if character.binary and character.polarity \
                        else 'bl',
            }[validate]

        # 5 minute rule
        if character.index % 2 != 0 and character.cindex % 5 == 0:
            validate = 'br' if even_active and not mixed_active else validate

        even = even_active and not mixed_active
        even_table = even and character.table
        mixed_table = not even and character.table

        return {
            'tl': 'bl' if character.index % 2 == 0 \
                    else 'br',
            'tr': 'bl',
            'bl': 'br' if (character.table and not character.mapped) \
                    else 'bl' if not character.polarity and character.binary \
                    else 'tl',
            'br': 'tr',
        }[
            validate
            if not character.mapped or not character.binary else character.position
        ]
