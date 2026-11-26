from __future__ import annotations
import numpy as np, pandas as pd
from scipy import stats

def validate(df,c):
    cnt=df.variant.value_counts(); srm=stats.chisquare(cnt.values); n0=int((df.variant=='control').sum()); n1=int((df.variant=='treatment').sum()); p=c['baseline_conversion']; sims=c['simulations']; rng=np.random.default_rng(c['seed']+8)
    a=rng.binomial(n0,p,sims); b=rng.binomial(n1,p,sims); pooled=(a+b)/(n0+n1); z=(b/n1-a/n0)/np.sqrt(pooled*(1-pooled)*(1/n0+1/n1)); pv=2*stats.norm.sf(np.abs(z)); fp=float(np.mean(pv<c['alpha'])); ci=[float(max(0,fp-1.96*np.sqrt(fp*(1-fp)/sims))),float(min(1,fp+1.96*np.sqrt(fp*(1-fp)/sims)))]
    pt=p*(1+c['relative_lift']); a2=rng.binomial(n0,p,sims); b2=rng.binomial(n1,pt,sims); pool=(a2+b2)/(n0+n1); zz=(b2/n1-a2/n0)/np.sqrt(pool*(1-pool)*(1/n0+1/n1)); power=float(np.mean(2*stats.norm.sf(np.abs(zz))<c['alpha']))
    curve=[]
    for nn in [4000,8000,12000,16000,20000,24000,32000,40000]:
        aa=rng.binomial(nn//2,p,sims); bb=rng.binomial(nn//2,pt,sims); po=(aa+bb)/nn; zc=(bb/(nn//2)-aa/(nn//2))/np.sqrt(po*(1-po)*4/nn); curve.append({'n_total':nn,'power':float(np.mean(2*stats.norm.sf(np.abs(zc))<c['alpha']))})
    pd.DataFrame({'p_value':pv}).to_csv('outputs/tables/aa_pvalues.csv',index=False); pd.DataFrame(curve).to_csv('outputs/tables/power_curve.csv',index=False)
    return {'srm_p_value':float(srm.pvalue),'srm_flag':bool(srm.pvalue<.001),'aa_false_positive_rate':fp,'aa_ci_low':ci[0],'aa_ci_high':ci[1],'empirical_power':power,'balance_file':'outputs/tables/balance.csv'}
