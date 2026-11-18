import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile


def atomic_write(path: Path, data: bytes):
    path.parent.mkdir(parents=True, exist_ok=True)
    name = None
    try:
        with NamedTemporaryFile(dir=path.parent, delete=False) as stream:
            name = stream.name
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
    finally:
        if name and Path(name).exists():
            Path(name).unlink()


def save_json(path, data):
    atomic_write(path, json.dumps(data, ensure_ascii=False, indent=2).encode('utf-8'))


def load_json(path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except (OSError, ValueError) as exc:
        raise ValueError(f'Gespeicherte Datei kann nicht gelesen werden: {path.name}') from exc
