from django.conf.urls.defaults import *
from django.contrib.auth.views import *
from game.views import *

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    (r'', include('django.contrib.auth.urls')),
    
    (r'^$', welcome),
    (r'^welcome$', welcome),
    
    #(r'^login$', login),
    (r'^signup$', signup),
    (r'^signup_done$', signup_done),
    (r'^sessions$', sessions),
    (r'^host/$', host),
    (r'^play/([0-9]+)$', play),
    (r'^update/([0-9]+)$', update),
    (r'^start/([0-9]+)$', start),
    (r'^open/([0-9]+)$', goOpen),
    (r'^blind/([0-9]+)$', goBlind),
    (r'^bet/([0-9]+)/([0-9]+)$', raiseBet),
    (r'^pass/([0-9]+)$', makePass),
    
    # [Static serve]
    (r'^styles/(?P<path>.*)$', 'django.views.static.serve',
        {'document_root': 'game/styles'}),
    (r'^images/(?P<path>.*)$', 'django.views.static.serve',
        {'document_root': 'game/images'}),
    (r'^js/(?P<path>.*)$', 'django.views.static.serve',
        {'document_root': 'game/js'}),


    # Example:
    # (r'^online1000/', include('online1000.foo.urls')),

    # Uncomment the admin/doc line below and add 'django.contrib.admindocs' 
    # to INSTALLED_APPS to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # (r'^admin/', include(admin.site.urls)),
)
