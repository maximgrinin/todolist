from django.conf import settings
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('core/', include(('core.urls', 'core'))),
    path('goals/', include(('goals.urls', 'goals'))),
    path('oauth/', include('social_django.urls', namespace='social')),
    path('bot/', include(('bot.urls', 'bot'))),
    path('admin/', admin.site.urls),
]

if settings.DEBUG:
    urlpatterns += [
        path('api-auth/', include('rest_framework.urls')),
    ]
