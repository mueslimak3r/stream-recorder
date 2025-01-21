from django.urls import include, path
from django.conf import settings as conf_settings
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path('admin/', admin.site.urls),
]
if conf_settings.DEBUG == True:
    urlpatterns.append(path("__reload__/", include("django_browser_reload.urls")))
    urlpatterns.extend(static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT))