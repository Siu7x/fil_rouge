from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from .models import Bien, Agence, Utilisateur, Favori, Offre, BienVu, Photo, Annonce
from . import db
from datetime import datetime
from sqlalchemy import text
import bcrypt

main = Blueprint('main', __name__)

# ── Décorateurs ───────────────────────────────────────────────────────────────

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

def agent_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get('user_role') != 'agent':
            return redirect(url_for('main.login'))
        return f(*args, **kwargs)
    return decorated

# ── Page publique ─────────────────────────────────────────────────────────────

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

    favoris_ids = []
    if session.get('user_role') == 'client':
        favoris = Favori.query.filter_by(client_id=session['user_id']).all()
        favoris_ids = [f.bien_id for f in favoris]

    return render_template('index.html', biens=biens, ville=ville,
                           type_bien=type_bien, prix_max=prix_max,
                           statut=statut, favoris_ids=favoris_ids)

# ── API statistiques ──────────────────────────────────────────────────────────

@main.route('/api/statistiques')
def api_statistiques():
    from sqlalchemy import func

    total_biens       = Bien.query.count()
    biens_disponibles = Bien.query.filter_by(statut='disponible').count()
    biens_vendus      = Bien.query.filter_by(statut='vendu').count()
    biens_loues       = Bien.query.filter_by(statut='loue').count()
    total_agences     = Agence.query.count()
    total_utilisateurs = Utilisateur.query.count()

    prix_data = db.session.query(
        func.min(Bien.prix).label('min'),
        func.max(Bien.prix).label('max'),
        func.avg(Bien.prix).label('avg')
    ).first()

    prix_min   = float(prix_data.min)  if prix_data.min  else 0
    prix_max   = float(prix_data.max)  if prix_data.max  else 0
    prix_moyen = float(prix_data.avg)  if prix_data.avg  else 0

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

# ── Détail bien ───────────────────────────────────────────────────────────────

@main.route('/bien/<int:id>')
def detail_bien(id):
    bien = Bien.query.get_or_404(id)

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

# ── Favoris ───────────────────────────────────────────────────────────────────

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

# ── Offre ─────────────────────────────────────────────────────────────────────

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

# ── Login ─────────────────────────────────────────────────────────────────────

@main.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email    = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        user = db.session.execute(
            text("SELECT id, nom, prenom, role, mot_de_passe FROM utilisateur WHERE email = :email"),
            {"email": email}
        ).fetchone()

        if not user or not bcrypt.checkpw(
            password.encode('utf-8'),
            user.mot_de_passe.encode('utf-8')
        ):
            flash("Email ou mot de passe incorrect.")
            return redirect(url_for('main.login'))

        session['user_id']   = user.id
        session['user_role'] = user.role
        session['user_nom']  = f"{user.prenom} {user.nom}"

        if user.role == 'admin':
            return redirect(url_for('main.admin'))
        elif user.role == 'agent':
            return redirect(url_for('main.espace_agent'))
        else:
            return redirect(url_for('main.index'))

    return render_template('login.html')

# ── Register ──────────────────────────────────────────────────────────────────

@main.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        nom              = request.form.get('nom', '').strip()
        prenom           = request.form.get('prenom', '').strip()
        email            = request.form.get('email', '').strip().lower()
        telephone        = request.form.get('telephone', '').strip()
        password         = request.form.get('password', '')
        password_confirm = request.form.get('password_confirm', '')

        if not nom or not prenom or not email:
            flash("Nom, prénom et email sont obligatoires.")
            return redirect(url_for('main.register'))

        if len(password) < 8:
            flash("Le mot de passe doit contenir au moins 8 caractères.")
            return redirect(url_for('main.register'))

        if password != password_confirm:
            flash("Les mots de passe ne correspondent pas.")
            return redirect(url_for('main.register'))

        existing = db.session.execute(
            text("SELECT id FROM utilisateur WHERE email = :email"),
            {"email": email}
        ).fetchone()

        if existing:
            flash("Un compte avec cet email existe déjà.")
            return redirect(url_for('main.register'))

        hashed = bcrypt.hashpw(
            password.encode('utf-8'),
            bcrypt.gensalt(rounds=12)
        ).decode('utf-8')

        db.session.execute(
            text("""INSERT INTO utilisateur (nom, prenom, email, mot_de_passe, role, telephone, agence_id)
                    VALUES (:nom, :prenom, :email, :mdp, 'client', :tel, NULL)"""),
            {"nom": nom, "prenom": prenom, "email": email,
             "mdp": hashed, "tel": telephone or None}
        )
        db.session.commit()

        new_user = db.session.execute(
            text("SELECT id, nom, prenom FROM utilisateur WHERE email = :email"),
            {"email": email}
        ).fetchone()

        session['user_id']   = new_user.id
        session['user_role'] = 'client'
        session['user_nom']  = f"{new_user.prenom} {new_user.nom}"

        return redirect(url_for('main.index'))

    return render_template('register.html')

