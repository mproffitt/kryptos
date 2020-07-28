from . import helpers
from . import Square
from time import sleep

class RulesEngine:
    alphabet = None
    @staticmethod
    def apply_rules(character):
        if not RulesEngine.alphabet:
            RulesEngine._create_alphabet()
        character.table = character.binary ^ character.polarity
        character.position = Square.ORDER[
            RulesEngine.alphabet[
                helpers.i2a(character.index + helpers.a2i(character.character)) % 26
                if helpers.i2a(character.index + helpers.a2i(character.character)) % 26 != 0 else 26
            ] % 4
        ]
        RulesEngine.alphabet[character.character] += 1
        character.algorithm = (character.cindex + RulesEngine.alphabet[character.character]) % 4
        return character.intermediate

    def _create_alphabet():
        RulesEngine.alphabet = {}
        for character in helpers.alphabet:
            RulesEngine.alphabet[character] = 0
