import random
cimport cards as cards
import cards as cards
from handscore import HandBuilder
from utility import MathUtils

class HandSimulator(object):
    """Given two hole cards & any number of table cards simulate the
    outcome of the hand a number of times to determine an approximate
    pot equity (percent of pot we can expect to win)
    """
    def __init__(self, hand, table_cards=[]):
        self.hand = [hand.high, hand.low]
        self.table_cards = table_cards
        self.deck = [c for c in cards.full_deck() \
                     if not c in self.table_cards and not c in self.hand]

    def best_hand(self):
        """Returns the best hand possible given the cards the simulator knows about"""
        if len(self.table_cards) >= 3:
            return HandBuilder(self.hand + self.table_cards).find_hand()
        else:
            return self.hand

    def simulate(self, iterations):
        """Repeatedly run the simulation, return the % pot equity"""
        wins = 0

        for i in range(0, iterations):
            wins += self.try_hand()

        return MathUtils.percentage(wins, iterations)

    def try_hand(self):
        # Deal out two opponent cards and 5 table cards
        cards = random.sample(self.deck, 7)
        opponent = cards[0:2]

        cards_needed = 5 - len(self.table_cards)
        common_cards = cards[2:(2+cards_needed)] + self.table_cards

        # Find the best hand for each set of hole cards
        _, our_score = HandBuilder(self.hand + common_cards).find_hand()
        _, their_score = HandBuilder(opponent + common_cards).find_hand()

        # return our equity: fraction of the pot we won
        if our_score > their_score:
            return 1
        elif our_score == their_score:
            return 0.5
        else:
            return 0