# ── Logout ────────────────────────────────────────────────────────────────────

@main.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('main.index'))

# ── Espace client ─────────────────────────────────────────────────────────────

@main.route('/client')
@login_required
def espace_client():
    client_id = session['user_id']

    favoris      = Favori.query.filter_by(client_id=client_id).order_by(Favori.cree_le.desc()).all()
    biens_favoris = [f.bien for f in favoris]

    vus       = BienVu.query.filter_by(client_id=client_id).order_by(BienVu.vu_le.desc()).limit(10).all()
    biens_vus = [v.bien for v in vus]

    offres = Offre.query.filter_by(client_id=client_id).order_by(Offre.cree_le.desc()).all()

    return render_template('client.html',
                           biens_favoris=biens_favoris,
                           biens_vus=biens_vus,
                           offres=offres)

# ── Espace agent ──────────────────────────────────────────────────────────────

@main.route('/agent')
@agent_required
def espace_agent():
    agent_id = session['user_id']

    # Infos agent + agence
    agent_info = db.session.execute(
        text("""
            SELECT u.nom, u.prenom, u.agence_id,
                   a.nom AS agence_nom, a.ville AS agence_ville
            FROM utilisateur u
            JOIN agence a ON u.agence_id = a.id
            WHERE u.id = :id
        """),
        {"id": agent_id}
    ).fetchone()

    # Biens de l'agence (pas seulement de l'agent)
    biens = Bien.query.filter_by(agence_id=agent_info.agence_id).order_by(Bien.id.desc()).all()

    # Offres sur les biens gérés par cet agent
    offres = Offre.query.join(Bien).filter(
        Bien.agent_id == agent_id
    ).order_by(Offre.cree_le.desc()).all()

    return render_template('agent.html',
                           offres=offres,
                           biens=biens,
                           agence_nom=agent_info.agence_nom,
                           agence_ville=agent_info.agence_ville,
                           agence_id=agent_info.agence_id)

# ── Agent : traiter une offre ─────────────────────────────────────────────────

@main.route('/agent/offre/<int:id>/<statut>', methods=['POST'])
@agent_required
def agent_traiter_offre(id, statut):
    offre = Offre.query.get_or_404(id)
    bien  = Bien.query.get(offre.bien_id)
    if bien.agent_id != session['user_id']:
        return redirect(url_for('main.espace_agent'))
    if statut in ['acceptee', 'refusee']:
        offre.statut = statut
        db.session.commit()
    return redirect(url_for('main.espace_agent'))

# ── Agent : modifier un bien de son agence ────────────────────────────────────

@main.route('/agent/bien/<int:id>/edit', methods=['GET', 'POST'])
@agent_required
def agent_edit_bien(id):
    bien      = Bien.query.get_or_404(id)
    agent_id  = session['user_id']

    # Vérifier que le bien appartient bien à l'agence de l'agent
    agent_info = db.session.execute(
        text("SELECT agence_id FROM utilisateur WHERE id = :id"),
        {"id": agent_id}
    ).fetchone()

    if bien.agence_id != agent_info.agence_id:
        flash("Vous n'avez pas accès à ce bien.")
        return redirect(url_for('main.espace_agent'))

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
        flash('Bien modifié avec succès.')
        return redirect(url_for('main.espace_agent'))

    return render_template('edit_bien_agent.html', bien=bien)

# ── Admin ─────────────────────────────────────────────────────────────────────

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