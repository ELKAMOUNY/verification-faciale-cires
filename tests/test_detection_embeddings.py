import cv2
import numpy as np

from conftest import face_image


def test_detect_one_face():
    from detection import detect
    faces = detect(face_image())
    assert len(faces) == 1
    assert faces[0][14] > 0.8  # score de confiance


def test_detect_no_face():
    from detection import detect
    assert len(detect(np.zeros((300, 300, 3), np.uint8))) == 0


def test_embedding_is_normalized():
    from embeddings import embed_image
    emb, face = embed_image(face_image())
    assert emb.shape == (128,)
    assert abs(np.linalg.norm(emb) - 1) < 1e-5


def test_same_person_similar():
    from embeddings import cosine, embed_image
    from verification import THRESHOLD
    img = face_image()
    e1, _ = embed_image(img)
    e2, _ = embed_image(cv2.flip(img, 1))
    assert cosine(e1, e2) > THRESHOLD
