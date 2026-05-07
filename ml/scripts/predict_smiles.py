#!/usr/bin/env python3
"""
Run one PharmaSim prediction from the terminal (SMILES or preset id).

From the repository root, with the venv activated:

  python ml/scripts/predict_smiles.py "CCO"
  python ml/scripts/predict_smiles.py --json "CC(=O)Nc1ccc(O)cc1"
  echo "CCO" | python ml/scripts/predict_smiles.py
  python ml/scripts/predict_smiles.py -c tylenol --dose 500
  python ml/scripts/predict_smiles.py -c thalidomide

API alternative (server must be running):

  curl -s -X POST http://127.0.0.1:8001/predict \\
    -H 'Content-Type: application/json' \\
    -d '{"drug_name":"me","smiles":"CCO","dose_mg":100}'
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from ml.src.pipeline import PredictRequest, run_predict  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Local PharmaSim test: one SMILES string or --compound preset.",
    )
    parser.add_argument(
        "smiles",
        nargs="?",
        default="",
        help="SMILES (optional if --compound or stdin)",
    )
    parser.add_argument(
        "-c",
        "--compound",
        metavar="ID",
        help="Preset compound_id (e.g. acetaminophen, tylenol, thalidomide)",
    )
    parser.add_argument("--dose", type=float, default=100.0, help="Dose in mg (default 100)")
    parser.add_argument("--name", default="", help="Display drug name when using raw SMILES")
    parser.add_argument(
        "-j",
        "--json",
        action="store_true",
        help="Print full JSON response (large: includes pk_curve)",
    )
    args = parser.parse_args()

    smiles = (args.smiles or "").strip()
    if not smiles and not sys.stdin.isatty():
        smiles = sys.stdin.read().strip()

    if not smiles and not args.compound:
        parser.error("Provide SMILES, pipe SMILES on stdin, or use --compound")

    drug_name = args.name
    if not drug_name and smiles and not args.compound:
        drug_name = "test"

    req = PredictRequest(
        drug_name=drug_name,
        smiles=smiles,
        dose_mg=args.dose,
        compound_id=args.compound,
    )
    out = run_predict(req)
    if hasattr(out, "code"):
        print(f"Error [{out.code}]: {out.message}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(out, indent=2, default=str))
        return 0

    c = out.get("compound") or {}
    ad = out.get("admet_ai") or {}
    tr = out.get("trial_recommendation") or {}
    ss = out.get("safety_score") or {}
    tox = out.get("toxicity") or {}
    print(f"name:        {c.get('name')}")
    print(f"SMILES:      {c.get('smiles')}")
    print(f"compound_id: {c.get('compound_id')}")
    print(f"verdict:     {out.get('verdict')}")
    print(f"trial:       {tr.get('verdict')} — {tr.get('title')}")
    print(f"safety:      {ss.get('score')} ({ss.get('label')})")
    print(f"admet:       used={ad.get('used')}  error={ad.get('error')}")
    print(f"hepatox:     {tox.get('hepatotoxicity')}  overall_tox: {tox.get('overall_toxicity')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
