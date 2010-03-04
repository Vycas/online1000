from random import shuffle

spades = 'S'
clubs = 'C'
diamonds = 'D'
hearts = 'H'

king = 'K'
queen = 'Q'
jack = 'J'

ace = 'A'

def getDeck(downto=2):
    """
    Generates a deck of card down to given card.
    """

    base = [ace, king, queen, jack]
    kinds = [spades, clubs, diamonds, hearts]
    cards = base + range(downto, 11)
    return [kind + str(card) for card in cards for kind in kinds]

def dealCards():
    """
    Deal cards for 1000 game and returns tuple for 3 players + bank.
    """

    cards = getDeck(9)
    shuffle(cards)
    return (cards[0:7], cards[7:14], cards[14:21], cards[21:24])

def encodeToString(cards):
    """
    Encodes list of cards to string.
    """

    return ' '.join(cards)

def decodeFromString(cards):
    """
    Decodes the string to the list of cards.
    """

    return cards.split(' ')

