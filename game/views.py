from django.contrib.auth.decorators import login_required
from django.contrib.sites.models import Site
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from forms import UserSignUpForm
from django.template import RequestContext
from models import Session, Player, GameError
from cards import ThousandCard
from django.db.models import Q
import simplejson as json

def welcome(request):
    if request.user.is_authenticated():
        return render_to_response('sessions.html', context_instance=RequestContext(request))
    else:
        return render_to_response('welcome.html', context_instance=RequestContext(request))

@login_required
def sessions(request):
    user = request.user
    sessions = Session.objects.filter(Q(player_1__user=user) | Q(player_2__user=user) | Q(player_3__user=user))
    result = []
    for s in sessions:
        line = {}
        line['id'] = s.id
        line['hostedby'] = s.player_1.user.username
        line['started'] = s.started
        line['lastmove'] = s.modified
        if s.state in ('waiting', 'ready'):
            line['turn'] = s.dealer.user.username
        else:
            line['turn'] = s.turn.user.username   
        if s.finished:
            line['state'] = 'Finished'
        else:
            line['state'] = 'Active'
        result.append(line)
    site = Site.objects.get_current()
    return render_to_response('sessions.html', {'sessions': result, 'domain': site.domain}, context_instance=RequestContext(request))
    
def signup(request, template_name='registration/signup.html', signup_form=UserSignUpForm):
    if request.method == "POST":
        form = signup_form(request.POST)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect('signup_done')
    else:
        form = signup_form()
    
    return render_to_response(template_name, {'form': form}, context_instance=RequestContext(request))
    
def signup_done(request, template_name='registration/signup_done.html'):
    return render_to_response(template_name)

@login_required
def host(request):
    session = Session()
    session.host(request.user)
    site = Site.objects.get_current()
    return render_to_response('host.html', {'id': session.id, 'domain': site.domain}, context_instance=RequestContext(request))

@login_required
def play(request, id):
    user = request.user
    try:
        session = Session.objects.get(id=id)
    except Session.DoesNotExist:
        return render_to_response('error.html', {'error': 'This session does not exist.'}, context_instance=RequestContext(request))
    
    try:
        player = session.getPlayerByUser(user)
        if player is None:
            player = session.join(user)
    
        return render_to_response('game.html', {'ingame':True})
    except GameError, error:
        return render_to_response('error.html', {'error': error}, context_instance=RequestContext(request))


def getstate(request, id):
    user = request.user
    try:
        session = Session.objects.get(id=id)
    except Session.DoesNotExist:
        return {'error': 'This session does not exist.'}
    
    response = {}
    try:
        player = session.getPlayerByUser(user)
        if player is None:
            player = session.join(user)
    
        if session.player_1 == player:
            opponent1, opponent2 = session.player_2, session.player_3
        elif session.player_2 == player:
            opponent1, opponent2 = session.player_3, session.player_1
        elif session.player_3 == player:
            opponent1, opponent2 = session.player_1, session.player_2
    
        for p in ('player', 'opponent1', 'opponent2'):
            pl = eval(p)
            response[p + '_turn'] = ''
            response[p + '_info'] = ''
            if pl:
                response[p + '_username'] = pl.user.username
                response[p + '_points'] = str(pl.points) + ' points'
            else:
                response[p + '_username'] = '[Not connected]'
                response[p + '_points'] = ''
        
        response['info_header'] = ''
        
        if session.isFull():
            turn = session.turn
            if player.blind is True:
                response['state'] = 'go_blind'
                response['cards'] = ['BACK'] * 7
            elif player.blind is False:
                response['state'] = 'go_open'
                response['cards'] = [str(c) for c in sorted(player.cards)]
            else:
                response['state'] = 'open_or_blind'
                response['cards'] = ['BACK'] * 7
            if session.state == 'ready':
                turn = session.dealer
                response['state'] = 'ready'
                if session.bet is not None:
                    next = session.getNextPlayer(player)
                    nextnext = session.getNextPlayer(next)
                    response['player_info'] = 'Took: %d' % player.bet
                    response['opponent1_info'] = 'Took: %d' % next.bet
                    response['opponent2_info'] = 'Took: %d' % nextnext.bet
            elif session.state == 'bettings':
                response['bank'] = ['BACK'] * 3
                response['passed'] = player.passed
                response['first'] = session.isFirstMove()
                if not player.passed:
                    response['bettings'] = []
                    for bet in range(session.bet + 10, 301, 10):
                        response['bettings'].append(bet)
                for p in ('player', 'opponent1', 'opponent2'):
                    pl = eval(p)
                    if pl.passed:
                        response[p + '_info'] = 'Pass'
                    elif pl.bet:
                        response[p + '_info'] = 'Bet %d' % pl.bet
                        if (pl.blind):
                            response[p + '_info'] += ' (Blind)'
                    else:
                        response[p + '_info'] = ''
            elif session.state == 'collect':
                winner = session.betsWinner()
                response['info_header'] = winner.user.username + ' takes the bank'
                response['state'] = 'collect'
                response['cards'] = [str(c) for c in sorted(player.cards)]
                if player == winner:
                    response['bank'] = [str(c) for c in session.bank]
                else:
                    if session.blind:
                        response['bank'] = ['BACK'] * 3
                    else:
                        response['bank'] = [str(c) for c in session.bank]
            elif session.state == 'finalBet':
                response['state'] = 'finalBet'
                response['cards'] = [str(c) for c in sorted(player.cards)]
                if turn == player:
                    response['info_header'] = 'Discard 3 card and make final bet'
                    response['bank'] = [str(c) for c in session.bank]
                    response['bettings'] = []
                    for bet in range(session.bet, 301, 10):
                        response['bettings'].append(bet)
                else:
                    response['info_header'] = 'Waiting for final bet'
                    response['bank'] = ['BACK'] * len(session.bank)
            elif session.state == 'inGame':
                response['state'] = 'inGame'
                next = session.getNextPlayer(player)
                nextnext = session.getNextPlayer(next)
                offset = max(len(player.thrown), len(next.thrown), len(nextnext.thrown))
                response['bank'] = []
                response['memo'] = []
                for p in (player, next, nextnext):
                    if offset > 0 and len(p.thrown) == offset:
                        response['bank'].append(str(p.thrown[offset-1]))
                    else:
                        response['bank'].append(None)
                    if offset > 1 and len(p.thrown) >= offset-1:
                        response['memo'].append(str(p.thrown[offset-2]))
                    else:
                        response['memo'].append(None)
                response['cards'] = [str(c) for c in sorted(player.cards)]
                if session.trump:
                    response['trump'] = 'Trump: ' + ThousandCard.kinds[session.trump]
                else:
                    response['trump'] = ''
                if session.info:
                    response['info_header'] = session.info
        
            if turn == player: response['player_turn'] = 'Waiting for turn'
            elif turn == opponent1: response['opponent1_turn'] = 'Waiting for turn'
            elif turn == opponent2: response['opponent2_turn'] = 'Waiting for turn'
        
        else:
            response['info_header'] = 'Waiting for players'
            response['state'] = 'waiting'

        
    except GameError, error:
        return {'error': error}
    return response
    
