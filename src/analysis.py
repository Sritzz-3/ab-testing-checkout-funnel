from __future__ import annotations
import numpy as np, pandas as pd
from scipy import stats
from statsmodels.stats.proportion import proportions_ztest, proportion_confint
from statsmodels.stats.multitest import multipletests
import statsmodels.formula.api as smf

def analyze(df,c):
    out={}; groups={a:df[df.variant==a] for a in ['control','treatment']}; n0,n1=[len(groups[a]) for a in ['control','treatment']]; x0,x1=[int(groups[a].converted.sum()) for a in ['control','treatment']]; p0,p1=x0/n0,x1/n1
    z,p=proportions_ztest([x1,x0],[n1,n0]); diff=p1-p0; se=np.sqrt(p1*(1-p1)/n1+p0*(1-p0)/n0); lo,hi=diff-1.96*se,diff+1.96*se
    rel=p1/p0-1; ser=np.sqrt((1-p1)/(n1*p1)+(1-p0)/(n0*p0)); rlo,rhi=rel-1.96*ser,rel+1.96*ser
    rng=np.random.default_rng(c['seed']+1); b0=rng.binomial(n0,p0,(c['bootstrap_resamples'],))/n0; b1=rng.binomial(n1,p1,(c['bootstrap_resamples'],))/n1; br=b1/b0-1; blo,bhi=np.quantile(br,[.025,.975])
    wil=[proportion_confint(x0,n0,method='wilson'),proportion_confint(x1,n1,method='wilson')]
    tables=[]
    for i,(a,n,x,ci) in enumerate([('control',n0,x0,wil[0]),('treatment',n1,x1,wil[1])]): tables.append({'arm':a,'sessions':n,'conversions':x,'rate':x/n,'ci_low':ci[0],'ci_high':ci[1]})
    pd.DataFrame(tables).to_csv('outputs/tables/conversion.csv',index=False)
    fish=stats.fisher_exact([[x1,n1-x1],[x0,n0-x0]]); chi=stats.chi2_contingency([[x1,n1-x1],[x0,n0-x0]],correction=False)
    try:
        model=smf.logit('converted ~ C(variant) + C(device) + C(traffic_source) + C(user_type) + np.log(cart_value)',data=df).fit(disp=0); key='C(variant)[T.treatment]'; aor=float(np.exp(model.params[key])); aci=np.exp(model.conf_int().loc[key]).tolist()
    except Exception: aor=1+rel; aci=[np.nan,np.nan]
    # checkout-time comparison among checkout starters
    starts=df.dropna(subset=['checkout_seconds']); t0=starts[starts.variant=='control'].checkout_seconds.to_numpy(); t1=starts[starts.variant=='treatment'].checkout_seconds.to_numpy()
    time={k:float(v) for k,v in {'control_median':np.median(t0),'treatment_median':np.median(t1),'control_mean':np.mean(t0),'treatment_mean':np.mean(t1),'median_reduction':1-np.median(t1)/np.median(t0),'mean_reduction':1-np.mean(t1)/np.mean(t0),'mann_whitney_p':stats.mannwhitneyu(t0,t1).pvalue,'welch_log_p':stats.ttest_ind(np.log(t0),np.log(t1),equal_var=False).pvalue}.items()}
    # AOV and payment error guardrails
    av0=groups['control'].dropna(subset=['order_value']).order_value.to_numpy(); av1=groups['treatment'].dropna(subset=['order_value']).order_value.to_numpy(); aovdiff=np.mean(av1)/np.mean(av0)-1; aovse=np.sqrt(np.var(av1,ddof=1)/len(av1)/np.mean(av0)**2+np.var(av0,ddof=1)/len(av0)*np.mean(av1)**2/np.mean(av0)**4); aovlow=aovdiff-1.645*aovse
    e0=groups['control'].payment_error.mean(); e1=groups['treatment'].payment_error.mean(); ediff=e1-e0; ese=np.sqrt(e0*(1-e0)/n0+e1*(1-e1)/n1)
    pd.DataFrame([{'guardrail':'AOV relative difference','control':np.mean(av0),'treatment':np.mean(av1),'effect':aovdiff,'ci_low':aovlow,'margin':c['aov_noninferiority_margin'],'pass':aovlow>c['aov_noninferiority_margin']},{'guardrail':'payment error difference','control':e0,'treatment':e1,'effect':ediff,'ci_low':ediff-1.96*ese,'margin':c['payment_error_margin'],'pass':ediff+1.645*ese<c['payment_error_margin']}]).to_csv('outputs/tables/guardrails.csv',index=False)
    # funnel steps
    funnel=[]
    for a,g in groups.items():
        for col,label in [('step1_reached','stage1'),('step2_reached','stage2'),('step3_reached','stage3')]: funnel.append({'arm':a,'stage':label,'reached':int(g[col].sum()),'sessions':len(g),'rate':g[col].mean()})
    pd.DataFrame(funnel).to_csv('outputs/tables/funnel.csv',index=False)
    # segments
    seg=[]
    for col in ['device','user_type','traffic_source']:
        for value,g in df.groupby(col):
            aa=g[g.variant=='control']; bb=g[g.variant=='treatment']; pp0=aa.converted.mean(); pp1=bb.converted.mean(); pv=stats.chi2_contingency([[bb.converted.sum(),len(bb)-bb.converted.sum()],[aa.converted.sum(),len(aa)-aa.converted.sum()]],correction=False)[1]
            serr=np.sqrt(pp1*(1-pp1)/len(bb)+pp0*(1-pp0)/len(aa)); seg.append({'dimension':col,'segment':value,'relative_lift':pp1/pp0-1,'ci_low':(pp1-pp0-1.96*serr)/pp0,'ci_high':(pp1-pp0+1.96*serr)/pp0,'p_value':pv})
    adj=multipletests([s['p_value'] for s in seg],method='holm')[1]
    for s,a in zip(seg,adj): s['holm_p_value']=float(a)
    pd.DataFrame(seg).to_csv('outputs/tables/segments.csv',index=False)
    # balance
    bal=[]
    for col in ['device','traffic_source','user_type','day_of_week']:
        tab=pd.crosstab(df.variant,df[col]); bal.append({'covariate':col,'p_value':stats.chi2_contingency(tab)[1]})
    pd.DataFrame(bal).to_csv('outputs/tables/balance.csv',index=False)
    # weekly/daily
    df.assign(week=np.where(pd.to_datetime(df.date).dt.day<=12,'week1','week2')).groupby(['week','variant']).converted.agg(['mean','sum','count']).reset_index().to_csv('outputs/tables/time_stability.csv',index=False)
    df.groupby([pd.to_datetime(df.date).dt.date,'variant']).converted.mean().rename('rate').reset_index().to_csv('outputs/tables/daily.csv',index=False)
    # posterior draws
    post0=rng.beta(1+x0,1+n0-x0,c['bayesian_draws']); post1=rng.beta(1+x1,1+n1-x1,c['bayesian_draws']); postrel=post1/post0-1
    result={'control_rate':p0,'treatment_rate':p1,'control_n':n0,'treatment_n':n1,'control_conversions':x0,'treatment_conversions':x1,'relative_lift':rel,'relative_ci_low':rlo,'relative_ci_high':rhi,'bootstrap_ci_low':float(blo),'bootstrap_ci_high':float(bhi),'absolute_lift':diff,'absolute_ci_low':lo,'absolute_ci_high':hi,'z_statistic':float(z),'z_p_value':float(p),'chi_square_p_value':float(chi[1]),'fisher_p_value':float(fish.pvalue),'adjusted_odds_ratio':aor,'adjusted_or_ci_low':float(aci[0]),'adjusted_or_ci_high':float(aci[1]),'checkout':time,'aov_pass':bool(aovlow>c['aov_noninferiority_margin']),'aov_relative_effect':float(aovdiff),'aov_ci_low':float(aovlow),'payment_error_pass':bool(ediff+1.645*ese<c['payment_error_margin']),'payment_error_difference':float(ediff),'payment_error_upper':float(ediff+1.645*ese),'bayes_probability_treatment_better':float(np.mean(post1>post0)),'bayes_relative_lift_mean':float(np.mean(postrel)),'bayes_ci_low':float(np.quantile(postrel,.025)),'bayes_ci_high':float(np.quantile(postrel,.975)),'expected_loss_control':float(np.mean(np.maximum(post1-post0,0))),'expected_loss_treatment':float(np.mean(np.maximum(post0-post1,0)))}
    result['decision']='SHIP' if p<c['alpha'] and rlo>0 and result['aov_pass'] and result['payment_error_pass'] else ('DO NOT SHIP' if p<c['alpha'] and rhi<0 else 'INCONCLUSIVE')
    result['decision_reasons']={'primary':bool(p<c['alpha'] and rlo>0),'aov':result['aov_pass'],'payment_error':result['payment_error_pass']}
    return result
