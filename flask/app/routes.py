from flask import Blueprint, render_template, request
from .models import Bien, Agence
from . import db

main = Blueprint('main', __name__)

@main.route('/')
def index():
    ville = request.args.get('ville', '')
    type_bien = request.args.get('type', '')
    prix_max = request.args.get('prix_max', '')

    query = Bien.query.filter_by(statut='disponible')

    if ville:
        query = query.filter(Bien.ville.ilike(f'%{ville}%'))
    if type_bien:
        query = query.filter_by(type=type_bien)
    if prix_max:
        query = query.filter(Bien.prix <= float(prix_max))

    biens = query.all()
    return render_template('index.html', biens=biens, ville=ville, type_bien=type_bien, prix_max=prix_max)

@main.route('/stats')
def stats():
    biens = Bien.query.all()
    
    villes = {}
    for b in biens:
        villes[b.ville] = villes.get(b.ville, 0) + 1

    return render_template('stats.html', villes=villes)