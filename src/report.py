from __future__ import annotations
import json
import sys
import subprocess
from pathlib import Path
import pandas as pd

OWNER = "Sritzz-3"
REPO = "ab-testing-checkout-funnel"


def _pvalue(value):
    value = float(value)
    if value <= 0:
        return "<1e-300"
    if value < 0.001:
        return "<0.001"
    return f"{value:.3g}"


def _pct(value, digits=2):
    return f"{float(value) * 100:.{digits}f}%"


def _mark(value):
    return "PASS ✓" if bool(value) else "FAIL ✗"


def _markdown_table(headers, rows):
    lines = ["| " + " | ".join(headers) + " |", "|" + "|".join(["---"] * len(headers)) + "|"]
    lines.extend("| " + " | ".join(str(v) for v in row) + " |" for row in rows)
    return "\n".join(lines)


def render(results):
    template = Path("README.template.md").read_text(encoding="utf-8")
    c, a, v = results["config"], results["analysis"], results["validation"]
    table_dir = Path("outputs/tables")
    funnel = pd.read_csv(table_dir / "funnel.csv")
    guardrails = pd.read_csv(table_dir / "guardrails.csv")
    segments = pd.read_csv(table_dir / "segments.csv")
    balance = pd.read_csv(table_dir / "balance.csv")
    stability = pd.read_csv(table_dir / "time_stability.csv")
    design = pd.read_csv(table_dir / "design.csv").iloc[0]

    funnel_pivot = funnel.pivot(index="stage", columns="arm", values="rate")
    funnel_counts = funnel.pivot(index="stage", columns="arm", values="reached")
    funnel_table = _markdown_table(
        ["Funnel stage", "Control reached", "Control completion", "Treatment reached", "Treatment completion"],
        [[stage.replace("stage", "Stage "),
          f"{int(funnel_counts.loc[stage, 'control']):,}", _pct(funnel_pivot.loc[stage, "control"]),
          f"{int(funnel_counts.loc[stage, 'treatment']):,}", _pct(funnel_pivot.loc[stage, "treatment"])]
         for stage in funnel_pivot.index],
    )

    guardrail_rows = []
    for _, row in guardrails.iterrows():
        if row["guardrail"] == "AOV relative difference":
            measure = "AOV among converters (relative difference)"
            estimate = _pct(row["effect"])
            interval = f"one-sided 95% lower bound {_pct(row['ci_low'])}"
            margin = _pct(row["margin"])
            passed = row["pass"]
        else:
            measure = "Payment error rate difference"
            estimate = f"{row['effect'] * 100:+.2f} pp"
            interval = f"one-sided 95% upper bound {a['payment_error_upper'] * 100:+.2f} pp"
            margin = f"+{c['payment_error_margin'] * 100:.2f} pp"
            passed = row["pass"]
        guardrail_rows.append([measure, estimate, interval, margin, _mark(passed)])
    guardrail_table = _markdown_table(["Guardrail", "Estimate", "Confidence bound", "Limit", "Result"], guardrail_rows)

    segment_rows = []
    for _, row in segments.iterrows():
        segment_rows.append([
            row["dimension"].replace("_", " ").title(), row["segment"], _pct(row["relative_lift"]),
            f"{_pct(row['ci_low'])} to {_pct(row['ci_high'])}", _pvalue(row["holm_p_value"]),
        ])
    segment_table = _markdown_table(["Dimension", "Segment", "Relative lift", "95% CI", "Holm-adjusted p"], segment_rows)

    balance_table = _markdown_table(
        ["Covariate", "Balance p-value"],
        [[row["covariate"].replace("_", " ").title(), _pvalue(row["p_value"])] for _, row in balance.iterrows()],
    )

    stable_rows = []
    for week, group in stability.groupby("week", sort=True):
        by_arm = group.set_index("variant")
        p0 = float(by_arm.loc["control", "mean"])
        p1 = float(by_arm.loc["treatment", "mean"])
        stable_rows.append([week.replace("week", "Week "), _pct(p0), _pct(p1), _pct(p1 / p0 - 1)])
    stability_table = _markdown_table(["Window", "Control conversion", "Treatment conversion", "Relative lift"], stable_rows)

    planned_per_arm = int(c["n_sessions"] // 2)
    actual_sample = (
        f"Planned sample: about {planned_per_arm:,} per arm. Actual arm sizes: "
        f"{a['control_n']:,} control and {a['treatment_n']:,} treatment."
    )
    ci_above_zero = a["relative_ci_low"] > 0
    primary_pass = a["z_p_value"] < c["alpha"] and ci_above_zero
    aov_row = guardrails.loc[guardrails.guardrail == "AOV relative difference"].iloc[0]
    payment_row = guardrails.loc[guardrails.guardrail == "payment error difference"].iloc[0]
    criteria = "\n".join([
        f"- **Primary test:** two-sided p {_pvalue(a['z_p_value'])} at α={c['alpha']:.2f}; relative-lift 95% CI {_pct(a['relative_ci_low'])} to {_pct(a['relative_ci_high'])} (lower bound above 0): **{_mark(primary_pass)}**.",
        f"- **AOV non-inferiority:** relative difference {_pct(aov_row['effect'])}; one-sided 95% lower bound {_pct(aov_row['ci_low'])}, margin {_pct(aov_row['margin'])}: **{_mark(aov_row['pass'])}**.",
        f"- **Payment error margin:** rate difference {a['payment_error_difference'] * 100:+.2f} pp; one-sided 95% upper bound {a['payment_error_upper'] * 100:+.2f} pp, limit +{c['payment_error_margin'] * 100:.2f} pp: **{_mark(payment_row['pass'])}**.",
        f"- **No sample-ratio mismatch:** SRM p {_pvalue(v['srm_p_value'])}; flag threshold p<0.001, flagged={str(v['srm_flag']).lower()}: **{_mark(not v['srm_flag'])}**.",
    ])

    bayes_probability = a["bayes_probability_treatment_better"]
    bayes_text = ">99.99%" if bayes_probability >= 0.99995 else _pct(bayes_probability)
    runtime = float(results.get("runtime_seconds", 0))
    try:
        tree = subprocess.check_output(["git", "ls-files"], text=True).strip()
    except Exception as exc:
        raise RuntimeError("Could not generate README structure from git ls-files") from exc
    if not tree:
        raise ValueError("git ls-files returned an empty repository structure")

    values = {
        "github_path": f"{OWNER}/{REPO}",
        "control_rate_pct": f"{a['control_rate'] * 100:.2f}",
        "treatment_rate_pct": f"{a['treatment_rate'] * 100:.2f}",
        "relative_lift_pct": f"{a['relative_lift'] * 100:.2f}",
        "relative_ci_low_pct": f"{a['relative_ci_low'] * 100:.2f}",
        "relative_ci_high_pct": f"{a['relative_ci_high'] * 100:.2f}",
        "time_reduction_pct": f"{a['checkout']['median_reduction'] * 100:.2f}",
        "decision": a["decision"], "alpha": f"{c['alpha']:.2f}", "target_power": f"{c['power']:.2f}",
        "baseline_pct": f"{c['baseline_conversion'] * 100:.1f}", "mde_pct": f"{c['relative_lift'] * 100:.0f}",
        "required_n": f"{int(design['required_n_per_arm']):,}", "actual_sample": actual_sample,
        "control_n": f"{a['control_n']:,}", "treatment_n": f"{a['treatment_n']:,}",
        "control_conversions": f"{a['control_conversions']:,}", "treatment_conversions": f"{a['treatment_conversions']:,}",
        "control_wilson_low": f"{results['conversion'][0]['ci_low'] * 100:.2f}",
        "control_wilson_high": f"{results['conversion'][0]['ci_high'] * 100:.2f}",
        "treatment_wilson_low": f"{results['conversion'][1]['ci_low'] * 100:.2f}",
        "treatment_wilson_high": f"{results['conversion'][1]['ci_high'] * 100:.2f}",
        "absolute_lift_pp": f"{a['absolute_lift'] * 100:.2f}",
        "absolute_ci_low_pp": f"{a['absolute_ci_low'] * 100:.2f}", "absolute_ci_high_pp": f"{a['absolute_ci_high'] * 100:.2f}",
        "bootstrap_ci_low_pct": f"{a['bootstrap_ci_low'] * 100:.2f}", "bootstrap_ci_high_pct": f"{a['bootstrap_ci_high'] * 100:.2f}",
        "p_value": _pvalue(a["z_p_value"]), "chi_square_p": _pvalue(a["chi_square_p_value"]), "fisher_p": _pvalue(a["fisher_p_value"]),
        "adjusted_or": f"{a['adjusted_odds_ratio']:.3f}", "adjusted_or_low": f"{a['adjusted_or_ci_low']:.3f}", "adjusted_or_high": f"{a['adjusted_or_ci_high']:.3f}",
        "control_median": f"{a['checkout']['control_median']:.1f}", "treatment_median": f"{a['checkout']['treatment_median']:.1f}",
        "mean_reduction_pct": f"{a['checkout']['mean_reduction'] * 100:.2f}",
        "mann_whitney_p": _pvalue(a["checkout"]["mann_whitney_p"]), "welch_log_p": _pvalue(a["checkout"]["welch_log_p"]),
        "bayes_probability": bayes_text, "bayes_lift_pct": f"{a['bayes_relative_lift_mean'] * 100:.2f}",
        "bayes_ci_low_pct": f"{a['bayes_ci_low'] * 100:.2f}", "bayes_ci_high_pct": f"{a['bayes_ci_high'] * 100:.2f}",
        "srm_p": _pvalue(v["srm_p_value"]), "srm_flag": str(v["srm_flag"]).lower(),
        "aa_rate_pct": f"{v['aa_false_positive_rate'] * 100:.2f}", "aa_ci_low_pct": f"{v['aa_ci_low'] * 100:.2f}",
        "aa_ci_high_pct": f"{v['aa_ci_high'] * 100:.2f}", "empirical_power_pct": f"{v['empirical_power'] * 100:.2f}",
        "python_version": sys.version.split()[0], "seed": c["seed"], "runtime_seconds": f"{runtime:.2f}",
        "file_tree": tree, "funnel_table": funnel_table, "guardrail_table": guardrail_table,
        "segment_table": segment_table, "balance_table": balance_table, "stability_table": stability_table,
        "decision_criteria": criteria,
        "lift_explanation": (
            f"The configured base relative lift is {c['relative_lift'] * 100:.0f}%. The simulator increases "
            "the treatment effect for mobile visitors and new users, so their higher weighted contributions "
            "raise the sample-average estimate above the base assumption. The exploratory segment estimates "
            "below show the observed pattern."
        ),
    }
    for key, value in values.items():
        template = template.replace("{{" + key + "}}", str(value))
    if "{{" in template or "}}" in template or any(word in template for word in ["TODO", "TBD", "populated after"]):
        raise ValueError("README contains unresolved template language")
    Path("README.md").write_text(template, encoding="utf-8")
