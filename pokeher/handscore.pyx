cimport cython_util as util
cimport cards
import cards
import itertools

cdef enum:
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

cdef class HandScore:
    """The score of a hand. Contains an hand type constant and a value-sorted tuple"""

    def __cinit__(self, type=NO_SCORE):
        """type should be one of the hand types defined here
        kicker is a tuple of card values sorted based on the hand type
        e.g. kicker=(10,10,9,5,2) for a pair of tens, 9-high
        """
        self.type = type
        self.kicker = None

    def __richcmp__(HandScore self, HandScore other not None, int op):
        cdef int compare
        if self.type > other.type:
            compare = 1
        elif self.type < other.type:
            compare = -1
        else:
            if self.kicker > other.kicker:
                compare = 1
            elif self.kicker < other.kicker:
                compare = -1
            else:
                compare = 0

        return util.richcmp_helper(compare, op)

    def __repr__(self):
        return '{self.type}, {self.kicker}'.format(self=self)

cdef enum:
    HAND_LENGTH = 5

cdef class HandBuilder:
    """Makes the best hand from a given set of cards, scores hands
    """

    def __init__(self, cards):
        if isinstance(cards, tuple):
            self.cards = list(cards)
        else:
            self.cards = cards

    def find_hand(self):
        """Returns the best hand & score of length HAND_LENGTH"""
        if not self.cards or len(self.cards) < HAND_LENGTH:
            return None, None

        best_hand_score = HandScore()
        best_hand = None
        for hand in itertools.combinations(self.cards, HAND_LENGTH):
            score = HandBuilder(list(hand)).score_hand()

            if score > best_hand_score:
                best_hand_score = score
                best_hand = hand
        return best_hand, best_hand_score

    def score_hand(self):
        """Returns the HandScore of a 5-card hand
        This guy runs fast. Don't feed it bad entries"""
        cdef HandScore score
        cdef cards.Card card

        score = HandScore()
        if not self.cards or len(self.cards) != HAND_LENGTH:
            return score

        # Find any pairs, triples or quads in the hand and score them
        score.type = HIGH_CARD

        # card values run 2-15 instead of 0-13
        seen = [None,None] + [0]*13
        for card in self.cards:
            seen[card.value] += 1

        # sort by # of times each value was seen
        # this puts quads in front of triples in front of pairs etc
        # if there aren't any pairs, then this sorts by rank order
        self.cards.sort(key=lambda card: (seen[card.value], card.value),
                        reverse=True)
        # this function also sets the handscore if there are any pairs etc.
        score.kicker = tuple(self.__score_cards_to_ranks(score))

        # At this point, return since we can't have any pairs
        # at the same time as a straight or flush
        if score.type > HIGH_CARD:
            return score

        # Do we have a flush?
        flush_suit = self.select_flush_suit()
        if flush_suit != -1:
            score.type = FLUSH

        # Is there a straight?
        if self.is_straight():
            if score.type == FLUSH:
                score.type = STRAIGHT_FLUSH
            else:
                score.type = STRAIGHT

        return score

    def __score_cards_to_ranks(self, HandScore score):
        """Goes through a list of cards sorted by quad/trip/pair and set the hand score."""
        cdef int last_value, run
        cdef cards.Card card

        last_value = -1
        run = 0
        for card in self.cards:
            if card.value == last_value:
                run += 1
            else:
                if run == 4:
                    score.type = QUADS
                elif run == 3:
                    score.type = TRIPS
                elif run == 2:
                    if score.type == TRIPS:
                        score.type = FULL_HOUSE
                    elif score.type == PAIR:
                        score.type = TWO_PAIR
                    else:
                        score.type = PAIR
                run = 1
            last_value = card.value
            yield card.value

        # the full house is the only hand where we need to match on the last card
        if run == 2 and score.type == TRIPS:
            score.type = FULL_HOUSE

    cpdef bint is_straight(self):
        """returns True if this hand is a straight, false otherwise"""
        cdef int last_value
        cdef cards.Card card

        last_value = -1
        for card in self.cards:
            if last_value > 0:
                gap = last_value - card.value
                if gap != 1:
                    return False
            last_value = card.value
        return True

    def cards_to_ranks(self):
        """Returns a generator of the ranks of our cards"""
        cdef cards.Card card
        return (card.value for card in self.cards)

    def sort_hand(self):
        """Sorts a hand, high values first"""
        sort_key = lambda card: card.value
        self.cards.sort(key=sort_key,reverse=True)

    cpdef int select_flush_suit(self):
        """If all cards match suit, return the suit. Return None otherwise."""
        cdef int suit
        cdef cards.Card card

        if not self.cards:
            return -1

        suit = self.cards[0].suit
        for card in self.cards:
            if suit != card.suit:
                return -1

        return suit