def update(request, id):
    state = getstate(request, id)
    print state
    out = json.dumps(state, separators=(',',':'))
    return HttpResponse(out, mimetype='application/json')

def ok():
    return HttpResponse('OK', mimetype='text/plain')
    

def start(request, id):
    try:
        session = Session.objects.get(id=id)
    except Session.DoesNotExist:
        return HttpResponse('This session does not exist.', mimetype='text/plain')
    
    user = request.user
    player = session.getPlayerByUser(user)
    
    try:
        session.start(player)
        return ok()
    except GameError, error:
        print error
        return HttpResponse(error, mimetype='text/plain')
    
    
def goOpen(request, id):
    try:
        session = Session.objects.get(id=id)
    except Session.DoesNotExist:
        return HttpResponse('This session does not exist.', mimetype='text/plain')

    player = session.getPlayerByUser(request.user)
    player.goOpen()
    return ok()

def goBlind(request, id):
    try:
        session = Session.objects.get(id=id)
    except Session.DoesNotExist:
        return HttpResponse('This session does not exist.', mimetype='text/plain')

    player = session.getPlayerByUser(request.user)
    player.goBlind()
    return ok()

def raiseBet(request, id, upto):
    try:
        session = Session.objects.get(id=id)
    except Session.DoesNotExist:
        return HttpResponse('This session does not exist.', mimetype='text/plain')
    
    player = session.getPlayerByUser(request.user)
    
    if session.state == 'bettings':
        session.raiseBet(player, int(upto))
    elif session.state == 'finalBet':
        session.begin(player, int(upto))
    return ok()

def makePass(request, id):
    try:
        session = Session.objects.get(id=id)
    except Session.DoesNotExist:
        return HttpResponse('This session does not exist.', mimetype='text/plain')

    player = session.getPlayerByUser(request.user)
    session.makePass(player)
    return ok()

def collectBank(request, id):
    try:
        session = Session.objects.get(id=id)
    except Session.DoesNotExist:
        return HttpResponse('This session does not exist.', mimetype='text/plain')

    player = session.getPlayerByUser(request.user)
    session.collectBank(player)
    return ok()

def putCard(request, id, card):
    try:
        session = Session.objects.get(id=id)
    except Session.DoesNotExist:
        return HttpResponse('This session does not exist.', mimetype='text/plain')
    
    player = session.getPlayerByUser(request.user) 
    card = ThousandCard(card)
    if session.state == 'finalBet':
        session.discardCard(player, card)
    else:
        session.putCard(player, card)
    return ok()

def retrieveCard(request, id, card):
    try:
        session = Session.objects.get(id=id)
    except Session.DoesNotExist:
        return HttpResponse('This session does not exist.', mimetype='text/plain')

    player = session.getPlayerByUser(request.user)  
    card = ThousandCard(card)
    session.retrieveCard(player, card)
    return ok()        