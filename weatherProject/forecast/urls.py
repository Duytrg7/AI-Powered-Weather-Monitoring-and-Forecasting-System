from django.urls import path
from . import views

urlpatterns = [
    path('', views.weather_view, name='Weather View'),
    path('api/sensor/', views.receive_sensor_data, name='Sensor Data'),
    path('api/retrain/', views.retrain_models, name='Retrain Models'),
]
