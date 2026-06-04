from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from .models import Bien, Agence, Utilisateur, Favori, Offre, BienVu, Photo, Annonce
from . import db
from datetime import datetime

main = Blueprint('main', __name__)

# décos
def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get('user_role') != 'admin':
            return redirect(url_for('main.login'))
        return f(*args, **kwargs)
    return decorated

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('user_id'):
            return redirect(url_for('main.login'))
        return f(*args, **kwargs)
    return decorated

# page publique
@main.route('/')
def index():
    ville     = request.args.get('ville', '')
    type_bien = request.args.get('type', '')
    prix_max  = request.args.get('prix_max', '')
    statut    = request.args.get('statut', '')

    query = Bien.query
    if ville:
        query = query.filter(Bien.ville.ilike(f'%{ville}%'))
    if type_bien:
        query = query.filter_by(type=type_bien)
    if prix_max:
        query = query.filter(Bien.prix <= float(prix_max))
    if statut:
        query = query.filter_by(statut=statut)

    biens = query.order_by(Bien.id.desc()).all()

    # ids favoris client
    favoris_ids = []
    if session.get('user_role') == 'client':
        favoris = Favori.query.filter_by(client_id=session['user_id']).all()
        favoris_ids = [f.bien_id for f in favoris]

    return render_template('index.html', biens=biens, ville=ville,
                           type_bien=type_bien, prix_max=prix_max,
                           statut=statut, favoris_ids=favoris_ids)

# statistiques API
@main.route('/api/statistiques')
def api_statistiques():
    from sqlalchemy import func
    
    # Comptages
    total_biens = Bien.query.count()
    biens_disponibles = Bien.query.filter_by(statut='disponible').count()
    biens_vendus = Bien.query.filter_by(statut='vendu').count()
    biens_loues = Bien.query.filter_by(statut='loue').count()
    total_agences = Agence.query.count()
    total_utilisateurs = Utilisateur.query.count()
    
    # Prices
    prix_data = db.session.query(
        func.min(Bien.prix).label('min'),
        func.max(Bien.prix).label('max'),
        func.avg(Bien.prix).label('avg')
    ).first()
    
    prix_min = float(prix_data.min) if prix_data.min else 0
    prix_max = float(prix_data.max) if prix_data.max else 0
    prix_moyen = float(prix_data.avg) if prix_data.avg else 0
    
    # Répartition par type
    types_data = db.session.query(
        Bien.type, func.count(Bien.id).label('count')
    ).group_by(Bien.type).all()
    
    types_chart = {
        'labels': [t[0] for t in types_data],
        'values': [t[1] for t in types_data]
    }
    
    return jsonify({
        'total_biens': total_biens,
        'biens_disponibles': biens_disponibles,
        'biens_vendus': biens_vendus,
        'biens_loues': biens_loues,
        'total_agences': total_agences,
        'total_utilisateurs': total_utilisateurs,
        'prix_min': prix_min,
        'prix_max': prix_max,
        'prix_moyen': prix_moyen,
        'types': types_chart
    })

# détail bien
@main.route('/bien/<int:id>')
def detail_bien(id):
    bien = Bien.query.get_or_404(id)

    # historique
    if session.get('user_role') == 'client':
        deja_vu = BienVu.query.filter_by(
            client_id=session['user_id'], bien_id=id).first()
        if not deja_vu:
            vu = BienVu(client_id=session['user_id'], bien_id=id)
            db.session.add(vu)
            db.session.commit()
        else:
            deja_vu.vu_le = datetime.utcnow()
            db.session.commit()

    est_favori = False
    if session.get('user_role') == 'client':
        est_favori = Favori.query.filter_by(
            client_id=session['user_id'], bien_id=id).first() is not None

    return render_template('detail_bien.html', bien=bien, est_favori=est_favori)

# favoris
@main.route('/favori/<int:bien_id>/toggle', methods=['POST'])
@login_required
def toggle_favori(bien_id):
    existant = Favori.query.filter_by(
        client_id=session['user_id'], bien_id=bien_id).first()
    if existant:
        db.session.delete(existant)
        db.session.commit()
        return jsonify({'status': 'removed'})
    else:
        favori = Favori(client_id=session['user_id'], bien_id=bien_id)
        db.session.add(favori)
        db.session.commit()
        return jsonify({'status': 'added'})

