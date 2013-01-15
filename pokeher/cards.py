import functools
import itertools
from wiring import Callable

@functools.total_ordering
class Suit(object):
    SUITS = ["Clubs", "Diamonds", "Hearts", "Spades"]

    def __init__(self, suit):
        assert suit >= 0 and suit < len(self.SUITS)
        self.suit = suit

    def __repr__(self):
        return self.SUITS[self.suit]

    def __eq__(self, other):
        if isinstance(other, Suit):
            return self.suit == other.suit
        return NotImplemented

    def __lt__(self, other):
        return self.suit < other.suit

@functools.total_ordering
class Card(object):
    """Card value"""
    FACES = [None,None] + range(2, 11) + ["J", "Q", "K", "A"]

    def __init__(self, value, suit):
        assert value > 1
        assert value < len(self.FACES)
        assert isinstance(suit, Suit)

        self.value = value
        self.suit = suit

    def is_pair(self, other):
        return self.value == other.value

    def is_suited(self, other):
        return self.suit == other.suit

    def score_value(self):
        if self.value < 10:
            return .01 * self.value
        else:
            return 0.1 * self.value

    def __repr__(self):
        return '{value}-{suit}'.format(value=self.FACES[self.value], suit=str(self.suit))

    def __eq__(self, other):
        if isinstance(other, Card):
            return self.value == other.value and self.suit == other.suit
        return NotImplemented

    def __lt__(self, other):
        """Implements compare for Cards. Check value, then suit"""
        return ((self.value, self.suit) <
                (other.value, other.suit))

class Hand(object):
    """Player's hand of cards"""
    def __init__(self, card1, card2):
        if card1.value > card2.value:
            self.high = card1
            self.low = card2
        else:
            self.high = card2
            self.low = card1
        self._score = HandBuilder.NO_SCORE

    def score(self):
        """Returns the score, see HandBuilder"""
        if self._score == HandBuilder.NO_SCORE:
            return None
        return self._score

    def set_score(self, score):
        if score and score > HandBuilder.NO_SCORE:
            self._score = score

    def is_pair(self):
        """Returns true if hand is a pair, false otherwise"""
        return self.high.value == self.low.value

    def is_suited(self):
        """Returns true if other and self are the same suit, false otherwise"""
        return self.high.suit == self.low.suit

    def card_gap(self):
        """Returns the gap between high & low"""
        return (self.high.value - self.low.value) - 1

    def is_connected(self):
        """Returns whether the hand is connected"""
        return self.card_gap() == 0

class HandBuilder(object):
    """Makes the best hand from a given set of cards, scores hands
    """
    NO_SCORE = -1 # when we haven't calculated the score yet
    HIGH_CARD = 0
    PAIR = 1
    TWO_PAIR = 2
    TRIPS = 3
    STRAIGHT = 4
    FLUSH = 5
    FULL_HOUSE = 6
    QUADS = 7
    STRAIGHT_FLUSH = 8

    HAND_LENGTH = 5

    def __init__(self, cards):
        self.cards = cards

    def find_hand(self):
        """Returns the best hand of length HAND_LENGTH"""
        if not self.cards or len(self.cards) < self.HAND_LENGTH:
            return None
        if len(self.cards) == self.HAND_LENGTH:
            return self.cards

        self.__sort_hand()
        best_hand_score = self.NO_SCORE
        best_hand = None
        for hand in itertools.combinations(self.cards, self.HAND_LENGTH):
            score = HandBuilder(hand).__score_hand()

            if score > best_hand_score:
                print "{hand} is new best with {score}".format(hand=hand, score=score)
                best_hand_score = score
                best_hand = hand
        return best_hand

    def score_hand(self):
        """Returns the score of a 5-card hand"""
        # Drop invalid hands
        if not self.cards or len(self.cards) != self.HAND_LENGTH:
            return self.NO_SCORE
        self.__sort_hand()
        return self.__score_hand()

    def __score_hand(self):
        """Internal verson of score_hand, works on tuples and lists"""
        score = self.NO_SCORE

        # Do we have a flush?
        flush_suit = self.select_flush_suit()
        if flush_suit is not None:
            # Add the values of all the cards to distinguish between flushes
            score = self.FLUSH + self.__score_flush()

        # Is there a straight?
        if self.is_straight():
            if score == self.FLUSH:
                score = self.STRAIGHT_FLUSH
            else:
                score = self.STRAIGHT
            # Add the high card to distinguish between multiple straights
            score += self.__score_high_card()

        # At this point, return since we can't have any pairs
        # at the same time as a straight or flush
        if score > self.NO_SCORE:
            return score

        pairs, trips, quads = self.find_pairs_trips_quads()

        # Go from least to most valuable hands
        score = self.HIGH_CARD + self.__score_high_card()

        if pairs:
            score = self.PAIR + self.__score_pairs(pairs)
        if len(pairs) > 1:
            score = self.TWO_PAIR + self.__score_pairs(pairs)
        if trips:
            score = self.TRIPS + self.__score_pairs(trips)
        if trips and pairs:
            score = self.FULL_HOUSE + self.__score_full_house(trips, pairs)
        if quads:
            score = self.QUADS + self.__score_pairs(pairs)

        return score

    def find_pairs_trips_quads(self):
        """Finds pairs and trips, returns a list of pairs & a list of trips"""
        pairs = []
        trips = []
        quads = []
        seen = [None,None] + [0]*13 # card values run 2-15 instead of 0-13

        for card in self.cards:
            seen[card.value] += 1

        for i, val in enumerate(seen):
            if val == 2:
                pairs.append(i)
            elif val == 3:
                trips.append(i)
            elif val == 4:
                quads.append(i)

        return (pairs, trips, quads)

    def is_straight(self):
        """returns True if this hand is a straight, false otherwise"""
        last_card = None
        for card in self.cards:
            if last_card:
                gap = self.__gap(last_card, card)
                if gap != 1:
                    return False
            last_card = card
        return True

    def __sort_hand(self):
        """Sorts a hand, high values first"""
        sort_key = lambda card: (card.value, card.suit.suit)
        self.cards.sort(key=sort_key,reverse=True)

    def __gap(self, card1, card2):
        return card1.value - card2.value

    def select_flush_suit(self):
        """Returns the suit that has 5+ cards, or None otherwise"""
        if not self.cards:
            return None

        counts = {}
        for i in range(0, 4):
            counts[i] = 0

        for card in self.cards:
            value = card.suit.suit
            counts[value] += 1

        for suit, count in counts.iteritems():
            if count >= self.HAND_LENGTH:
                return suit
        return None

    def __score_flush(self):
        return 0

    def __score_high_card(self):
        return self.cards[0].score_value()

    def __score_pairs(self, pairs):
        return 0

    def __score_full_house(self, trips, pairs):
        return 0

class Constants(object):
    CLUBS = Suit(0)
    DIAMONDS = Suit(1)
    HEARTS = Suit(2)
    SPADES = Suit(3)

    # Can use real numbers for everything else
    JACK = 11
    QUEEN = 12
    KING = 13
    ACE = 14
