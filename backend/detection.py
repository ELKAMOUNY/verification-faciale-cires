"""
Détection de visages avec YuNet (OpenCV DNN, modèle ONNX ~230 Ko).

Chaque visage détecté est une ligne de 15 valeurs :
  x, y, w, h, 5 points de repère (yeux, nez, coins de la bouche), score
"""
import shutil
import tempfile
import urllib.request
from pathlib import Path

import cv2
import numpy as np

MODELS_DIR = Path(__file__).resolve().parent / "models"
_BASE = "https://media.githubusercontent.com/media/opencv/opencv_zoo/main/models"
MODELS = {
    "yunet": (MODELS_DIR / "face_detection_yunet_2023mar.onnx",
              f"{_BASE}/face_detection_yunet/face_detection_yunet_2023mar.onnx"),
    "sface": (MODELS_DIR / "face_recognition_sface_2021dec.onnx",
              f"{_BASE}/face_recognition_sface/face_recognition_sface_2021dec.onnx"),
}

# Taille exacte des fichiers officiels (sert à détecter un téléchargement interrompu)
MODEL_SIZES = {"yunet": 232_589, "sface": 38_696_353}

SCORE_THRESHOLD = 0.8
MAX_SIDE = 1280  # les grandes photos sont réduites avant détection

_detector = None


def ensure_models():
    """Télécharge les modèles ONNX s'ils sont absents (une seule fois)."""
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    for name, (path, url) in MODELS.items():
        expected = MODEL_SIZES[name]
        if path.exists() and path.stat().st_size == expected:
            continue
        if path.exists():
            print(f"Modèle {name} incomplet ({path.stat().st_size} octets au lieu de {expected}) : nouveau téléchargement…")
            path.unlink()
        tmp = path.with_suffix(".part")
        for attempt in range(1, 4):
            print(f"Téléchargement du modèle {name} ({expected // 1_000_000 or 1} Mo), essai {attempt}/3…")
            try:
                urllib.request.urlretrieve(url, tmp)
                if tmp.stat().st_size == expected:
                    tmp.replace(path)          # le fichier n'apparaît que s'il est complet
                    break
                print(f"  téléchargement incomplet ({tmp.stat().st_size} octets)")
            except OSError as e:
                print(f"  échec : {e}")
        else:
            if tmp.exists():
                tmp.unlink()
            raise RuntimeError(
                f"Impossible de télécharger le modèle {name}. Vérifiez la connexion Internet, "
                f"ou téléchargez-le manuellement depuis {url} et placez-le dans {path}"
            )
    return {k: v[0] for k, v in MODELS.items()}


# ---------- Chemins avec accents (Windows) ----------
# OpenCV ne sait pas ouvrir un chemin contenant des accents sous Windows
# (ex. « Systéme de reconnaissance faciale »). Ces fonctions contournent le problème.
def imread_unicode(path, flags=cv2.IMREAD_COLOR):
    """cv2.imread compatible avec les accents : lecture des octets en Python pur, décodage par OpenCV."""
    try:
        data = Path(path).read_bytes()
    except OSError as e:
        print(f"Lecture impossible : {path} ({e})")
        return None
    img = cv2.imdecode(np.frombuffer(data, np.uint8), flags) if data else None
    if img is None:
        print(f"Image non décodable : {path}")
    return img


def imwrite_unicode(path, img, ext=".jpg") -> bool:
    """cv2.imwrite compatible avec les accents."""
    ok, buf = cv2.imencode(ext, img)
    if ok:
        Path(path).write_bytes(buf.tobytes())
    return bool(ok)


def model_path(name: str) -> str:
    """Chemin du modèle utilisable par OpenCV : copie vers un dossier sans accent si besoin."""
    ensure_models()
    src = MODELS[name][0]
    if str(src).isascii():
        return str(src)
    for base in (Path(tempfile.gettempdir()), Path("C:/Users/Public"), Path("C:/ProgramData")):
        dst = base / "fv_models" / src.name
        if str(dst).isascii():
            try:
                dst.parent.mkdir(parents=True, exist_ok=True)
                if not dst.exists() or dst.stat().st_size != src.stat().st_size:
                    shutil.copyfile(src, dst)
                return str(dst)
            except OSError:
                continue
    raise RuntimeError(
        f"Impossible de charger le modèle depuis « {src} » (accents dans le chemin). "
        "Renommez le dossier du projet sans accent, par exemple « Systeme de reconnaissance faciale »."
    )


def _get_detector():
    global _detector
    if _detector is None:
        ensure_models()
        _detector = cv2.FaceDetectorYN.create(
            model_path("yunet"), "", (320, 320), SCORE_THRESHOLD, 0.3, 5000
        )
    return _detector


def resize_if_needed(img):
    h, w = img.shape[:2]
    scale = min(1.0, MAX_SIDE / max(h, w))
    if scale < 1.0:
        img = cv2.resize(img, (int(w * scale), int(h * scale)))
    return img


def decode_image(data: bytes):
    img = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("Image illisible")
    return resize_if_needed(img)


def detect(img) -> np.ndarray:
    """Retourne un tableau (N, 15) des visages, trié du plus grand au plus petit."""
    det = _get_detector()
    h, w = img.shape[:2]
    det.setInputSize((w, h))
    _, faces = det.detect(img)
    if faces is None:
        return np.zeros((0, 15), dtype=np.float32)
    order = np.argsort(-(faces[:, 2] * faces[:, 3]))
    return faces[order]


def box(face_row):
    """[x, y, w, h] en entiers (pour le frontend)."""
    return [int(round(v)) for v in face_row[:4]]
