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
    thrown = ThousandCardField(7, null=True)
    tricks = ThousandCardField(24, null=True)
    blind = models.NullBooleanField(null=True)
    bet = models.SmallIntegerField(null=True)
    passed = models.BooleanField(default=False)
    plus = models.BooleanField(default=False)
    calls = models.CharField(max_length=4)
    
    def goBlind(self):
        """
        Chooses to play blind.
        
        Fails if:
            - Choise was already open.
        """
        
        if self.blind is False:
            raise GameError('The choise was already made to be open.')
        
        self.blind = True
        self.save()
    
    def goOpen(self):
        """
        Chooses to play open.
        
        Always succeeds. None -> Open OK. Blind -> Open OK.
        """
        
        self.blind = False
        self.save()
    
    def hasPair(self, card):
        """
        Checks if player have a pair for given card.
        """
        
        v = card.value()
        k = card.kind()
        if v == 'K':
            c = ThousandCard(k+'Q')
            return c in self.cards
        elif v == 'Q':
            c = ThousandCard(k+'K')
            return c in self.cards
        else:
            return False
    
    def hasKind(self, kind):
        """
        Checks if player has card for given kind.
        """
        
        for card in self.cards:
            if card.kind() == kind:
                return True
        return False
    
    def getGamePoints(self):
        """
        Calculates and returns points collected in current game.
        """
        
        points = 0
        for c in self.calls:
            points += ThousandCard.pairs[c]
        for c in self.tricks:
            points += c.points()
        return points

