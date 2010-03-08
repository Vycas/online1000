from django.db import models
from django.contrib.auth.models import User
from cards import CardSet, ThousandCard
from random import shuffle

class GameError(Exception):
    pass


class Player(models.Model):
    user = models.ForeignKey(User, null=False)
    cards = models.CharField(max_length=32)
    bank = models.CharField(max_length=16)
    tricks = models.CharField(max_length=128)
    passed = models.BooleanField()


class Session(models.Model):
    player_1 = models.OneToOneField(Player, null=False, related_name='session_as1')
    player_2 = models.OneToOneField(Player, null=True, related_name='session_as2')
    player_3 = models.OneToOneField(Player, null=True, related_name='session_as3')
    dealer = models.OneToOneField(Player, null=False, related_name='session_as_dealer')
    started = models.DateTimeField(auto_now_add=True, null=False)
    finished = models.DateTimeField(null=True)

    def host(self, user):
        """
        One user start the session as host.
        """
        
        player = Player(user=user)
        player.save()
        self.player_1 = player
        self.dealer = player

    def join(self, user):
        """
        Another user joins this session and becomes its player.
        """

        if self.player_2 is None: self.player_2 = Player(user)
        elif self.player_3 is None: self.player_3 = Player(user)
        else: raise GameError('This session is already full.')
        
    def playing(self, user):
        """
        Checks if current user is playing in this session.
        """
        
        return user in (self.player_1, self.player_2)
        
    def is_full(self):
        """
        Checks if all three player joined.
        """

        return (self.player_2 is not None) and (self.player_3 is not None)

    def getNextPlayer(self, current):
        """
        Returns who is the next after the current player.
        """

        if current == self.player_1:
            return player_2
        elif current == self.player_2:
            return player_3
        elif current == self.player_3:
            return player_1


class Game(models.Model):
    session = models.OneToOneField(Session, null=False)
    turn = models.ForeignKey(Player, null=False)
    bet = models.SmallIntegerField(null=False)
    bettings = models.BooleanField(null=False)
    blind = models.BooleanField(null=False)
    bank = models.CharField(max_length=16, null=False)
    trump = models.CharField(max_length=1, null=True)

    def start(self, session):
        """
        New game is started in given session.
        The turn is given to player after dealer.
        """

        if session.game is not None:
            raise GameError('This session already has active game.')

        if not session.isfull:
            raise GameError('Session must be full to start a game.')

        self.session = session
        cards = shuffle(ThousandCard.generateDeck())
        player = session.player_1
        for i in range(3):
            player.cards = cards[i*7:(i+1)*7]
            player.passed = False
            player.bank = None
            player.tricks = None
            player = session.getNextPlayer(player)
        self.bank = cards[21:24]
        self.turn = session.dealer = session.getNextPlayer(session.dealer)
        self.bet = 100
        self.bettings = True
        self.blind = False
        self.trump = None

    def raiseBet(self, player, bet):
        """
        Tries to raise the bet up to given value.

        Fails if:
            - Bets are already finished
            - The turn is not for the given user
            - Value is bettween 100 and 300
            - Value is not divisible by 10
            - Value is smaller than the current bet

        First to reach 300 finished bettings.
        """

        if not self.bettings:
            raise GameError('Bettings are already finished.')
        if self.turn != player:
            raise GameError('It\'s not your turn to bet.')
        if bet < 100 or bet > 300:
            raise GameError('Bet must be between 100 and 300.')
        if bet % 10 != 0:
            raise GameError('Bets must be divisible by 10.')
        if bet < self.bet:
            raise GameError('Your bet must be higher than current bet.')
        
        self.bet = bet
        self.turn = session.getNextPlayer(player)

        if bet == 300:
            self.bettings = False

    def makePass(self, player):
        """
        Passes the bettings in current game. The player can only pass once in a game.

        Fails if:
            - Bets are already finished
            - The turn is not for the given player
            - Player has already passed
        """
        
        if not self.bettings:
            raise GameError('Bettings are already finished.')
        if self.turn != player:
            raise GameError('It\'s not your turn to pass.')
        if player.passed:
            raise GameError('This player has already passed.')

        player.passed = True

    def collectBank(self, player):
        """
        Collect the bank.

        Fails if:
            - The turn is not for the given player
            - All other players have passed
        """

        if self.turn != player:
            raise GameError('It\'s not your turn.')
        next = self.session.getNextPlayer(player)
        nextnext = self.session.getNextPlayer(next)
        if not (next.passed and nextnext.passed):
            raise GameError('All other players have to pass first.')

        player.card += self.bank
        self.bank = None

    def putPrivateBank(self, player, cards):
        """
        Puts away the private bank.

        Fails if:
            - The turn is not for the given player
            - The main bank is not collected yet
            - Given cards are not three
            - Given cards don't belong to player
        """

        if self.turn != player:
            raise GameError('It\'s not your turn.')
        if not self.bank is None:
            raise GameError('The bank is not yet collected.')
        if len(cards) != 3:
            raise GameError('You must discard 3 cards.')
        player.bank = CardSet()
        for c in cards:
            if not c in player.cards:
                raise GameError('Given card does not belong to you.')
            player.bank.append(c)
        for c in player.bank:
            player.cards.remove(c)

    def startGame(self, player):
        """
        Called after bank collection and final bet. Closes bettings and start the game.
        
        Fails if:
            - The turn is not for the given player
            - Bank is not collected
            - Private bank is not put away yet
        """

        if self.turn != player:
            raise GameError('It\'s not your turn.')
        if not self.bank is None:
            raise GameError('The bank is not yet collected.')
        if player.bank is None:
            raise GameError('Private bank is not put away.')

        self.bettings = False

class History(models.Model):
    session = models.ForeignKey(Session, null=False)
    player_1 = models.SmallIntegerField(null=False)
    player_2 = models.SmallIntegerField(null=False)
    player_3 = models.SmallIntegerField(null=False)
