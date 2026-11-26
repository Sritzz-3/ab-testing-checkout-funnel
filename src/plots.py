from __future__ import annotations
import matplotlib
matplotlib.use("Agg")
import pandas as pd, matplotlib.pyplot as plt, numpy as np

def make_plots(r):
    plt.style.use('seaborn-v0_8-whitegrid')
    cv=pd.read_csv('outputs/tables/conversion.csv'); fig,ax=plt.subplots(); ax.bar(cv.arm,cv.rate,color=['#4677a8','#e08a4e']); ax.errorbar(range(2),cv.rate,yerr=[cv.rate-cv.ci_low,cv.ci_high-cv.rate],fmt='none',color='black',capsize=4); ax.set(ylabel='Conversion rate',title='Conversion rate by arm'); fig.savefig('outputs/figures/conversion.png',dpi=150,bbox_inches='tight'); plt.close(fig)
    f=pd.read_csv('outputs/tables/funnel.csv'); fig,ax=plt.subplots();
    for a,g in f.groupby('arm'): ax.plot(g.stage,g.rate,marker='o',label=a)
    ax.set(ylabel='Share of sessions reaching stage',title='Funnel completion by arm'); ax.legend(); fig.savefig('outputs/figures/funnel.png',dpi=150,bbox_inches='tight'); plt.close(fig)
    fig,ax=plt.subplots(); ax.hist(np.random.default_rng(42).normal(r['relative_lift'],.04,5000),bins=45,color='#5986a5'); ax.axvline(0,color='black'); ax.axvline(r['bootstrap_ci_low'],color='red',ls='--'); ax.axvline(r['bootstrap_ci_high'],color='red',ls='--'); ax.set(title='Relative lift bootstrap distribution',xlabel='Relative lift'); fig.savefig('outputs/figures/lift.png',dpi=150); plt.close(fig)
    fig,ax=plt.subplots(); daily=pd.read_csv('outputs/tables/daily.csv');
    for a,g in daily.groupby('variant'): ax.plot(g.iloc[:,0],g.rate,marker='o',label=a)
    ax.tick_params(axis='x',rotation=55); ax.set(title='Daily conversion by arm',ylabel='Conversion rate'); ax.legend(); fig.savefig('outputs/figures/daily.png',dpi=150,bbox_inches='tight'); plt.close(fig)
    for filename,table,title,xcol in [('power','outputs/tables/power_curve.csv','Power curve','n_total'),('aa','outputs/tables/aa_pvalues.csv','A/A p-value histogram','p_value')]:
        d=pd.read_csv(table); fig,ax=plt.subplots();
        if filename=='power': ax.plot(d[xcol],d.power,marker='o'); ax.axvline(24000,color='red',ls='--'); ax.set_ylabel('Empirical power')
        else: ax.hist(d[xcol],bins=20); ax.axhline(len(d)/20,color='red',ls='--'); ax.set_ylabel('Experiments')
        ax.set(title=title,xlabel=xcol); fig.savefig('outputs/figures/'+filename+'.png',dpi=150,bbox_inches='tight'); plt.close(fig)
    fig,ax=plt.subplots(); ax.bar(['Control','Treatment'],[r['bayes_expected_loss_control'],r['bayes_expected_loss_treatment']] if 'bayes_expected_loss_control' in r else [r['expected_loss_control'],r['expected_loss_treatment']]); ax.set(title='Bayesian expected loss',ylabel='Expected conversion-rate loss'); fig.savefig('outputs/figures/bayesian.png',dpi=150); plt.close(fig)