class Session(models.Model):
    player_1 = models.OneToOneField(Player, null=False, related_name='session_as1')
    player_2 = models.OneToOneField(Player, null=True, related_name='session_as2')
    player_3 = models.OneToOneField(Player, null=True, related_name='session_as3')
    dealer = models.OneToOneField(Player, null=False, related_name='session_as_dealer')
    started = models.DateTimeField(auto_now_add=True, null=False)
    modified = models.DateTimeField(auto_now=True, null=False)
    finished = models.DateTimeField(null=True)
    turn = models.ForeignKey(Player, null=True)
    bet = models.SmallIntegerField(null=True)
    state = models.CharField(max_length=8, null=False)
    blind = models.BooleanField(default=False)
    bank = ThousandCardField(3, null=True)
    trump = models.CharField(max_length=1, null=True)
    info = models.CharField(max_length=64, null=True)

    def host(self, user):
        """
        One user start the session as host.
        """
        
        player = Player(user=user)
        player.save()
        self.player_1 = player
        self.dealer = player
        self.state = 'waiting'
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
            self.state = 'ready'
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

    def start(self, player):
        """
        New game is started in given session.
        The game can only be started by dealer.
        The turn is given to player after dealer.

        Fails if:
            - Current game have not been finished.
            - Session is not full.
            - Current user is not a dealer.
        """

        if self.state != 'ready':
            raise GameError('Current game have not been finished or session is not full.')
        if player != self.dealer:
            raise GameError('Only the dealer can start the game.')

        cards = ThousandCard.generateDeck()
        shuffle(cards)
        for i, player in enumerate([self.player_1, self.player_2, self.player_3]):
            player.cards = cards[i*7:(i+1)*7]
            player.passed = False
            player.bet = None
            player.blind = None
            player.bank = []
            player.thrown = []
            player.tricks = []
            player.calls = ''
            player.save()
        self.bank = cards[21:24]
        self.turn = self.dealer = self.getNextPlayer(self.dealer)
        self.bet = 90
        self.state = 'bettings'
        self.blind = False
        self.trump = None
        self.info = None
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

        if self.state != 'bettings':
            raise GameError('Bettings are already finished.')
        if self.turn != player:
            raise GameError('It\'s not your turn to bet.')
        if bet < 100 or bet > 300:
            raise GameError('Bet must be between 100 and 300.')
        if bet % 10 != 0:
            raise GameError('Bets must be divisible by 10.')
        if bet <= self.bet:
            raise GameError('Your bet must be higher than current bet.')

        player.bet = bet
        player.save()
        self.bet = bet
        self.turn = self.getNextPlayer(player)
        self.save()

        if self.betsOver():
            self.finishBets()

    def makePass(self, player):
        """
        Passes the bettings in current game. The player can only pass once in a game.

        Fails if:
            - Bets are already finished
            - The turn is not for the given player
            - Player has already passed
            - Player can not pass if he is the first one
        """

        if self.state != 'bettings':
            raise GameError('Bettings are already finished.')
        if self.turn != player:
            raise GameError('It\'s not your turn to pass.')
        if player.passed:
            raise GameError('This player has already passed.')
        if self.isFirstMove():
            raise GameError('The first player cannot pass the first time.')

        player.passed = True
        player.save()
        self.turn = self.getNextPlayer(player)
        self.save()

        if self.betsOver():
            self.finishBets()

    def getPlayerOffset(self, player):
        """
        Returns given player offset in current game.
        That is, how far away the player is from the first player.
        """

        if (len(self.bank) == 0) or (self.state != 'inGame'):
            return 0
        else:
            card = player.bank[0]
            nextcard = self.getNextPlayer(player).bank[0]
            if self.bank[0] == card: return 0
            elif self.bank[0] == nextcard: return 1
            else: return 2

    def isFirstMove(self):
        """
        Checks if it is the first move in the game.
        """

        return (self.bet == 90) and (self.dealer == self.turn)

    def betsOver(self):
        """
        Checks if bettings are over.

        Bet are over when:
            - Two of the three player passes
            - 300 points bet is reached
        """

        passed = 0
        if self.player_1.passed: passed += 1
        if self.player_2.passed: passed += 1
        if self.player_3.passed: passed += 1

        if passed == 2:
            return True
        if self.bet == 300:
            return True
        return False

    def betsWinner(self):
        """"
        Returns bets winner (last betting player) which can collect the bank.
        """

        if self.player_1.bet == '300': return self.player_1
        if self.player_2.bet == '300': return self.player_2
        if self.player_3.bet == '300': return self.player_3

        if not self.player_1.passed: return self.player_1
        elif not self.player_2.passed: return self.player_2
        elif not self.player_3.passed: return self.player_3
        else: raise GameError('Unexpected error: all players passed')

    def finishBets(self):
        """
        After bets are over, set game variables and goes to bank collect state.
        """

        player = self.betsWinner()
        self.bet = player.bet
        self.blind = player.blind
        self.state = 'collect'
        self.turn = player
        self.save()
        
    def collectBank(self, player):
        """
        Collect the bank.

        Fails if:
            - Game state is not for collect.
            - The given player is the winner of bettings.
        """

        if self.state != 'collect':
            raise GameError('Bank can not be collected at this game state.')
        if self.betsWinner() != player:
            raise GameError('Only the bets winner can collect the bank.')

        player.cards += self.bank
        player.save()
        self.bank = []
        self.state = 'finalBet'
        self.save()

    def discardCard(self, player, card):
        """
        Discards card to the bank.

        Fails if:
            - The turn is not for the given player.
            - There is already 3 cards in bank.
            - Player does not have given card.
            - Game state is not for discarding cards.
        """

        if self.state != 'finalBet':
            raise GameError('You can not put cards in this game state.')
        if self.turn != player:
            raise GameError('It\'s not your turn to go.')
        if len(self.bank) == 3:
            raise GameError('There is already 3 cards in bank.')
        if not card in player.cards:
            raise GameError('Player does not have given card.')

        player.cards.remove(card)
        self.bank.append(card)
        player.save()
        self.save()

    def retrieveCard(self, player, card):
        """
        Retrieves card from the bank in final bet state (in case of mistake).

        Fails if:
            - Game state is not final bet.
            - The turn is not for the given player.
            - Bank does not contain given card.
        """

        if self.state != 'finalBet':
            raise GameError('Retrieving cards is possible only in final bet state.')
        if self.turn != player:
            raise GameError('It\'s not your turn to go.')
        if not card in self.bank:
            raise GameError('Bank does not contain given card.')

        self.bank.remove(card)
        self.save()
        player.cards.append(card)
        player.save()

    def begin(self, player, finalBet):
        """
        Called after bank collection and final bet. Start the main game.

        Fails if:
            - The turn is not for the given player.
            - Game state is not final bet.
            - 3 cards have not been discarded.
            - Final bet is not bettween 100 and 300
            - Final bet is not divisible by 10
            - Final bet is smaller than current bet.
        """

        if self.turn != player:
            raise GameError('It\'s not your turn.')
        if self.state != 'finalBet':
            raise GameError('Game can be begun only in final bet state.')
        if len(self.bank) != 3:
            raise GameError('3 cards must be discarded before begining the game.')
        if finalBet < 100 or finalBet > 300:
            raise GameError('Bet must be between 100 and 300.')
        if finalBet % 10 != 0:
            raise GameError('Bet must be divisible by 10.')
        if finalBet < self.bet:
            raise GameError('Your bet must be higher or equal than current bet.')

        self.bet = finalBet
        self.state = 'inGame'
        player.tricks = self.bank
        self.bank = []
        player.save()
        self.save()
    
    def putCard(self, player, card):
        """
        Puts card to the bank.

        Fails if:
            - The turn is not for the given player.
            - There is already 3 cards in bank.
            - Player does not have given card.
            - Game state is not for putting cards.
        """

        if self.state != 'inGame':
            raise GameError('You can not put cards in this game state.')
        if self.turn != player:
            raise GameError('It\'s not your turn to go.')
        if len(self.bank) == 3:
            raise GameError('There is already 3 cards in bank.')
        if not card in player.cards:
            raise GameError('Player does not have given card.')

        if len(self.bank) > 0:
            first = self.bank[0]
            if (first.kind() == card.kind()) or (not player.hasKind(first.kind())):
                player.cards.remove(card)
                player.thrown.append(card)
                self.bank.append(card)
            else:
                raise GameError('You must put the card with matching kind.')
        else:
            player.cards.remove(card)
            player.thrown.append(card)
            self.bank.append(card)

        player.bank = [card]
        self.info = ''
        if (len(self.bank) == 1) and player.hasPair(card):
            player.calls += card.kind()
            self.trump = card.kind()
            self.info = '%s calls %d (%s)' % (player.user.username, 
                        ThousandCard.pairs[self.trump], ThousandCard.kinds[self.trump])
        if len(self.bank) == 3:
            self.bank[0].player = self.getNextPlayer(player)
            self.bank[1].player = self.getNextPlayer(self.bank[0].player)
            self.bank[2].player = player
            anyTrumps = ([c.kind() for c in self.bank].count(self.trump) > 0)
            for c in self.bank:
                if anyTrumps:
                    c.isTrump = (c.kind() == self.trump)
                else:
                    c.isTrump = (c.kind() == self.bank[0].kind())
                c.__cmp__ = lambda x: cardCompare(c, x)
            bestCard = max(self.bank)
            bestCard.player.tricks += self.bank
            bestCard.player.save()
            self.bank = []
            self.turn = bestCard.player
            self.info = bestCard.player.user.username + ' takes the trick'
            if len(player.cards) == 0:
                w = self.betsWinner()
                for p in (self.player_1, self.player_2, self.player_3):
                    pts = p.getGamePoints()
                    print p.user.username, pts
                    if p == w:
                        if pts >= self.bet:
                            pts = self.bet
                            self.info = "%s succeeds playing %d" % (p.user.username, self.bet)
                        else:
                            pts = -self.bet
                            self.info = "%s fails playing %d" % (p.user.username, self.bet)
                        if self.blind:
                            self.info += " (Blind)"
                            pts *= 2
                        p.points += pts
                    else:
                        if self.blind:
                            pts *= 2
                        pts = int(round(pts, -1))
                        if p.points > 900:
                            pts = 0
                        p.points += pts
                    p.bet = pts
                    p.save()
                h = History(session=self, player_1=p1.points, player_2=p2.points, player_3=p3.points)
                h.save()
                self.state = 'ready'
                self.save()
                return
        else:
            self.turn = self.getNextPlayer(player)
        player.save()
        self.save()


class History(models.Model):
    session = models.ForeignKey(Session, null=False)
    player_1 = models.SmallIntegerField(null=False)
    player_2 = models.SmallIntegerField(null=False)
    player_3 = models.SmallIntegerField(null=False)


def cardCompare(self, other):
    """
    Compares to cards with respect to trump.
    """
    
    t1 = self.isTrump
    t2 = other.isTrump
    if (t1 == False) and (t2 == True):
        return -1
    elif (t1 == True) and (t2 == False):
        return 1
    else:
        v1 = self.value()
        v2 = other.value()
        if self.value_order.index(v1) < self.value_order.index(v2):
            return -1
        elif self.value_order.index(v1) > self.value_order.index(v2):
            return 1
        else:
            return 0
