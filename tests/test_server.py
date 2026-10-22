import ast
from pathlib import Path


def test_backend_syntax():
    path = Path(__file__).resolve().parents[1] / 'backend' / 'server.py'
    ast.parse(path.read_text(encoding='utf-8'))


def test_frontend_exists():
    root = Path(__file__).resolve().parents[1] / 'frontend'
    assert all((root / name).is_file() for name in ('index.html','app.js','style.css'))
