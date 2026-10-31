"""
Authentification simple et sans dépendance externe.

- Comptes stockés dans data/users.db (SQLite)
- Mots de passe hachés avec PBKDF2-SHA256 (200 000 itérations + sel aléatoire)
- Jeton de session signé HMAC-SHA256 (format proche d'un JWT), avec date d'expiration
- Connexion Google optionnelle (si FV_GOOGLE_CLIENT_ID est défini)

Variables d'environnement :
  FV_SECRET_KEY         clé de signature des jetons (générée et sauvegardée sinon)
  FV_ADMIN_EMAIL        compte admin créé au premier lancement (défaut admin@cires.ma)
  FV_ADMIN_PASSWORD     mot de passe de ce compte (défaut Admin@2026)
  FV_GOOGLE_CLIENT_ID   identifiant OAuth Google (facultatif)
"""
import base64
import hashlib
import hmac
import json
import os
import secrets
import sqlite3
import time
import urllib.parse
import urllib.request
from pathlib import Path

from fastapi import Depends, HTTPException, Request

DATA_DIR = Path(os.environ.get("FV_DATA_DIR", Path(__file__).resolve().parent.parent / "data"))
DB_PATH = DATA_DIR / "users.db"
SECRET_FILE = DATA_DIR / ".secret_key"

SESSION_HOURS = 12            # sans « Se souvenir de moi »
REMEMBER_DAYS = 30            # avec « Se souvenir de moi »
GOOGLE_CLIENT_ID = os.environ.get("FV_GOOGLE_CLIENT_ID", "")


# ---------- Clé secrète ----------
def _secret() -> bytes:
    env = os.environ.get("FV_SECRET_KEY")
    if env:
        return env.encode()
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not SECRET_FILE.exists():
        SECRET_FILE.write_text(secrets.token_hex(32))
    return SECRET_FILE.read_text().strip().encode()


# ---------- Base des utilisateurs ----------
def _db():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    con.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL DEFAULT '',
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'user',
        created_at REAL NOT NULL
    )""")
    return con


def hash_password(password: str, salt: bytes = None) -> str:
    salt = salt or secrets.token_bytes(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 200_000)
    return f"pbkdf2_sha256$200000${salt.hex()}${dk.hex()}"


def check_password(password: str, stored: str) -> bool:
    try:
        _, iters, salt, digest = stored.split("$")
        dk = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), int(iters))
        return hmac.compare_digest(dk.hex(), digest)
    except ValueError:
        return False


def create_user(email: str, password: str, name: str = "", role: str = "user"):
    email = email.strip().lower()
    if len(password) < 8:
        raise ValueError("Le mot de passe doit contenir au moins 8 caractères")
    with _db() as con:
        con.execute(
            "INSERT INTO users (email, name, password_hash, role, created_at) VALUES (?, ?, ?, ?, ?)",
            (email, name or email.split("@")[0], hash_password(password), role, time.time()),
        )


def set_password(email: str, password: str):
    with _db() as con:
        n = con.execute("UPDATE users SET password_hash = ? WHERE email = ?",
                        (hash_password(password), email.strip().lower())).rowcount
    if not n:
        raise ValueError("Utilisateur introuvable")


def get_user(email: str):
    with _db() as con:
        row = con.execute("SELECT * FROM users WHERE email = ?", (email.strip().lower(),)).fetchone()
    return dict(row) if row else None


def list_users():
    with _db() as con:
        return [dict(r) for r in con.execute("SELECT id, email, name, role FROM users ORDER BY id")]


def ensure_admin():
    """Crée le compte administrateur au premier lancement."""
    with _db() as con:
        if con.execute("SELECT COUNT(*) FROM users").fetchone()[0]:
            return
    email = os.environ.get("FV_ADMIN_EMAIL", "admin@cires.ma")
    password = os.environ.get("FV_ADMIN_PASSWORD", "Admin@2026")
    create_user(email, password, "Administrateur", "admin")
    print(f"Compte administrateur créé : {email}  (changez le mot de passe : python create_user.py)")


# ---------- Jetons ----------
def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _unb64(s: str) -> bytes:
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


def make_token(user: dict, remember: bool = False) -> tuple[str, int]:
    exp = int(time.time() + (REMEMBER_DAYS * 86400 if remember else SESSION_HOURS * 3600))
    payload = _b64(json.dumps({"sub": user["email"], "role": user["role"], "exp": exp}).encode())
    sig = _b64(hmac.new(_secret(), payload.encode(), hashlib.sha256).digest())
    return f"{payload}.{sig}", exp


def read_token(token: str):
    try:
        payload, sig = token.split(".")
        expected = _b64(hmac.new(_secret(), payload.encode(), hashlib.sha256).digest())
        if not hmac.compare_digest(sig, expected):
            return None
        data = json.loads(_unb64(payload))
        if data["exp"] < time.time():
            return None
        return data
    except Exception:
        return None


# ---------- Dépendance FastAPI ----------
def current_user(request: Request) -> dict:
    """Exige un jeton valide (en-tête Authorization: Bearer … ou ?token= pour les images)."""
    header = request.headers.get("Authorization", "")
    token = header[7:] if header.startswith("Bearer ") else request.query_params.get("token", "")
    data = read_token(token) if token else None
    user = get_user(data["sub"]) if data else None
    if not user:
        raise HTTPException(401, "Session expirée ou invalide. Veuillez vous reconnecter.")
    return {"email": user["email"], "name": user["name"], "role": user["role"]}


require_user = Depends(current_user)


# ---------- Google (facultatif) ----------
def verify_google(credential: str) -> str:
    """Vérifie un ID token Google et renvoie l'e-mail (compte déjà créé obligatoire)."""
    if not GOOGLE_CLIENT_ID:
        raise HTTPException(501, "Connexion Google non configurée sur le serveur")
    url = "https://oauth2.googleapis.com/tokeninfo?" + urllib.parse.urlencode({"id_token": credential})
    try:
        with urllib.request.urlopen(url, timeout=10) as r:
            info = json.loads(r.read())
    except Exception:
        raise HTTPException(401, "Jeton Google invalide")
    if info.get("aud") != GOOGLE_CLIENT_ID or info.get("email_verified") not in ("true", True):
        raise HTTPException(401, "Jeton Google invalide")
    return info["email"]
