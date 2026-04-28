========================================
YMMO - DOCUMENTATION BASE DE DONNÉES
========================================

Projet : UF B2 INFRA & DEV - Ynov Informatique
Stack  : Python / Flask - MariaDB - Docker - Nginx

----------------------------------------
1. DESCRIPTION DE LA BASE DE DONNÉES
----------------------------------------

La base de données Ymmo contient 6 tables :

Table        | Enregistrements
-------------|----------------
agence       | 4
utilisateur  | 4
bien         | 4
annonce      | 4
photo        | 4
transaction  | 0

----------------------------------------
2. SCHÉMA RELATIONNEL
----------------------------------------

agence (1) ────────── (N) bien
utilisateur (1) ────── (N) bien  [agent]
bien (1) ──────────── (1) annonce
bien (1) ──────────── (N) photo
bien (1) ──────────── (N) transaction
utilisateur (1) ────── (N) transaction  [acheteur]

----------------------------------------
3. AGENCES ET AGENTS PAR AGENCE
----------------------------------------

Agence          | Nb agents
----------------|----------
Siege Ymmo      | 1
Ymmo Paris      | 1
Ymmo Lyon       | 0
Ymmo Marseille  | 0

Note : les 4 agences sont actives.
2 agences ont un agent assigné pour le moment.

----------------------------------------
4. VENTES PAR MOIS
----------------------------------------

Mois     | Nb biens ajoutés | Nb ventes
---------|------------------|----------
Mars     | 4                | 0

Note : Table transaction vide pour
l'instant...

----------------------------------------
5. DÉMARCHE DE TRAVAIL
----------------------------------------
Utilisation de MariaDB et de Heidisql pour une
meilleur visualisation de la data base.

========================================