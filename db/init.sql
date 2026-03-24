CREATE DATABASE IF NOT EXISTS ymmo CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE ymmo;

CREATE TABLE agence (
    id        INT AUTO_INCREMENT PRIMARY KEY,
    nom       VARCHAR(100) NOT NULL,
    adresse   VARCHAR(255),
    ville     VARCHAR(100),
    telephone VARCHAR(20),
    est_siege BOOLEAN DEFAULT FALSE,
    cree_le   DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE utilisateur (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    nom          VARCHAR(100) NOT NULL,
    prenom       VARCHAR(100) NOT NULL,
    email        VARCHAR(150) NOT NULL UNIQUE,
    mot_de_passe VARCHAR(255) NOT NULL,
    role         ENUM('client','agent','admin') DEFAULT 'client',
    telephone    VARCHAR(20),
    agence_id    INT,
    cree_le      DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (agence_id) REFERENCES agence(id) ON DELETE SET NULL
);

CREATE TABLE bien (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    titre       VARCHAR(200) NOT NULL,
    type        ENUM('appartement','maison','bureau','commerce','terrain'),
    prix        DECIMAL(12,2) NOT NULL,
    surface     DECIMAL(8,2),
    ville       VARCHAR(100),
    adresse     VARCHAR(255),
    nb_pieces   INT,
    description TEXT,
    statut      ENUM('disponible','vendu','loue','archive') DEFAULT 'disponible',
    agence_id   INT,
    agent_id    INT,
    cree_le     DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (agence_id) REFERENCES agence(id) ON DELETE SET NULL,
    FOREIGN KEY (agent_id)  REFERENCES utilisateur(id) ON DELETE SET NULL
);

CREATE TABLE annonce (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    description TEXT,
    publiee_le  DATETIME DEFAULT CURRENT_TIMESTAMP,
    active      BOOLEAN DEFAULT TRUE,
    bien_id     INT NOT NULL UNIQUE,
    FOREIGN KEY (bien_id) REFERENCES bien(id) ON DELETE CASCADE
);

CREATE TABLE photo (
    id      INT AUTO_INCREMENT PRIMARY KEY,
    url     VARCHAR(500) NOT NULL,
    ordre   INT DEFAULT 0,
    bien_id INT NOT NULL,
    FOREIGN KEY (bien_id) REFERENCES bien(id) ON DELETE CASCADE
);

CREATE TABLE transaction (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    type        ENUM('vente','location') NOT NULL,
    prix_final  DECIMAL(12,2) NOT NULL,
    date_trans  DATETIME DEFAULT CURRENT_TIMESTAMP,
    bien_id     INT NOT NULL,
    acheteur_id INT,
    agent_id    INT,
    FOREIGN KEY (bien_id)     REFERENCES bien(id) ON DELETE RESTRICT,
    FOREIGN KEY (acheteur_id) REFERENCES utilisateur(id) ON DELETE SET NULL,
    FOREIGN KEY (agent_id)    REFERENCES utilisateur(id) ON DELETE SET NULL
);