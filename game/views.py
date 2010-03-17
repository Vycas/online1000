from django.contrib.auth.decorators import login_required
from django.contrib.sites.models import Site
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from forms import UserSignUpForm
from django.template import RequestContext
from models import Session, Player, Game, GameError
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
        line['lastmove'] = ''
        try: 
            line['turn'] = s.game.turn.username
        except Game.DoesNotExist:
            line['turn'] = s.dealer.user.username
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
    
        response['player_username'] = player.user.username
        response['player_points'] = str(player.points) + ' points'
        if opponent1:
            response['opponent1_username'] = opponent1.user.username
            response['opponent1_points'] = str(opponent1.points) + ' points'
        else:
            response['opponent1_username'] = '[Not connected]'
            response['opponent1_points'] = ''
        if opponent2:
            response['opponent2_username'] = opponent2.user.username
            response['opponent2_points'] = str(opponent2.points) + ' points'
        else:
            response['opponent2_username'] = '[Not connected]'
            response['opponent2_points'] = ''
        
        response['player_turn'] = ''
        response['opponent1_turn'] = ''
        response['opponent2_turn'] = ''
        
        response['info_header'] = ''
        
        if session.isFull():
            if session.hasActiveGame():
                turn = session.game.turn
                response['state'] = 'started'
            else:
                turn = session.dealer
                response['state'] = 'ready'
            
            if turn == player: response['player_turn'] = 'Waiting for turn'
            elif turn == opponent1: response['opponent1_turn'] = 'Waiting for turn'
            elif turn == opponent2: response['opponent2_turn'] = 'Waiting for turn'
            
            
        else:
            response['info_header'] = 'Waiting for players'
            response['state'] = 'waiting'
        #response['bettings'] = []
        #for a in range(140, 301, 10):
        #    response['bettings'].append(a)
        
    except GameError, error:
        return {'error': error}
    return response
    
def update(request, id):
    state = getstate(request, id)
    print state
    out = json.dumps(state, separators=(',',':'))
    return HttpResponse(out, mimetype='application/json')

def start(request, id):
    try:
        session = Session.objects.get(id=id)
    except Session.DoesNotExist:
        return HttpResponse('This session does not exist.', mimetype='text/plain')
    
    try:
        game = Game()
        game.start(session)
        
    except GameError, error:
        print error
        return HttpResponse(error, mimetype='text/plain')
    
    