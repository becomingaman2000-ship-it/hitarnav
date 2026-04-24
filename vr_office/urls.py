"""
URL configuration for vr_office project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponseRedirect, JsonResponse


def _chrome_devtools_json(request):
    # Respond with an empty JSON object so Chrome's devtools request returns 200.
    return JsonResponse({})

urlpatterns = [
    path('admin/', admin.site.urls),
    path('.well-known/appspecific/com.chrome.devtools.json', _chrome_devtools_json),
    path('', lambda request: HttpResponseRedirect('/ar-indoor-navigator/')),
    path('', include('navigator.urls')),
]
