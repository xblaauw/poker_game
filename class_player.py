from poker import Card, Hand, Range, Rank, Combo
import random

class Player:
    hand = []
    stack = 0
    name = ''
    bank = 0
    folded = False

    def __init__(self, name):
        self.name = name

    def evaluate_options(self, options, table):
        action = random.choice(options)
        return action

    def get_raise_amount(self, table):
        return 2

    def get_hand(self):
        if self.hand[0].rank == self.hand[1].rank:
            suited = ''
        elif self.hand[0].suit == self.hand[1].suit:
            suited = 's'
        else:
            suited = 'o'
        ranks = str(self.hand[0].rank) + str(self.hand[1].rank)
        return Hand(ranks+suited)
