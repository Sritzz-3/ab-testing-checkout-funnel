from pathlib import Path
from src.validation import validate
from src.simulator import simulate_sessions
from src.config import load_config

def test_validation(tmp_path, monkeypatch):
    c=load_config()
    monkeypatch.chdir(tmp_path)
    Path("outputs/tables").mkdir(parents=True)
    c['simulations']=100; v=validate(simulate_sessions(c),c); assert 0<=v['aa_false_positive_rate']<=1
