import ast, importlib.util, json, tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def test_backend_syntax():
    ast.parse((ROOT/'backend/server.py').read_text(encoding='utf-8'))

def test_frontend_exists():
    assert all((ROOT/'frontend'/name).is_file() for name in ('index.html','app.js','style.css'))

def load_server(monkeypatch,folder):
    monkeypatch.setenv('CLONE_APP_DATA',str(folder))
    spec=importlib.util.spec_from_file_location('clone_backend_test',ROOT/'backend/server.py')
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def test_create_project(monkeypatch,tmp_path):
    m=load_server(monkeypatch,tmp_path)
    obj=m.project_payload({'name':'Demo','media':[]})
    assert obj['name']=='Demo' and len(obj['id'])==32

def test_missing_media_rejected(monkeypatch,tmp_path):
    m=load_server(monkeypatch,tmp_path)
    import pytest
    with pytest.raises(ValueError):m.project_payload({'name':'Demo','media':['missing']})

def test_invalid_media_id(monkeypatch,tmp_path):
    m=load_server(monkeypatch,tmp_path)
    assert m.media_path('../secrets') is None
