# tools/validator.py
from __future__ import annotations
import json, math, argparse, pathlib
from dataclasses import dataclass
from typing import Dict, List, Tuple

ROOT = pathlib.Path(__file__).resolve().parents[1]

# --- weights ---
VALUE_WEIGHTS = {"Low": 0.60, "Med": 0.80, "High": 0.95, "Critical": 1.00}
EFFORT_WEIGHTS = {"XS": 0.70, "S": 0.85, "M": 1.00, "L": 1.20, "XL": 1.50}

def clamp(x, lo=0.0, hi=1.0): return max(lo, min(hi, x))
def softmax(scores: Dict[str, float], tau: float) -> Dict[str, float]:
    if not scores: return {}
    m = max(scores.values())
    exps = {k: math.exp((v - m) / max(tau, 1e-8)) for k, v in scores.items()}
    s = sum(exps.values()) or 1.0
    return {k: v / s for k, v in exps.items()}

@dataclass
class RequirementMeta:
    rid: str
    value: str = "Med"
    effort: str = "M"
    perf_enabled: bool = False

def load_requirement_meta() -> Dict[str, RequirementMeta]:
    out: Dict[str, RequirementMeta] = {}
    for p in (ROOT / "requirements").glob("R-*.yaml"):
        rid = p.stem
        meta = RequirementMeta(rid)
        for line in p.read_text().splitlines():
            line = line.strip()
            if line.startswith("value:"): meta.value = line.split(":",1)[1].strip().title()
            elif line.startswith("effort:"): meta.effort = line.split(":",1)[1].strip().upper()
            elif line.startswith("perf_enabled:"): meta.perf_enabled = line.split(":",1)[1].strip().lower() in ("true","1","yes")
        out[rid] = meta
    return out

def load_registry() -> Dict[str, str]:
    # github_handle -> hotkey
    out: Dict[str, str] = {}
    for p in (ROOT / "registry" / "miners").glob("*.yaml"):
        gh = hk = None
        for line in p.read_text().splitlines():
            if line.startswith("github:"): gh = line.split(":",1)[1].strip().lstrip("@")
            elif line.startswith("hotkey_ss58:"): hk = line.split(":",1)[1].strip()
        if gh and hk: out[gh] = hk
    return out

def compute_Wr(meta: RequirementMeta) -> float:
    v = VALUE_WEIGHTS.get(meta.value, 0.80)
    e = EFFORT_WEIGHTS.get(meta.effort, 1.00)
    return min(1.5, v * e)

def S_spec(spec: dict) -> float:
    total = max(1, int(spec.get("total", 1)))
    passed = int(spec.get("passed", 0))
    return clamp(passed / total, 0, 1)

def S_tests(coverage: dict) -> float:
    delta = float(coverage.get("delta", 0.0))  # fraction (e.g., +0.05)
    return clamp(0.6 + 2.0 * delta, 0.0, 1.0)

def S_quality(q: dict) -> float:
    c = float(q.get("complexity_delta", 0.0))
    d = float(q.get("dup_delta", 0.0))
    lints = int(q.get("lints", 0))
    score = 0.85 + 0.25*max(-c,0) + 0.25*max(-d,0) - 0.5*max(c,0) - 0.5*max(d,0) - 0.05*min(lints,10)
    return clamp(score, 0.0, 1.0)

def S_perf(perf: dict, enabled: bool) -> float:
    if not enabled: return 0.0
    lat = float(perf.get("latency_ms_delta", 0.0))   # negative good
    thr = float(perf.get("throughput_delta", 0.0))   # positive good
    score = 0.5 + (-lat)/100.0 + 0.5*thr
    return clamp(score, 0.0, 1.0)

def requirement_score(k: dict, meta: RequirementMeta) -> float:
    wr = compute_Wr(meta)
    s = 0.50*S_spec(k.get("spec_checks", {})) \
      + 0.20*S_quality(k.get("quality", {})) \
      + 0.20*S_tests(k.get("coverage", {})) \
      + 0.10*S_perf(k.get("perf", {}), meta.perf_enabled)
    return max(0.0, min(2.0, wr * s))  # allow >1.0 due to Wr

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--epoch", required=True)
    ap.add_argument("--tau", type=float, default=0.5)
    ap.add_argument("--service-threshold", type=float, default=0.8)
    args = ap.parse_args()

    registry = load_registry()
    req_meta = load_requirement_meta()

    snap_dir = ROOT / "snapshots" / args.epoch
    if not snap_dir.exists():
        print(f"No snapshot dir {snap_dir}")
        return

    miner_scores: Dict[str, float] = {}
    scorecards: List[dict] = []

    for p in sorted(snap_dir.glob("pr-*.json")):
        k = json.loads(p.read_text())
        rid = (k.get("requirement") or "").strip()
        gh = (k.get("miner_github") or "").lstrip("@")
        hotkey = k.get("hotkey") or registry.get(gh, "")
        if not rid or not hotkey:
            # unregistered or malformed
            print(f"skip {p.name}: rid/hotkey missing")
            continue
        meta = req_meta.get(rid, RequirementMeta(rid))
        rs = requirement_score(k, meta)
        miner_scores[hotkey] = miner_scores.get(hotkey, 0.0) + rs
        scorecards.append({"rid": rid, "github": gh, "hotkey": hotkey, "score": round(rs,6)})

    # softmax miner weights
    miner_weights = softmax(miner_scores, args.tau) if miner_scores else {}

    # service miner slice
    svc_file = ROOT / "service_sla" / f"{args.epoch}.json"
    svc_share, svc_hotkey = 0.0, ""
    if svc_file.exists():
        svc = json.loads(svc_file.read_text())
        svc_hotkey = svc.get("hotkey", "")
        budget = float(svc.get("budget", 0.0))  # e.g., 0.075
        svc_score = float(svc.get("service_score", 0.0))
        if svc_score >= args.service_threshold and svc_hotkey:
            svc_share = min(0.2, max(0.0, budget * svc_score))  # cap safety

    final: Dict[str, float] = {}
    if miner_weights:
        scale = 1.0 - svc_share
        for hk, w in miner_weights.items():
            final[hk] = w * scale
    if svc_share and svc_hotkey:
        final[svc_hotkey] = final.get(svc_hotkey, 0.0) + svc_share

    # normalize
    s = sum(final.values()) or 1.0
    final = {k: v/s for k, v in final.items()}

    out = {
        "epoch": args.epoch,
        "tau": args.tau,
        "value_weights": VALUE_WEIGHTS,
        "effort_weights": EFFORT_WEIGHTS,
        "service": {"applied_share": svc_share, "hotkey": svc_hotkey},
        "miners": [{"hotkey": hk, "weight": round(w,10), "raw_score": round(miner_scores.get(hk,0.0),6)} 
                   for hk, w in sorted(final.items(), key=lambda kv: kv[1], reverse=True)],
        "scorecards": scorecards
    }
    out_path = ROOT / "weights" / f"{args.epoch}.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2))
    print(f"Wrote {out_path}")

if __name__ == "__main__":
    main()
