from django.contrib.auth.decorators import login_required
from django.contrib.sites.models import Site
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from forms import UserSignUpForm
from django.template import RequestContext
from models import Session, Player, Game
from django.db.models import Q

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
    session.save()
    site = Site.objects.get_current()
    return render_to_response('host.html', {'id': session.id, 'domain': site.domain}, context_instance=RequestContext(request))

@login_required
def play(request, id):
    try:
        session = Session.objects.get(id=id)
    except Session.DoesNotExist:
        return render_to_response('error.html', {'error': 'This session does not exist.'}, context_instance=RequestContext(request))
    if session.playing(request.user):
        pass #todo playing
    elif session.is_full():
        return render_to_response('error.html', {'error': 'This session is already full.'}, context_instance=RequestContext(request))
    else:
        session.join(request.user)
        #todo playing