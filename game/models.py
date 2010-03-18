from django.db import models
from django.contrib.auth.models import User
from cards import ThousandCard
from fields import ThousandCardField
from random import shuffle

class GameError(Exception):
    pass


class Player(models.Model):
    user = models.ForeignKey(User, null=False)
    points = models.SmallIntegerField(null=False, default=0)
    cards = ThousandCardField(10, null=True)
    bank = ThousandCardField(3, null=True)
    tricks = ThousandCardField(24, null=True)
    blind = models.NullBooleanField(null=True)
    passed = models.BooleanField(default=False)
    plus = models.BooleanField(default=False)
    
    def go_blind(self):
        """
        Chooses to play blind.
        
        Fails if:
            - Choise was already open.
        """
        
        if self.blind is False:
            raise GameError('The choise was already made to be open.')
        
        self.blind = True
        self.save()
    
    def go_open(self):
        """
        Chooses to play open.
        
        Always succeeds. None -> Open OK. Blind -> Open OK.
        """
        
        self.blind = False
        self.save()


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
        self.save()
        return player

    def join(self, user):
        """
        Another user joins this session and becomes its player.
        """

        if self.player_2 is None:
            player = Player(user=user)
            player.save()
            self.player_2 = player
            self.save()
            return player
        elif self.player_3 is None:
            player = Player(user=user)
            player.save()
            self.player_3 = player
            self.save()
            return player
        else:
            raise GameError('This session is already full.')
        
    def isFull(self):
        """
        Checks if all three player joined.
        """

        return (self.player_2 is not None) and \
               (self.player_2 is not None) and \
               (self.player_3 is not None)
    
    def hasActiveGame(self):
        """
        Checks if there is a started game.
        """
        
        try:
            self.game
            return True
        except Game.DoesNotExist:
            return False

    def getPlayerByUser(self, user):
        """
        Return the player associated with given user in this session.
        """
        
        if self.player_1 and self.player_1.user == user: return self.player_1
        elif self.player_2 and self.player_2.user == user: return self.player_2
        elif self.player_3 and self.player_3.user == user: return self.player_3
        else: return None

    def getNextPlayer(self, current):
        """
        Returns who is the next after the current player.
        """

        if current == self.player_1:
            return self.player_2
        elif current == self.player_2:
            return self.player_3
        elif current == self.player_3:
            return self.player_1


class Game(models.Model):
    session = models.OneToOneField(Session, null=False)
    turn = models.ForeignKey(Player, null=False)
    bet = models.SmallIntegerField(null=False)
    state = models.CharField(max_length=8, null=False)
    blind = models.BooleanField(null=False)
    bank = ThousandCardField(3, null=False)
    trump = models.CharField(max_length=1, null=True)

    def start(self, session, player):
        """
        New game is started in given session.
        The game can only be started by dealer.
        The turn is given to player after dealer.
        
        Fails if:
            - The session already has an active game.
            - Session is not full.
            - Current user is not a dealer.
        """

        try:
            session.game
            raise GameError('This session already has an active game.')
        except Game.DoesNotExist:
            pass

        if not session.isFull():
            raise GameError('Session must be full to start a game.')
        
        if player != session.dealer:
            raise GameError('Only the dealer can start the game.')

        self.session = session
        cards = ThousandCard.generateDeck()
        shuffle(cards)
        player = session.player_1
        for i in range(3):
            player.cards = sorted(cards[i*7:(i+1)*7])
            player.passed = False
            player.blind = None
            player.bank = []
            player.tricks = []
            player.save()
            player = session.getNextPlayer(player)
        self.bank = cards[21:24]
        self.turn = session.dealer = session.getNextPlayer(session.dealer)
        self.bet = 100
        self.state = 'started'
        self.blind = False
        self.trump = None
        self.save()

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
            - Player can not pass if he is the first one
        """
        
        if not self.bettings:
            raise GameError('Bettings are already finished.')
        if self.turn != player:
            raise GameError('It\'s not your turn to pass.')
        if player.passed:
            raise GameError('This player has already passed.')
        if self.bet == 100 and self.session.dealer == player:
            raise GameError('The first player cannot pass the first time.')

        player.passed = True
        self.turn = session.getNextPlayer(player)

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
