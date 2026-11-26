from src.simulator import simulate_sessions

def test_simulator():
    a=simulate_sessions(); b=simulate_sessions(); assert len(a)>=20000; assert a.equals(b); assert (a.converted<=a.step3_reached).all(); assert a.variant.value_counts(normalize=True).min()>.47
