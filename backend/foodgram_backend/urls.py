"""Модуль головного маршрутизатора проекта."""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path, re_path

from recipes.views import recipe_shortlinked_retreave

urlpatterns = [
    path('api/', include('api.urls')),
    path('admin/', admin.site.urls),
    path(r's/<slug:short_link>', recipe_shortlinked_retreave,
         name='recipe_shortlinked_retreave'),
#    re_path(r's/(?P<short_link>[\w]{5})', recipe_shortlinked_retreave,
#            name='recipe_shortlinked_retreave'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
