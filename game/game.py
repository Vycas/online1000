from models import Session, Game, History
from django.contrib.auth.models import User

def startSession(user):
    """
    One user start the session as host.
    """

    session = Session()
    session.player_1 = user
    return session


def startGame(session):
    """
    Starts the new game in one of the sessions.
    """

    game = Game()
    game.session = session
    
