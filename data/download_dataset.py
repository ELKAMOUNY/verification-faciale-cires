"""
Télécharge un jeu de données de visages EN LIGNE et le range au format :

    data/dataset/person_001/img_01.jpg ...      (toutes les images)
    data/reference/person_001/img_01.jpg ...    (images de référence = galerie)
    data/test/person_001/img_04.jpg ...         (images de test = évaluation)
    data/persons.json                            {"person_001": "Nom réel", ...}

Source : LFW — Labeled Faces in the Wild (Université du Massachusetts),
13 233 photos de 5 749 personnalités. Téléchargé via scikit-learn (~200 Mo la 1re fois).

Exemples :
    python data/download_dataset.py                        # 20 personnes, 8 photos, 3 de référence
    python data/download_dataset.py --people 50 --max 10 --ref 4
    python data/download_dataset.py --split-only            # re-découper votre propre data/dataset
"""
import argparse
import json
import random
import shutil
from pathlib import Path

import cv2
import numpy as np

DATA = Path(__file__).resolve().parent
DATASET, REF, TEST = DATA / "dataset", DATA / "reference", DATA / "test"
IMG_EXT = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def clear(folder: Path):
    folder.mkdir(parents=True, exist_ok=True)
    for d in folder.glob("person_*"):
        shutil.rmtree(d)


def download_lfw(n_people, min_faces, max_per_person, seed):
    from sklearn.datasets import fetch_lfw_people

    print("Téléchargement de LFW (≈200 Mo la première fois, ensuite en cache)…")
    lfw = fetch_lfw_people(
        min_faces_per_person=min_faces,
        color=True,
        resize=1.0,
        slice_=(slice(0, 250), slice(0, 250)),  # image entière 250x250 (le visage est détecté ensuite)
    )
    images = lfw.images
    if images.max() <= 1.0:
        images = images * 255
    images = images.astype(np.uint8)

    labels = sorted(set(lfw.target.tolist()))
    random.Random(seed).shuffle(labels)
    labels = labels[:n_people]
    print(f"{len(lfw.target_names)} personnes ont au moins {min_faces} photos ; {len(labels)} sélectionnées.")

    clear(DATASET)
    names = {}
    for k, label in enumerate(labels, start=1):
        pid = f"person_{k:03d}"
        folder = DATASET / pid
        folder.mkdir(parents=True)
        idx = np.where(lfw.target == label)[0][:max_per_person]
        for j, i in enumerate(idx, start=1):
            cv2.imwrite(str(folder / f"img_{j:02d}.jpg"), cv2.cvtColor(images[i], cv2.COLOR_RGB2BGR))
        names[pid] = str(lfw.target_names[label])
        print(f"  {pid}  {names[pid]:30s} {len(idx)} images")

    (DATA / "persons.json").write_text(json.dumps(names, ensure_ascii=False, indent=2), encoding="utf-8")


def split(n_ref):
    """Les n_ref premières images -> reference/, les autres -> test/."""
    clear(REF)
    clear(TEST)
    n_r = n_t = 0
    for d in sorted(p for p in DATASET.iterdir() if p.is_dir()):
        imgs = sorted(f for f in d.iterdir() if f.suffix.lower() in IMG_EXT)
        for i, f in enumerate(imgs):
            dest = (REF if i < n_ref else TEST) / d.name
            dest.mkdir(parents=True, exist_ok=True)
            shutil.copy2(f, dest / f.name)
            if i < n_ref:
                n_r += 1
            else:
                n_t += 1
    names_file = DATA / "persons.json"
    if not names_file.exists():  # dataset personnel : le nom du dossier sert de nom
        names = {d.name: d.name for d in DATASET.iterdir() if d.is_dir()}
        names_file.write_text(json.dumps(names, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Découpage : {n_r} images de référence, {n_t} images de test.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--people", type=int, default=20, help="nombre de personnes (défaut 20)")
    ap.add_argument("--min-faces", type=int, default=10, help="photos minimum par personne dans LFW (défaut 10)")
    ap.add_argument("--max", type=int, default=8, help="photos maximum par personne (défaut 8)")
    ap.add_argument("--ref", type=int, default=3, help="photos de référence par personne (défaut 3)")
    ap.add_argument("--seed", type=int, default=42, help="graine du tirage des personnes")
    ap.add_argument("--split-only", action="store_true", help="ne pas télécharger, découper data/dataset existant")
    a = ap.parse_args()

    if not a.split_only:
        download_lfw(a.people, a.min_faces, a.max, a.seed)
    elif not DATASET.exists():
        raise SystemExit("data/dataset n'existe pas")
    split(a.ref)
    print("Terminé. Redémarrez le backend ou appelez POST /api/reload.")
