import cv2
import numpy as np
import pytest
from fastapi.testclient import TestClient

from conftest import face_image


@pytest.fixture(scope="module")
def client(data_dir):
    import importlib

    import verification
    importlib.reload(verification)  # prend en compte FV_DATA_DIR
    import main
    importlib.reload(main)
    return TestClient(main.app)


def jpg(img):
    return cv2.imencode(".jpg", img)[1].tobytes()


def test_health(client):
    r = client.get("/api/health").json()
    assert r["status"] == "ok" and r["persons"] == 1


def test_persons(client):
    p = client.get("/api/persons").json()
    assert p[0]["id"] == "person_001" and p[0]["name"] == "Astronaute" and p[0]["n_faces"] == 3


def test_verify_match(client):
    r = client.post("/api/verify", data={"person_id": "person_001"},
                    files={"file": ("a.jpg", jpg(face_image()), "image/jpeg")})
    assert r.status_code == 200 and r.json()["match"] is True


def test_verify_no_face(client):
    r = client.post("/api/verify", data={"person_id": "person_001"},
                    files={"file": ("n.jpg", jpg(np.zeros((200, 200, 3), np.uint8)), "image/jpeg")})
    assert r.status_code == 422


def test_verify_unknown_person(client):
    r = client.post("/api/verify", data={"person_id": "person_999"},
                    files={"file": ("a.jpg", jpg(face_image()), "image/jpeg")})
    assert r.status_code == 404


def test_identify(client):
    r = client.post("/api/identify", files={"file": ("a.jpg", jpg(face_image()), "image/jpeg")}).json()
    assert r["faces"][0]["best"]["person_id"] == "person_001"


def test_compare(client):
    img = face_image()
    r = client.post("/api/compare", files={"file1": ("a.jpg", jpg(img), "image/jpeg"),
                                           "file2": ("b.jpg", jpg(cv2.flip(img, 1)), "image/jpeg")}).json()
    assert r["match"] is True


def test_add_person_rejects_without_face(client):
    r = client.post("/api/persons", data={"name": "Vide"},
                    files=[("files", ("n.jpg", jpg(np.zeros((200, 200, 3), np.uint8)), "image/jpeg"))])
    assert r.status_code == 422


def test_image_served(client):
    r = client.get("/api/persons/person_001/images/img_01.jpg")
    assert r.status_code == 200 and r.headers["content-type"] == "image/jpeg"
