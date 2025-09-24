from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),  # Exemple de route d'accueil
]