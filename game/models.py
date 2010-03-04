from django.db import models
from django.contrib.auth.models import User
from cards import dealCards

class GameError(Exception):
    pass

class Session(models.Model):
    id = models.AutoField()
    player_1 = models.ForeignKey(User, null=False)
    player_2 = models.ForeignKey(User, null=False)
    player_3 = models.ForeignKey(User, null=False)
    player_4 = models.ForeignKey(User, null=True)
    dealer = models.ForeignKey(User, null=False)
    started = models.DateField(auto_now_add=True)
    finished = models.DateField()

    def __init__(self, user):
        """
        One user start the session as host.
        """

        self.player_1 = user
        self.dealer = user
        
    def getNextTurn(self, current):
        """
        Returns who is the next after the current player.
        """

        if current == self.player_1:
            return player_2
        elif current == self.player_2:
            return player_3
        elif current == self.player_3:
            if self.player_4 is None:
                return player_1
            else:
                return player_4
        else:
            return None

class Game(models.Model):
    id = models.AutoField()
    session = models.ForeignKey(Session, null=False)
    turn = models.ForeignKey(User, null=False)
    bet = models.SmallIntegerField(null=False)
    bettings = models.BooleanField(null=False)
    blind = models.BooleanField(null=False)
    cards_1 = models.CharField(max_length=28, null=False)
    cards_2 = models.CharField(max_length=28, null=False)
    cards_3 = models.CharField(max_length=28, null=False)
    bank = models.CharField(max_length=12, null=False)
    trump = models.CharField(max_length=1, null=True)

    def __init__(self, session):
        """
        New game is started in given session.
        The turn is given to player after dealer.
        """

        self.session = session
        self.turn = session.dealer = session.getNextTurn(session.dealer)
        self.bet = 100
        self.bettings = True
        self.blind = False
        self.trump = None
        cards_1, cards_2, cards_3, bank = dealCards()

    def raiseBet(self, user, bet):
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
        if self.turn != user:
            raise GameError('It\'s not your turn to bet.')
        if bet < 100 or bet > 300:
            raise GameError('Bet must be between 100 and 300.')
        if bet % 10 != 0:
            raise GameError('Bets must be divisible by 10.')
        if bet < self.bet:
            raise GameError('Your bet must be higher than current bet.')
        
        self.bet = bet
        self.turn = session.getNextTurn(self.turn)

        if bet == 300:
            self.bettings = False

    def makePass(self, user):
        """
        Passes the bettings in current game. The user can only pass once in a game.

        Fails if:
            - Bets are already finished
            - The turn is not for the given user
            - User has already passed
        """
        
        if not self.bettings:
            raise GameError('Bettings are already finished.')
        if self.turn != user:
            raise GameError('It\'s not your turn to pass.')

class History(models.Model):
    id = models.AutoField()
    game = models.ForeignKey(Game, null=False)
    player_1 = models.SmallIntegerField(null=False)
    player_2 = models.SmallIntegerField(null=False)
    player_3 = models.SmallIntegerField(null=False)
    player_4 = models.SmallIntegerField(null=True)
