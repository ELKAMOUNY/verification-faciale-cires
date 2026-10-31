# Système de reconnaissance faciale

Plateforme de **vérification (1:1)** et d'**identification (1:N)** de visages : Notebook + Backend FastAPI + Frontend React.

## Architecture

```
Systéme de reconnaissance faciale/
├── backend/          API FastAPI (Python)
│   ├── main.py           routes de l'API
│   ├── detection.py      YuNet : détection du visage
│   ├── embeddings.py     SFace : visage → vecteur de 128 nombres
│   ├── verification.py   comparaison, identification, évaluation
│   ├── auth.py           comptes et connexion
│   ├── create_user.py    gestion des comptes
│   └── models/           modèles d'IA (ONNX)
├── frontend/         Interface web React (Vite)
├── data/             photos : reference/ (galerie) et test/ (évaluation)
├── notebooks/        analyse : courbe ROC, EER, choix du seuil
├── mes photo/        photos personnelles (reference/ et test/)
└── tests/            tests automatiques (pytest)
```

**Fonctionnement :** le frontend envoie la photo à l'API → YuNet détecte le visage → SFace le transforme en vecteur → comparaison par similarité cosinus. Score ≥ **0.363** = même personne.

```
Navigateur (React, port 5173)  ⇄  API FastAPI (port 8000)  ⇄  modèles ONNX + data/
```

## Démarrer

Deux fenêtres cmd, à laisser ouvertes.

**1. Backend**

```bash
cd /d "C:\Users\pc\Desktop\app finaliser\Systéme de reconnaissance faciale\backend"
venv\Scripts\activate
python -m uvicorn main:app --reload --port 8000
```

Attendre `Application startup complete.`

**2. Frontend**

```bash
cd /d "C:\Users\pc\Desktop\app finaliser\Systéme de reconnaissance faciale\frontend"
npm run dev
```

**3. Navigateur :** ouvrir http://localhost:5173

## Connexion

| E-mail | Rôle |
|---|---|
| `f.elkamouny@gmail.com` | administratrice |

Changer le mot de passe :

```bash
cd /d "C:\Users\pc\Desktop\app finaliser\Systéme de reconnaissance faciale\backend"
venv\Scripts\activate
python create_user.py password f.elkamouny@gmail.com
```

## Pages de l'application

| Page | Rôle |
|---|---|
| Vérification 1:1 | « Cette photo est-elle bien cette personne ? » |
| Identification 1:N | « Qui est sur cette photo ? » |
| Galerie | voir les personnes, en ajouter une |
| Évaluation | précision, FAR, FRR, choix du seuil |

## Important

- Ne pas déplacer le dossier du projet (le venv ne fonctionnerait plus).
- Les photos restent sur le PC : rien n'est envoyé sur Internet.
"# systeme-reconnaissance-faciale" 
