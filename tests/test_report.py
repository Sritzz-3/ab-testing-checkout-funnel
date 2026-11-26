import json
from pathlib import Path

def test_rendered_headlines():
    r=json.loads(Path('outputs/results.json').read_text()); s=Path('README.md').read_text(); assert f"{r['analysis']['control_rate']*100:.2f}%" in s; assert '{{' not in s
