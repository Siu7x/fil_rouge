from . import db
from datetime import datetime

class Agence(db.Model):
    __tablename__ = 'agence'
    id        = db.Column(db.Integer, primary_key=True)
    nom       = db.Column(db.String(100), nullable=False)
    adresse   = db.Column(db.String(255))
    ville     = db.Column(db.String(100))
    telephone = db.Column(db.String(20))
    est_siege = db.Column(db.Boolean, default=False)
    cree_le   = db.Column(db.DateTime, default=datetime.utcnow)

class Utilisateur(db.Model):
    __tablename__ = 'utilisateur'
    id           = db.Column(db.Integer, primary_key=True)
    nom          = db.Column(db.String(100), nullable=False)
    prenom       = db.Column(db.String(100), nullable=False)
    email        = db.Column(db.String(150), nullable=False, unique=True)
    mot_de_passe = db.Column(db.String(255), nullable=False)
    role         = db.Column(db.Enum('client','agent','admin'), default='client')
    telephone    = db.Column(db.String(20))
    agence_id    = db.Column(db.Integer, db.ForeignKey('agence.id'), nullable=True)
    cree_le      = db.Column(db.DateTime, default=datetime.utcnow)

class Bien(db.Model):
    __tablename__ = 'bien'
    id          = db.Column(db.Integer, primary_key=True)
    titre       = db.Column(db.String(200), nullable=False)
    type        = db.Column(db.Enum('appartement','maison','bureau','commerce','terrain'))
    prix        = db.Column(db.Numeric(12,2), nullable=False)
    surface     = db.Column(db.Numeric(8,2))
    ville       = db.Column(db.String(100))
    adresse     = db.Column(db.String(255))
    nb_pieces   = db.Column(db.Integer)
    description = db.Column(db.Text)
    statut      = db.Column(db.Enum('disponible','vendu','loue','archive'), default='disponible')
    agence_id   = db.Column(db.Integer, db.ForeignKey('agence.id'), nullable=True)
    agent_id    = db.Column(db.Integer, db.ForeignKey('utilisateur.id'), nullable=True)
    cree_le     = db.Column(db.DateTime, default=datetime.utcnow)

class Annonce(db.Model):
    __tablename__ = 'annonce'
    id          = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.Text)
    publiee_le  = db.Column(db.DateTime, default=datetime.utcnow)
    active      = db.Column(db.Boolean, default=True)
    bien_id     = db.Column(db.Integer, db.ForeignKey('bien.id'), nullable=False, unique=True)

class Photo(db.Model):
    __tablename__ = 'photo'
    id      = db.Column(db.Integer, primary_key=True)
    url     = db.Column(db.String(500), nullable=False)
    ordre   = db.Column(db.Integer, default=0)
    bien_id = db.Column(db.Integer, db.ForeignKey('bien.id'), nullable=False)

class Transaction(db.Model):
    __tablename__ = 'transaction'
    id          = db.Column(db.Integer, primary_key=True)
    type        = db.Column(db.Enum('vente','location'), nullable=False)
    prix_final  = db.Column(db.Numeric(12,2), nullable=False)
    date_trans  = db.Column(db.DateTime, default=datetime.utcnow)
    bien_id     = db.Column(db.Integer, db.ForeignKey('bien.id'), nullable=False)
    acheteur_id = db.Column(db.Integer, db.ForeignKey('utilisateur.id'), nullable=True)
    agent_id    = db.Column(db.Integer, db.ForeignKey('utilisateur.id'), nullable=True)