from django.shortcuts import render
from django.http import HttpResponse

def index(request):
    return HttpResponse("Bienvenue sur la page d'accueil !")