# offre
@main.route('/bien/<int:bien_id>/offre', methods=['POST'])
@login_required
def faire_offre(bien_id):
    montant = request.form.get('montant')
    message = request.form.get('message', '')
    if montant:
        offre = Offre(
            client_id=session['user_id'],
            bien_id=bien_id,
            montant=float(montant),
            message=message
        )
        db.session.add(offre)
        db.session.commit()
        flash('Votre offre a été envoyée avec succès !')
    return redirect(url_for('main.detail_bien', id=bien_id))

# login
@main.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email    = request.form.get('email')
        password = request.form.get('password')
        user = Utilisateur.query.filter_by(email=email).first()
        if user and user.mot_de_passe == password:
            session['user_id']   = user.id
            session['user_role'] = user.role
            session['user_nom']  = user.prenom
            if user.role == 'admin':
                return redirect(url_for('main.admin'))
            elif user.role == 'client':
                return redirect(url_for('main.espace_client'))
            elif user.role == 'agent':
                return redirect(url_for('main.espace_agent'))
            else:
                return redirect(url_for('main.index'))
        flash('Email ou mot de passe incorrect.')
    return render_template('login.html')

@main.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('main.index'))

# espace client
@main.route('/client')
@login_required
def espace_client():
    client_id = session['user_id']

    favoris = Favori.query.filter_by(client_id=client_id).order_by(
        Favori.cree_le.desc()).all()
    biens_favoris = [f.bien for f in favoris]

    vus = BienVu.query.filter_by(client_id=client_id).order_by(
        BienVu.vu_le.desc()).limit(10).all()
    biens_vus = [v.bien for v in vus]

    offres = Offre.query.filter_by(client_id=client_id).order_by(
        Offre.cree_le.desc()).all()

    return render_template('client.html',
                           biens_favoris=biens_favoris,
                           biens_vus=biens_vus,
                           offres=offres)

# agent
def agent_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get('user_role') != 'agent':
            return redirect(url_for('main.login'))
        return f(*args, **kwargs)
    return decorated

@main.route('/agent')
@agent_required
def espace_agent():
    agent_id = session['user_id']
    # Offres sur les biens gérés par cet agent
    offres = Offre.query.join(Bien).filter(Bien.agent_id == agent_id).order_by(Offre.cree_le.desc()).all()
    return render_template('agent.html', offres=offres)

@main.route('/agent/offre/<int:id>/<statut>', methods=['POST'])
@agent_required
def agent_traiter_offre(id, statut):
    offre = Offre.query.get_or_404(id)
    bien = Bien.query.get(offre.bien_id)
    if bien.agent_id != session['user_id']:
        return redirect(url_for('main.espace_agent'))
    if statut in ['acceptee', 'refusee']:
        offre.statut = statut
        db.session.commit()
    return redirect(url_for('main.espace_agent'))

# admin
@main.route('/admin')
@admin_required
def admin():
    biens  = Bien.query.order_by(Bien.id).all()
    offres = Offre.query.order_by(Offre.cree_le.desc()).all()
    return render_template('admin.html', biens=biens, offres=offres)

@main.route('/admin/bien/<int:id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_bien(id):
    bien    = Bien.query.get_or_404(id)
    agences = Agence.query.all()
    if request.method == 'POST':
        bien.titre       = request.form.get('titre')
        bien.type        = request.form.get('type')
        bien.prix        = float(request.form.get('prix'))
        bien.surface     = float(request.form.get('surface') or 0)
        bien.ville       = request.form.get('ville')
        bien.adresse     = request.form.get('adresse')
        bien.nb_pieces   = int(request.form.get('nb_pieces') or 0)
        bien.description = request.form.get('description')
        bien.statut      = request.form.get('statut')
        db.session.commit()
        return redirect(url_for('main.admin'))
    return render_template('edit_bien.html', bien=bien, agences=agences)

@main.route('/admin/bien/<int:id>/delete', methods=['POST'])
@admin_required
def delete_bien(id):
    bien = Bien.query.get_or_404(id)
    Photo.query.filter_by(bien_id=id).delete()
    Annonce.query.filter_by(bien_id=id).delete()
    Favori.query.filter_by(bien_id=id).delete()
    Offre.query.filter_by(bien_id=id).delete()
    BienVu.query.filter_by(bien_id=id).delete()
    db.session.delete(bien)
    db.session.commit()
    return redirect(url_for('main.admin'))

@main.route('/admin/offre/<int:id>/<statut>', methods=['POST'])
@admin_required
def traiter_offre(id, statut):
    offre = Offre.query.get_or_404(id)
    if statut in ['acceptee', 'refusee']:
        offre.statut = statut
        db.session.commit()
    return redirect(url_for('main.admin'))