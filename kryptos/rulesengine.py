from . import helpers
from . import Square
from time import sleep

class RulesEngine:
    alphabet = None
    @staticmethod
    def apply_rules(character):
        if not RulesEngine.alphabet:
            RulesEngine._create_alphabet()
        return character.intermediate

    def _create_alphabet():
        RulesEngine.alphabet = {}
        for character in helpers.alphabet:
            RulesEngine.alphabet[character] = 0
