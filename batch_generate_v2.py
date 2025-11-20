#!/usr/bin/env python3
"""
Robust batch generator v2
- Improved handling for 429 (Too Many Requests)
- Exponential backoff with jitter
- Resume capability
- Writes outputs incrementally
Usage:
  python batch_generate_v2.py --input sample_products.csv --out outputs --delay 1 --start 0
"""

import csv
import json
import os
import time
import argparse
import traceback
import math
import random
from hashlib import md5
from datetime import datetime

from generator import generate  # generate(name, features) -> (result_json_dict, seo_report_dict)

# ---------- Helpers ----------
def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def slugify(text: str) -> str:
    s = text.lower().strip()
    s = "".join(c if c.isalnum() or c in "-_ " else "-" for c in s)
    s = "-".join(s.split())
    return s[:60]

def ensure_dirs(base_out: str):
    desc_dir = os.path.join(base_out, "descriptions")
    seo_dir = os.path.join(base_out, "seo_reports")
    combined_dir = os.path.join(base_out, "combined")
    os.makedirs(desc_dir, exist_ok=True)
    os.makedirs(seo_dir, exist_ok=True)
    os.makedirs(combined_dir, exist_ok=True)
    return desc_dir, seo_dir, combined_dir

def read_csv_rows(csv_path: str):
    with open(csv_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    return rows

def safe_write_json(path: str, obj):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)

def append_combined_row(csv_path: str, row_dict: dict, header: list):
    exists = os.path.exists(csv_path)
    with open(csv_path, "a", newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=header)
        if not exists:
            writer.writeheader()
        writer.writerow(row_dict)

# ---------- Backoff utilities ----------
def calc_backoff(attempt: int, base: float, cap: float, jitter: float = 0.3):
    """Exponential backoff with jitter. attempt is 0-based."""
    expo = base * (2 ** attempt)
    # add jitter +/- jitter*expo
    jitter_amt = expo * jitter
    val = expo + random.uniform(-jitter_amt, jitter_amt)
    return min(max(0.5, val), cap)

