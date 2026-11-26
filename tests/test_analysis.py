from scipy.stats import norm
from statsmodels.stats.proportion import proportions_ztest

def test_hand_z():
    z,p=proportions_ztest([100,90],[1000,1000]); assert abs(p-2*norm.sf(abs(z)))<1e-12
