"""Prépare un mini-dataset temporaire (aucune donnée réelle nécessaire)."""
import json
import os
import sys
from pathlib import Path

import cv2
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))


def face_image():
    from skimage import data  # image libre de droits fournie avec scikit-image
    return cv2.cvtColor(data.astronaut(), cv2.COLOR_RGB2BGR)


@pytest.fixture(scope="session")
def data_dir(tmp_path_factory):
    d = tmp_path_factory.mktemp("data")
    img = face_image()
    variants = [img, cv2.flip(img, 1), cv2.convertScaleAbs(img, alpha=1.2, beta=10)]
    for i, v in enumerate(variants, 1):
        (d / "reference" / "person_001").mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(d / "reference" / "person_001" / f"img_{i:02d}.jpg"), v)
    (d / "test" / "person_001").mkdir(parents=True)
    cv2.imwrite(str(d / "test" / "person_001" / "img_04.jpg"), cv2.convertScaleAbs(img, alpha=0.8))
    (d / "persons.json").write_text(json.dumps({"person_001": "Astronaute"}))
    os.environ["FV_DATA_DIR"] = str(d)
    return d
