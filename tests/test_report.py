import json
import re
from pathlib import Path

OWNER = "Sritzz-3"
REPO = "ab-testing-checkout-funnel"


def test_rendered_report_content():
    results = json.loads(Path("outputs/results.json").read_text())
    text = Path("README.md").read_text()

    assert f"{results['analysis']['control_rate'] * 100:.2f}%" in text
    assert "{{" not in text and "}}" not in text
    assert "p=0" not in text.lower()
    assert "{'" not in text
    owners = re.findall(r"github\.com/([^/]+)/" + re.escape(REPO), text)
    assert owners and set(owners) == {OWNER}
    assert "### Funnel completion by arm" in text
    assert "### Guardrails" in text
    assert "### Segment lift (exploratory)" in text
    assert "### Covariate balance" in text
    assert "### Week 1 vs week 2 stability" in text
    assert "Why the estimated lift exceeds the base assumption" in text
    assert ">99.99%" in text
    assert "about 12,000 per arm" in text
    assert "12,068 control" in text and "11,932 treatment" in text