# ---------- Main ----------
def main():
    p = argparse.ArgumentParser()
    p.add_argument("--input", required=True, help="CSV path with columns: name,features,category,audience,keywords")
    p.add_argument("--out", default="outputs", help="Output folder")
    p.add_argument("--delay", type=float, default=1.0, help="Base delay between successful calls (seconds)")
    p.add_argument("--start", type=int, default=0, help="Start index (zero-based)")
    p.add_argument("--max", type=int, default=0, help="Max items to process (0 = all)")
    p.add_argument("--max-retries", type=int, default=5, help="Max retries for transient errors")
    p.add_argument("--max-backoff", type=float, default=60.0, help="Max backoff seconds for 429s")
    p.add_argument("--backoff-base", type=float, default=2.0, help="Backoff base seconds")
    p.add_argument("--fast-mode", action="store_true", help="Attempt to reduce optional LLM refine calls (if generator supports it)")
    p.add_argument("--delay-increase-factor", type=float, default=1.5, help="Factor to increase base delay after repeated 429s")
    args = p.parse_args()

    rows = read_csv_rows(args.input)
    total = len(rows)
    print(f"{now()} - Loaded {total} products from {args.input}")

    desc_dir, seo_dir, combined_dir = ensure_dirs(args.out)
    combined_csv = os.path.join(combined_dir, "combined.csv")

    header = [
        "index","name","category","audience","keywords","features",
        "description_file","seo_file","title","meta_description","short_description","status","error"
    ]

    end_index = total if args.max == 0 else min(total, args.start + args.max)

    base_delay = args.delay
    consecutive_429 = 0

    for idx in range(args.start, end_index):
        row = rows[idx]
        name = (row.get("name") or "").strip()
        features = (row.get("features") or "").strip()
        category = (row.get("category") or "").strip()
        audience = (row.get("audience") or "").strip()
        keywords = (row.get("keywords") or "").strip()

        slug = slugify(name) or f"item-{idx}"
        short_hash = md5((name + features).encode("utf-8")).hexdigest()[:6]
        filename_base = f"{idx:03d}_{slug}_{short_hash}"
        desc_file = os.path.join(desc_dir, f"{filename_base}.json")
        seo_file = os.path.join(seo_dir, f"{filename_base}_seo.json")

        # Resume safe: skip if both files exist
        if os.path.exists(desc_file) and os.path.exists(seo_file):
            print(f"{now()} - [{idx+1}/{total}] SKIP (exists): {name}")
            continue

        print(f"{now()} - [{idx+1}/{total}] START: {name}")

        attempt = 0
        success = False
        last_err_msg = ""
        while attempt <= args.max_retries and not success:
            try:
                # Optionally, set fast-mode env var to influence generator behavior if implemented.
                if args.fast_mode:
                    os.environ["PDG_FAST_MODE"] = "1"
                else:
                    if "PDG_FAST_MODE" in os.environ:
                        os.environ.pop("PDG_FAST_MODE", None)

                result, seo_report = generate(name, features)
                # Save outputs
                safe_write_json(desc_file, result)
                safe_write_json(seo_file, seo_report)

                combined_row = {
                    "index": idx,
                    "name": name,
                    "category": category,
                    "audience": audience,
                    "keywords": keywords,
                    "features": features,
                    "description_file": os.path.relpath(desc_file, args.out),
                    "seo_file": os.path.relpath(seo_file, args.out),
                    "title": result.get("title",""),
                    "meta_description": result.get("meta_description",""),
                    "short_description": result.get("short_description",""),
                    "status": "OK",
                    "error": ""
                }
                append_combined_row(combined_csv, combined_row, header)

                print(f"{now()} - [{idx+1}/{total}] DONE: {filename_base}.json")
                success = True
                consecutive_429 = 0  # reset
                # polite base delay after success
                time.sleep(base_delay)
            except Exception as e:
                # Inspect exception to detect 429 or server busy
                last_err_msg = str(e)
                attempt += 1

                # Default wait using exponential backoff + jitter
                wait = calc_backoff(attempt-1, args.backoff_base, args.max_backoff, jitter=0.3)

                # If HTTPError with Retry-After header available, use that
                try:
                    import requests
                    if isinstance(e, requests.exceptions.HTTPError) and e.response is not None:
                        # try to extract Retry-After
                        ra = e.response.headers.get("Retry-After")
                        status_code = getattr(e.response, "status_code", None)
                        if ra:
                            try:
                                ra_val = float(ra)
                                wait = min(ra_val + 1.0, args.max_backoff)
                            except:
                                pass
                        if status_code == 429:
                            # increase consecutive 429 counter
                            consecutive_429 += 1
                            # gradually increase base_delay to be gentler
                            base_delay = base_delay * args.delay_increase_factor
                except Exception:
                    pass

                print(f"{now()} - [{idx+1}/{total}] ERROR attempt {attempt}/{args.max_retries} for '{name}': {last_err_msg}")
                traceback.print_exc()

                if attempt <= args.max_retries:
                    print(f"{now()} - Waiting {wait:.1f}s before retrying...")
                    time.sleep(wait)
                else:
                    print(f"{now()} - FAILED after {args.max_retries} retries: {name}")
                    # write failed row
                    failed_row = {
                        "index": idx,
                        "name": name,
                        "category": category,
                        "audience": audience,
                        "keywords": keywords,
                        "features": features,
                        "description_file": "FAILED",
                        "seo_file": "FAILED",
                        "title": "",
                        "meta_description": f"ERROR: {last_err_msg}",
                        "short_description": "",
                        "status": "FAILED",
                        "error": last_err_msg
                    }
                    append_combined_row(combined_csv, failed_row, header)
                    break

        # small extra delay to reduce burstiness if we had many 429s
        if consecutive_429 > 0:
            extra = min(5 * consecutive_429, args.max_backoff)
            print(f"{now()} - Detected {consecutive_429} consecutive 429s; sleeping extra {extra}s to recover.")
            time.sleep(extra)

    print(f"{now()} - Batch generation complete.")
    print(f"Descriptions -> {desc_dir}")
    print(f"SEO reports -> {seo_dir}")
    print(f"Combined CSV -> {combined_csv}")

if __name__ == "__main__":
    main()
