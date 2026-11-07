import json
import shutil
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

CALC_OUT = {"m_kg": 1, "dT_example": 5, "Q_J": 21000, "c_water": 4200, "c_concrete": 880, "c_asphalt": 920,
            "dT_water": 5.0, "dT_concrete": 23.86, "dT_asphalt": 22.83}
NUMBER_KEYS = [f"table.r{r}c{c}" for r in (1, 2, 3) for c in (1, 2, 3)] + ["example.result"] + [f"graph.{i}.value" for i in (1, 2, 3)]
ID_LABELS = {
    "label.quest_map": "PETA MISIMU", "label.fun_fact": "TAHUKAH KAMU?", "label.timeline": "LINIMASA",
    "label.equation": "PERSAMAAN KUNCI", "label.example": "CONTOH SOAL", "label.graph": "GRAFIK",
    "label.tip": "KATA BULB BUDDY", "label.quiz": "KUIS KILAT · 3 SOAL · CENTANG SATU KOTAK",
    "label.lab": "LAB MINI · COBA DI RUMAH ATAU SEKOLAH", "label.badge": "LENCANA TERBUKA",
    "quest.1.title": "Ceritanya", "quest.2.title": "Fisikanya", "quest.3.title": "Misimu",
}


def example_en():
    return json.loads((ROOT / "schema" / "example.en.json").read_text(encoding="utf-8"))


def id_from(en):
    """A stand-in id.json: same text, Indonesian number format and labels."""
    d = dict(en, _lang="id", **{"guide.lang": "ID", "quiz.answer_key": "Kunci: 1B · 2A · 3C"}, **ID_LABELS)
    for k in NUMBER_KEYS:
        d[k] = d[k].translate(str.maketrans({",": ".", ".": ","}))
    return d


class Issue:
    def __init__(self, root):
        self.root = root
        self.folder = root / "issues" / "2026-11-09"
        self.folder.mkdir(parents=True)
        self.manifest = root / "manifest.json"
        self.en = example_en()
        self.id = id_from(self.en)
        self.calc = dict(CALC_OUT)
        self.check = [{"item": "stat.1", "claim": "4,200 J", "source": 2, "pass": True, "note": ""}]
        self.guides = []
        (self.folder / "cover.jpg").write_bytes(b"jpg")

    def write(self):
        for name, obj in (("en.json", self.en), ("id.json", self.id), ("calc.out.json", self.calc), ("check.json", self.check)):
            (self.folder / name).write_text(json.dumps(obj, ensure_ascii=False), encoding="utf-8")
        self.manifest.write_text(json.dumps({"updated": None, "guides": self.guides}), encoding="utf-8")

    def errors(self):
        import validate
        self.write()
        return validate.check(self.folder, self.manifest)


@pytest.fixture
def issue(tmp_path):
    return Issue(tmp_path)
