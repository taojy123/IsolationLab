"""isolation URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
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
from django.urls import path

from example import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index),
    path('info/', views.info),
    path('reset/', views.reset),
    path('add_100/', views.add_100),
    path('add_200/', views.add_200),
    path('add_100_atomic/', views.add_100_atomic),
    path('add_200_atomic/', views.add_200_atomic),
    path('add_300_atomic/', views.add_300_atomic),
    path('get_zhang3/', views.get_zhang3),
    path('get_zhang3_twice/', views.get_zhang3_twice),
    path('get_all_twice/', views.get_all_twice),
    path('add_people/', views.add_people),
]
