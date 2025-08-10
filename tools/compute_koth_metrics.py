#!/usr/bin/env python3
import argparse, json, os, sys, xml.etree.ElementTree as ET, subprocess, pathlib

def read_cov_total(xml_path: str) -> float:
    if not os.path.exists(xml_path): return 0.0
    try:
        root = ET.parse(xml_path).getroot()
        # coverage.py XML has <lines-valid> & <lines-covered> totals in <coverage> or <packages>
        lines_valid = root.find(".//lines-valid")
        lines_covered = root.find(".//lines-covered")
        if lines_valid is not None and lines_covered is not None:
            v = float(lines_valid.text or 0.0); c = float(lines_covered.text or 0.0)
            return 0.0 if v <= 0 else c / v
        # fallback: look for 'line-rate' attr (Cobertura style)
        lr = root.attrib.get("line-rate")
        return float(lr) if lr else 0.0
    except Exception:
        return 0.0

def run_radon_avg_complexity(root_dir: str) -> float:
    try:
        out = subprocess.check_output(["radon", "cc", "-s", "-a", "-j", root_dir], text=True)
        data = json.loads(out or "{}")
        totals = []
        for file, items in data.items():
            for it in items:
                if isinstance(it, dict) and "complexity" in it:
                    totals.append(float(it["complexity"]))
        return sum(totals)/len(totals) if totals else 0.0
    except Exception:
        return 0.0

def read_ruff_count(json_path: str) -> int:
    if not os.path.exists(json_path): return 0
    try:
        arr = json.load(open(json_path)) or []
        return len(arr)
    except Exception:
        return 0

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pr", required=True, help="PR HEAD dir (.)")
    ap.add_argument("--base", required=True, help="baseline dir (checked out base)")
    ap.add_argument("--out-coverage", required=True)
    ap.add_argument("--out-quality", required=True)
    args = ap.parse_args()

    pr_cov = read_cov_total(os.path.join(args.pr, "coverage.xml"))
    base_cov = read_cov_total(os.path.join(args.base, "coverage.xml"))
    delta = round(pr_cov - base_cov, 6)

    pr_cc = run_radon_avg_complexity(args.pr)
    base_cc = run_radon_avg_complexity(args.base)
    cc_delta = round(pr_cc - base_cc, 6)  # negative is improvement

    lints = read_ruff_count(os.path.join(args.pr, "ruff.json"))

    cov = {"delta": delta, "new_total": round(pr_cov, 6)}
    qual = {"complexity_delta": cc_delta, "dup_delta": 0.0, "lints": int(lints)}

    pathlib.Path(args.out_coverage).write_text(json.dumps(cov))
    pathlib.Path(args.out_quality).write_text(json.dumps(qual))
    print("coverage:", cov)
    print("quality:", qual)

if __name__ == "__main__":
    main()
