from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
    path('states/', views.StatesListView.as_view(), name='states-list'),
    path('<loc_type>/<loc_id>/', views.geo_map, name='geo_map'),
    path('<latitude>/<longitude>/', views.map_view, name='map_view')
]
