from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from forms import UserSignUpForm
from django.template import RequestContext

def welcome(request):
    return render_to_response('welcome.html')

def sessions(request):
    return render_to_response('sessions.html')
    
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