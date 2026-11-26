from src.validation import validate
from src.simulator import simulate_sessions
from src.config import load_config

def test_validation():
    c=load_config(); c['simulations']=100; v=validate(simulate_sessions(c),c); assert 0<=v['aa_false_positive_rate']<=1
