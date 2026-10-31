"""
API de vérification faciale (FastAPI).

Lancer :  uvicorn main:app --reload --port 8000
Docs interactives : http://127.0.0.1:8000/docs
"""
import os
from typing import List

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

import auth
import verification as V
from detection import box, decode_image, detect
from embeddings import embed_face, embed_image
from pydantic import BaseModel

app = FastAPI(title="Vérification faciale", version="1.0")
# Autorise le frontend sur n'importe quel port local (5173, 5174, 3000…)
# + origines supplémentaires via FV_CORS_ORIGINS="https://mon-site.ma,https://autre.ma"
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1|\[::1\])(:\d+)?",
    allow_origins=[o.strip() for o in os.environ.get("FV_CORS_ORIGINS", "").split(",") if o.strip()],
    allow_methods=["*"],
    allow_headers=["*"],
)

auth.ensure_admin()
gallery = V.Gallery()

_n_faces = sum(len(p["embs"]) for p in gallery.persons.values())
print(f"Galerie : {len(gallery.persons)} personne(s), {_n_faces} visage(s) de référence — dossier {V.REF_DIR}")
if gallery.persons and _n_faces == 0:
    print("ATTENTION : aucun visage chargé. Supprimez le dossier data\\.cache puis relancez.")


async def _read(file: UploadFile):
    try:
        return decode_image(await file.read())
    except ValueError:
        raise HTTPException(400, f"Image illisible : {file.filename}")


def _embed_or_400(img, label="l'image"):
    emb, face = embed_image(img)
    if emb is None:
        raise HTTPException(422, f"Aucun visage détecté dans {label}")
    return emb, face


# ---------- Authentification ----------
class LoginIn(BaseModel):
    email: str
    password: str
    remember: bool = False


class GoogleIn(BaseModel):
    credential: str
    remember: bool = False


def _session(user, remember):
    token, exp = auth.make_token(user, remember)
    return {"token": token, "expires": exp,
            "user": {"email": user["email"], "name": user["name"], "role": user["role"]}}


@app.post("/api/auth/login")
def login(body: LoginIn):
    user = auth.get_user(body.email)
    if not user or not auth.check_password(body.password, user["password_hash"]):
        raise HTTPException(401, "E-mail ou mot de passe incorrect")
    return _session(user, body.remember)


@app.post("/api/auth/google")
def login_google(body: GoogleIn):
    user = auth.get_user(auth.verify_google(body.credential))
    if not user:
        raise HTTPException(403, "Ce compte Google n'est pas autorisé. Contactez l'administrateur.")
    return _session(user, body.remember)


@app.get("/api/auth/config")
def auth_config():
    return {"google_client_id": auth.GOOGLE_CLIENT_ID or None}


@app.get("/api/auth/me")
def me(user: dict = Depends(auth.current_user)):
    return user


# ---------- Infos ----------
@app.get("/api/health")
def health():
    return {"status": "ok", "persons": len(gallery.persons), "threshold": V.THRESHOLD}


@app.get("/api/persons", dependencies=[auth.require_user])
def persons():
    return [
        {
            "id": pid,
            "name": p["name"],
            "n_images": len(p["images"]),
            "n_faces": len(p["embs"]),
            "images": [f.name for f in p["images"]],
        }
        for pid, p in gallery.persons.items()
    ]


@app.get("/api/persons/{person_id}/images/{filename}", dependencies=[auth.require_user])
def person_image(person_id: str, filename: str):
    p = gallery.persons.get(person_id)
    match = [f for f in (p["images"] if p else []) if f.name == filename]
    if not match:
        raise HTTPException(404, "Image introuvable")
    return FileResponse(match[0])


@app.post("/api/persons", dependencies=[auth.require_user])
async def add_person(name: str = Form(...), files: List[UploadFile] = File(...)):
    imgs = [await _read(f) for f in files]
    pid, saved = gallery.add_person(name.strip(), imgs)
    if not pid:
        raise HTTPException(422, "Aucun visage détecté dans les images envoyées")
    return {"id": pid, "name": name.strip(), "saved": saved, "rejected": len(imgs) - saved}


@app.post("/api/reload", dependencies=[auth.require_user])
def reload():
    gallery.reload()
    return {"persons": len(gallery.persons)}


# ---------- Détection ----------
@app.post("/api/detect", dependencies=[auth.require_user])
async def detect_faces(file: UploadFile = File(...)):
    img = await _read(file)
    faces = detect(img)
    return {
        "width": img.shape[1], "height": img.shape[0],
        "faces": [{"box": box(f), "score": round(float(f[14]), 3),
                   "landmarks": [[round(float(f[4 + 2 * k])), round(float(f[5 + 2 * k]))] for k in range(5)]}
                  for f in faces],
    }


# ---------- Vérification 1:1 ----------
@app.post("/api/verify", dependencies=[auth.require_user])
async def verify(person_id: str = Form(...), file: UploadFile = File(...)):
    """La photo correspond-elle à la personne déclarée ?"""
    if person_id not in gallery.persons:
        raise HTTPException(404, "Personne inconnue")
    img = await _read(file)
    emb, face = _embed_or_400(img)
    res = gallery.verify(emb, person_id)
    return {**res, "person_id": person_id, "name": gallery.persons[person_id]["name"],
            "threshold": V.THRESHOLD, "box": box(face), "width": img.shape[1], "height": img.shape[0]}


@app.post("/api/compare", dependencies=[auth.require_user])
async def compare(file1: UploadFile = File(...), file2: UploadFile = File(...)):
    """Les deux photos montrent-elles la même personne ?"""
    e1, _ = _embed_or_400(await _read(file1), "la photo 1")
    e2, _ = _embed_or_400(await _read(file2), "la photo 2")
    return {**V.cosine_between(e1, e2), "threshold": V.THRESHOLD}


# ---------- Identification 1:N ----------
@app.post("/api/identify", dependencies=[auth.require_user])
async def identify(file: UploadFile = File(...)):
    """Qui est (sont) sur la photo ? Tous les visages sont analysés."""
    img = await _read(file)
    faces = detect(img)
    if len(faces) == 0:
        raise HTTPException(422, "Aucun visage détecté")
    results = []
    for f in faces:
        r = gallery.identify(embed_face(img, f))
        results.append({"box": box(f), **r})
    return {"faces": results, "threshold": V.THRESHOLD, "width": img.shape[1], "height": img.shape[0]}


# ---------- Évaluation ----------
@app.get("/api/evaluate", dependencies=[auth.require_user])
def evaluate(threshold: float = V.THRESHOLD):
    res = V.evaluate(gallery, threshold)
    if "error" in res:
        raise HTTPException(400, res["error"])
    return res
