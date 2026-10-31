"""
Vérification (1:1) et identification (1:N) à partir des images de référence.

  data/reference/person_001/img_01.jpg   -> galerie (identités connues)
  data/test/person_001/img_04.jpg        -> images de test (évaluation)
  data/persons.json                      -> {"person_001": "Nom réel", ...}
"""
import json
import os
import re
from pathlib import Path

import cv2
import numpy as np

from detection import imread_unicode, imwrite_unicode
from embeddings import cosine, embed_image

DATA_DIR = Path(os.environ.get("FV_DATA_DIR", Path(__file__).resolve().parent.parent / "data"))
REF_DIR = DATA_DIR / "reference"
TEST_DIR = DATA_DIR / "test"
CACHE_DIR = DATA_DIR / ".cache"
IMG_EXT = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

# Seuil cosinus recommandé pour SFace (OpenCV Zoo). Au-dessus : même personne.
THRESHOLD = float(os.environ.get("FV_THRESHOLD", 0.363))


# ---------- Lecture du dataset ----------
def person_names():
    f = DATA_DIR / "persons.json"
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}


def list_images(root: Path):
    """{person_id: [chemins triés]} pour root/person_xxx/*.jpg"""
    out = {}
    if not root.exists():
        return out
    for d in sorted(p for p in root.iterdir() if p.is_dir()):
        imgs = sorted(f for f in d.iterdir() if f.suffix.lower() in IMG_EXT)
        if imgs:
            out[d.name] = imgs
    return out


def embed_files(paths, cache_name):
    """Embeddings des fichiers, avec cache disque (recalcul si le fichier change)."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file = CACHE_DIR / f"{cache_name}.npz"
    cache = {}
    if cache_file.exists():
        z = np.load(cache_file, allow_pickle=True)
        cache = dict(zip(z["keys"].tolist(), z["embs"]))
    result, changed, keys = {}, False, []
    for p in paths:
        key = f"{p}|{p.stat().st_mtime_ns}"
        if key in cache and np.any(cache[key]):
            emb = cache[key]          # visage déjà calculé
        else:                         # nouveau fichier, ou « aucun visage » mémorisé : on recalcule
            img = imread_unicode(p)
            if img is None:
                continue  # fichier illisible : on ne mémorise rien, nouvel essai la prochaine fois
            emb, _ = embed_image(img)
            emb = emb if emb is not None else np.zeros(128, np.float32)  # aucun visage
            cache[key] = emb
            changed = True
        keys.append(key)
        if np.any(emb):
            result[p] = emb
    if keys and (changed or len(keys) != len(cache)):
        np.savez(cache_file, keys=np.array(keys, dtype=object), embs=np.array([cache[k] for k in keys]))
    return result


# ---------- Galerie ----------
class Gallery:
    def __init__(self):
        self.persons = {}   # id -> {"name", "images": [Path], "embs": ndarray (n,128)}
        self.reload()

    def reload(self):
        names = person_names()
        files = list_images(REF_DIR)
        all_paths = [p for ps in files.values() for p in ps]
        embs = embed_files(all_paths, "reference")
        self.persons = {}
        for pid, paths in files.items():
            valid = [p for p in paths if p in embs]
            self.persons[pid] = {
                "name": names.get(pid, pid),
                "images": paths,
                "embs": np.array([embs[p] for p in valid]) if valid else np.zeros((0, 128)),
            }
        return self

    # 1:1 — « Cette photo est-elle bien la personne X ? »
    def verify(self, emb, person_id):
        p = self.persons.get(person_id)
        if p is None:
            raise KeyError(person_id)
        if len(p["embs"]) == 0:
            return {"score": 0.0, "mean": 0.0, "match": False}
        sims = p["embs"] @ emb
        score = float(sims.max())
        return {"score": round(score, 4), "mean": round(float(sims.mean()), 4),
                "match": score >= THRESHOLD}

    # 1:N — « Qui est sur cette photo ? »
    def identify(self, emb, top_k=5):
        ranking = []
        for pid, p in self.persons.items():
            if len(p["embs"]):
                ranking.append({"person_id": pid, "name": p["name"],
                                "score": round(float((p["embs"] @ emb).max()), 4)})
        ranking.sort(key=lambda r: -r["score"])
        best = ranking[0] if ranking and ranking[0]["score"] >= THRESHOLD else None
        return {"best": best, "ranking": ranking[:top_k]}

    def add_person(self, name, images_bgr):
        """Crée data/reference/person_XXX/ avec les images contenant un visage."""
        nums = [int(m.group(1)) for d in REF_DIR.glob("person_*")
                if (m := re.match(r"person_(\d+)", d.name))]
        pid = f"person_{(max(nums) + 1 if nums else 1):03d}"
        folder = REF_DIR / pid
        saved = 0
        for img in images_bgr:
            if embed_image(img)[0] is None:
                continue
            folder.mkdir(parents=True, exist_ok=True)
            saved += 1
            imwrite_unicode(folder / f"img_{saved:02d}.jpg", img)
        if saved:
            names = person_names()
            names[pid] = name
            (DATA_DIR / "persons.json").write_text(json.dumps(names, ensure_ascii=False, indent=2), encoding="utf-8")
            self.reload()
        return pid if saved else None, saved


# ---------- Évaluation sur data/test ----------
def evaluate(gallery: Gallery, threshold=THRESHOLD):
    files = {pid: ps for pid, ps in list_images(TEST_DIR).items() if pid in gallery.persons}
    embs = embed_files([p for ps in files.values() for p in ps], "test")

    genuine, impostor, rank1, n_ident = [], [], 0, 0
    for pid, paths in files.items():
        for p in paths:
            if p not in embs:
                continue
            e = embs[p]
            for other, info in gallery.persons.items():
                if len(info["embs"]) == 0:
                    continue
                s = float((info["embs"] @ e).max())
                (genuine if other == pid else impostor).append(s)
            ident = gallery.identify(e, top_k=1)["ranking"]
            n_ident += 1
            rank1 += bool(ident and ident[0]["person_id"] == pid)

    g, i = np.array(genuine), np.array(impostor)
    if len(g) == 0 or len(i) == 0:
        return {"error": "Pas assez de données de test (au moins 2 personnes avec des images dans data/test)"}

    def rates(t):
        return float(np.mean(i >= t)), float(np.mean(g < t))  # FAR, FRR

    far, frr = rates(threshold)
    ts = np.linspace(-0.2, 1.0, 241)
    curve = [rates(t) for t in ts]
    eer_idx = int(np.argmin([abs(a - b) for a, b in curve]))
    bins = np.linspace(-0.2, 1.0, 25)
    return {
        "threshold": threshold,
        "n_test_images": n_ident,
        "n_genuine": len(g),
        "n_impostor": len(i),
        "FAR": round(far, 4),               # imposteurs acceptés à tort
        "FRR": round(frr, 4),               # vraies personnes refusées à tort
        "verification_accuracy": round(1 - (far * len(i) + frr * len(g)) / (len(i) + len(g)), 4),
        "identification_rank1": round(rank1 / n_ident, 4),
        "EER": round((curve[eer_idx][0] + curve[eer_idx][1]) / 2, 4),
        "EER_threshold": round(float(ts[eer_idx]), 3),
        "histogram": {
            "bins": [round(float(b), 2) for b in bins[:-1]],
            "genuine": np.histogram(g, bins)[0].tolist(),
            "impostor": np.histogram(i, bins)[0].tolist(),
        },
    }


def cosine_between(emb_a, emb_b):
    s = cosine(emb_a, emb_b)
    return {"score": round(s, 4), "match": s >= THRESHOLD}
