from __future__ import annotations
import numpy as np
import pandas as pd
from .config import load_config

def simulate_sessions(config=None):
    c = config or load_config(); rng = np.random.default_rng(c['seed']); n=max(20000,int(c['n_sessions']))
    arm=np.where(rng.random(n)<.5,'treatment','control')
    device=rng.choice(['mobile','desktop','tablet'],n,p=[.58,.34,.08]); source=rng.choice(['organic','paid','email','direct'],n,p=[.38,.28,.16,.18]); user=rng.choice(['new','returning'],n,p=[.62,.38])
    date=pd.Series(pd.Timestamp('2025-01-06')+pd.to_timedelta(rng.integers(0,c['days'],n),unit='D'))
    cart=np.exp(rng.normal(3.5,.65,n)); dow=date.dt.dayofweek.to_numpy(); dayeff=np.array([-.008,0,.006,.002,-.003,.008,-.005])[dow]
    lift=np.full(n,c['relative_lift'])+np.where(device=='mobile',.08,np.where(device=='desktop',-.04,0))+np.where(user=='new',.06,-.04)
    p=np.clip(c['baseline_conversion']+dayeff,0,.8); p=np.where(arm=='treatment',p*(1+lift),p); conv=(rng.random(n)<p).astype(int)
    start=rng.random(n)<.94; reached2=start&(rng.random(n)<np.where(arm=='control',.79,.85)); reached3=reached2&(rng.random(n)<np.where(arm=='control',.82,.86)); reached3|=conv.astype(bool)
    conv=(conv & reached3).astype(int)
    sec=np.where(device=='mobile',1.25,1.0)*rng.lognormal(np.log(np.where(arm=='treatment',150,300)),.48,n)
    err=(rng.random(n)<.025).astype(int); order=np.where(conv==1,cart*rng.lognormal(0,.08,n),np.nan)
    return pd.DataFrame({'session_id':np.arange(1,n+1),'date':date,'day_of_week':date.dt.day_name(),'variant':arm,'device':device,'traffic_source':source,'user_type':user,'cart_value':cart,'step1_reached':start.astype(int),'step2_reached':reached2.astype(int),'step3_reached':reached3.astype(int),'converted':conv,'checkout_seconds':np.where(start,sec,np.nan),'payment_error':err,'order_value':order})
