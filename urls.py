from django.conf.urls.defaults import *
from django.contrib.auth.views import *
from game.views import *

urlpatterns = patterns('',
    (r'', include('django.contrib.auth.urls')),
    
    (r'^$', welcome),
    (r'^welcome$', welcome),
    (r'^signup$', signup),
    (r'^signup_done$', signup_done),
    (r'^sessions$', sessions),
    (r'^host/$', host),
    (r'^play/(\d+)$', play),
    (r'^update/(\d+)$', update),
    (r'^start/(\d+)$', start),
    (r'^open/(\d+)$', goOpen),
    (r'^blind/(\d+)$', goBlind),
    (r'^bet/(\d+)/(\d+)$', raiseBet),
    (r'^pass/(\d+)$', makePass),
    (r'^collect/(\d+)$', collectBank),
    (r'^put/(\d+)/(\w{2,3})$', putCard),
    (r'^retrieve/(\d+)/(\w{2,3})$', retrieveCard),
    
    # [Static serve]
    (r'^styles/(?P<path>.*)$', 'django.views.static.serve',
        {'document_root': 'game/styles'}),
    (r'^images/(?P<path>.*)$', 'django.views.static.serve',
        {'document_root': 'game/images'}),
    (r'^js/(?P<path>.*)$', 'django.views.static.serve',
        {'document_root': 'game/js'}),
)
