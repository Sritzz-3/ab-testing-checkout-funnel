from __future__ import annotations
import os
os.environ.setdefault("MPLBACKEND", "Agg")

import json, logging, time
from pathlib import Path
import pandas as pd
from .config import load_config
from .simulator import simulate_sessions
from .design import build_design
from .validation import validate
from .analysis import analyze
from .plots import make_plots
from .report import render

def main():
    logging.basicConfig(level=logging.INFO,format='%(asctime)s %(levelname)s %(message)s'); start=time.time(); c=load_config()
    for p in ['outputs/figures','outputs/tables','data/raw']: Path(p).mkdir(parents=True,exist_ok=True)
    logging.info('Simulating sessions'); df=simulate_sessions(c); df.to_csv('data/raw/sessions.csv',index=False)
    logging.info('Computing design'); n=build_design(c); logging.info('Running integrity checks'); v=validate(df,c); logging.info('Analyzing experiment'); a=analyze(df,c)
    conversion=pd.read_csv('outputs/tables/conversion.csv').to_dict(orient='records')
    logging.info('Rendering figures'); make_plots(a); results={'config':c,'design':n,'validation':v,'analysis':a,'conversion':conversion}; results['runtime_seconds']=time.time()-start
    Path('outputs/results.json').write_text(json.dumps(results,indent=2,allow_nan=False),encoding='utf-8'); render(results); logging.info('Finished in %.2f seconds; verdict %s',results['runtime_seconds'],a['decision'])
if __name__=='__main__': main()
