#!/usr/bin/env python3
"""
Batch generator for product-description-generator.

Usage:
  python batch_generate.py --input sample_products.csv --out outputs --delay 1 --start 0

Options:
  --input    CSV file with columns: name,features,category,audience,keywords
  --out      Output folder (default: outputs)
  --delay    Seconds to wait between API calls (default: 1)
  --start    Zero-based start index (default: 0)
  --max      Max products to process (0 = all)
  --retry    Number of retries on error (default: 2)
"""

import csv
import json
import os
import time
import argparse
import traceback
from hashlib import md5
from urllib.parse import quote_plus

# Import your generator function
# It must be reachable as: from generator import generate
# generate(name, features) -> (result_json_dict, seo_report_dict)
from generator import generate

def slugify(text: str) -> str:
    s = text.lower().strip()
    # safe filename characters only
    s = "".join(c if c.isalnum() or c in "-_ " else "-" for c in s)
    s = "-".join(s.split())
    # shorten
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
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)

def append_combined_row(csv_path: str, row_dict: dict, header: list):
    exists = os.path.exists(csv_path)
    with open(csv_path, "a", newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=header)
        if not exists:
            writer.writeheader()
        writer.writerow(row_dict)

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--input", required=True)
    p.add_argument("--out", default="outputs")
    p.add_argument("--delay", type=float, default=1.0)
    p.add_argument("--start", type=int, default=0)
    p.add_argument("--max", type=int, default=0)
    p.add_argument("--retry", type=int, default=2)
    args = p.parse_args()

    csv_path = args.input
    base_out = args.out
    delay = args.delay
    start_index = args.start
    max_items = args.max
    retries = args.retry

    desc_dir, seo_dir, combined_dir = ensure_dirs(base_out)
    combined_csv = os.path.join(combined_dir, "combined.csv")

    rows = read_csv_rows(csv_path)
    total = len(rows)
    print(f"Loaded {total} products from {csv_path}")

    # define header for combined CSV
    header = [
        "index","name","category","audience","keywords","features",
        "description_file","seo_file","title","meta_description","short_description"
    ]

    end_index = total if max_items == 0 else min(total, start_index + max_items)

    for idx in range(start_index, end_index):
        row = rows[idx]
        try:
            name = row.get("name","").strip()
            features = row.get("features","").strip()
            category = row.get("category","").strip()
            audience = row.get("audience","").strip()
            keywords = row.get("keywords","").strip()

            slug = slugify(name) or f"item-{idx}"
            # ensure unique filename in case of duplicates
            short_hash = md5((name + features).encode("utf-8")).hexdigest()[:6]
            filename_base = f"{idx:03d}_{slug}_{short_hash}"

            desc_file = os.path.join(desc_dir, f"{filename_base}.json")
            seo_file = os.path.join(seo_dir, f"{filename_base}_seo.json")

            # If outputs already exist, skip (resume capability)
            if os.path.exists(desc_file) and os.path.exists(seo_file):
                print(f"[{idx+1}/{total}] Skipping (already exists): {name}")
                continue

            print(f"[{idx+1}/{total}] Generating: {name}")

            attempt = 0
            last_exc = None
            while attempt <= retries:
                try:
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
                        "description_file": os.path.relpath(desc_file, base_out),
                        "seo_file": os.path.relpath(seo_file, base_out),
                        "title": result.get("title",""),
                        "meta_description": result.get("meta_description",""),
                        "short_description": result.get("short_description","")
                    }
                    append_combined_row(combined_csv, combined_row, header)
                    print(f"[{idx+1}/{total}] Saved: {filename_base}.json")
                    break
                except Exception as e:
                    attempt += 1
                    last_exc = e
                    print(f"  Error on attempt {attempt}/{retries} for '{name}': {e}")
                    traceback.print_exc()
                    wait = 2 ** attempt
                    print(f"  Waiting {wait}s before retrying...")
                    time.sleep(wait)
            else:
                # all retries failed
                print(f"[{idx+1}/{total}] FAILED after {retries} retries: {name}")
                # record failed row with error info
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
                    "meta_description": f"ERROR: {str(last_exc)}",
                    "short_description": ""
                }
                append_combined_row(combined_csv, failed_row, header)

            # polite delay between calls
            time.sleep(delay)

        except KeyboardInterrupt:
            print("Interrupted by user. Exiting.")
            break

    print("Batch generation complete.")
    print(f"Descriptions -> {desc_dir}")
    print(f"SEO reports -> {seo_dir}")
    print(f"Combined CSV -> {combined_csv}")

if __name__ == "__main__":
    main()
