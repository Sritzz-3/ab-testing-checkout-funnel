from src.design import build_design
from src.config import load_config

def test_design(): assert build_design(load_config())>0
