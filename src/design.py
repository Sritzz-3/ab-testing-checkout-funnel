from __future__ import annotations
import numpy as np, pandas as pd
from statsmodels.stats.power import NormalIndPower
from statsmodels.stats.proportion import proportion_effectsize

def build_design(c):
    p=c['baseline_conversion']; eff=proportion_effectsize(p,p*(1+c['relative_lift'])); n=int(np.ceil(NormalIndPower().solve_power(eff, power=c['power'], alpha=c['alpha'], ratio=1, alternative='two-sided')))
    pd.DataFrame([{'metric':'conversion_rate','H0':'p_treatment = p_control','H1':'p_treatment != p_control','alpha':c['alpha'],'power':c['power'],'baseline_rate':p,'relative_mde':c['relative_lift'],'required_n_per_arm':n,'actual_n_per_arm':c['n_sessions']//2,'adequately_powered':c['n_sessions']//2>=n}]).to_csv('outputs/tables/design.csv',index=False)
    rows=[]
    for m in [.10,.15,.20,.25,.30]:
        rows.append({'relative_mde':m,'required_n_per_arm':int(np.ceil(NormalIndPower().solve_power(proportion_effectsize(p,p*(1+m)),power=c['power'],alpha=c['alpha'],ratio=1,alternative='two-sided')))})
    pd.DataFrame(rows).to_csv('outputs/tables/sample_size_sensitivity.csv',index=False)
    return n
