"""
Embeddings faciaux avec SFace (réseau de neurones, OpenCV DNN).

Un visage est transformé en un vecteur de 128 nombres (« embedding »).
Deux photos de la même personne donnent des vecteurs proches :
on les compare avec la similarité cosinus (1 = identiques, 0 = sans rapport).
"""
import cv2
import numpy as np

from detection import detect, model_path

_recognizer = None


def _get_recognizer():
    global _recognizer
    if _recognizer is None:
        _recognizer = cv2.FaceRecognizerSF.create(model_path("sface"), "")
    return _recognizer


def aligned_face(img, face_row):
    """Visage aligné (yeux à l'horizontale) et recadré en 112x112."""
    return _get_recognizer().alignCrop(img, face_row)


def embed_face(img, face_row) -> np.ndarray:
    """Embedding normalisé (norme 1) d'un visage détecté."""
    feat = _get_recognizer().feature(aligned_face(img, face_row)).flatten()
    return feat / (np.linalg.norm(feat) + 1e-10)


def embed_image(img):
    """(embedding, face_row) du plus grand visage, ou (None, None) si aucun visage."""
    faces = detect(img)
    if len(faces) == 0:
        return None, None
    return embed_face(img, faces[0]), faces[0]


def cosine(a, b) -> float:
    return float(np.dot(a, b))  # vecteurs déjà normalisés
