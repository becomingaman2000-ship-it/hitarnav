from django.urls import path
from . import views

urlpatterns = [
    path('ar-indoor-navigator/', views.ar_indoor_navigator, name='ar_indoor_navigator'),
    path('analyze-rooms/', views.analyze_rooms, name='analyze_rooms'),
    path('room-map/', views.room_map, name='room_map'),
    path('api/upload-rooms/', views.upload_rooms, name='upload_rooms'),
    path('api/clear-rooms/', views.clear_rooms, name='clear_rooms'),
    path('api/rooms-count/', views.rooms_count, name='rooms_count'),
    path('api/get-rooms/', views.get_rooms, name='get_rooms'),
]