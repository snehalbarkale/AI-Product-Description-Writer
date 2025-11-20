import argparse
import json
import os
from model_client import call_llm

# -----------------------------------------
# FAST MODE TOGGLE
# -----------------------------------------
FAST_MODE = os.getenv("PDG_FAST_MODE") == "1"

# -----------------------------------------
# Prompt Template
# -----------------------------------------
PROMPT = """
Generate a detailed, SEO-optimized product description in valid JSON only.

Product Name: "{name}"
Features: "{features}"

Return ONLY JSON with the following structure:

{
  "title": "...",
  "meta_description": "...",
  "short_description": "...",
  "long_description": "...",
  "bullets": ["...", "..."],
  "keywords": ["...", "..."],
  "website": {
    "hero_blurb": "...",
    "tagline": "...",
    "website_description": "...",
    "website_bullets": ["...", "..."]
  },
  "title_suggestions": ["...", "..."],
  "meta_suggestions": ["...", "..."]
}
"""

# -----------------------------------------
# SEO Calculation (Normal Mode Only)
# -----------------------------------------
def calculate_seo(data):
    title = data.get("title", "")
    meta = data.get("meta_description", "")
    keywords = data.get("keywords", [])

    metrics = {
        "title_length": len(title),
        "meta_length": len(meta),
        "title_has_primary": {},
        "meta_has_primary": {},
        "keyword_density": {}
    }

    long_desc = data.get("long_description", "").lower()

    for kw in keywords:
        k_low = kw.lower()
        metrics["title_has_primary"][kw] = k_low in title.lower()
        metrics["meta_has_primary"][kw] = k_low in meta.lower()
        metrics["keyword_density"][kw] = long_desc.count(k_low)

    suggestions = []

    for kw, found in metrics["title_has_primary"].items():
        if not found:
            suggestions.append(f"Primary keyword '{kw}' not found in title.")

    for kw, found in metrics["meta_has_primary"].items():
        if not found:
            suggestions.append(f"Primary keyword '{kw}' not found in meta description.")

    return {
        "metrics": metrics,
        "suggestions": suggestions
    }

# -----------------------------------------
# Safe JSON Loader (repairs JSON)
# -----------------------------------------
def safe_json_load(raw_output):
    try:
        return json.loads(raw_output)
    except:
        # Ask model to fix JSON
        fix_prompt = f"Fix this and return VALID JSON only:\n{raw_output}"
        fixed = call_llm(fix_prompt)
        return json.loads(fixed)

# -----------------------------------------
# GENERATE FUNCTION (CORE)
# -----------------------------------------
def generate(name, features):
    prompt = PROMPT.format(name=name, features=features)

    # Step 1: Query LLM
    raw_output = call_llm(prompt)

    # Step 2: JSON extract/repair
    try:
        data = json.loads(raw_output)
    except:
        data = safe_json_load(raw_output)

    # ------------------------------
    # FAST MODE — Skip heavy SEO work
    # ------------------------------
    if FAST_MODE:
        seo_report = {
            "metrics": {
                "title_length": len(data.get("title", "")),
                "meta_length": len(data.get("meta_description", "")),
            },
            "suggestions": []
        }
        return data, seo_report

    # ------------------------------
    # NORMAL MODE — Full SEO
    # ------------------------------
    seo_report = calculate_seo(data)

    return data, seo_report

# -----------------------------------------
# MAIN ENTRYPOINT (CLI)
# -----------------------------------------
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", required=True)
    parser.add_argument("--features", required=True)
    args = parser.parse_args()

    result, seo_report = generate(args.name, args.features)

    print("\n======================")
    print("=== PRODUCT OUTPUT ===")
    print("======================")
    print(json.dumps(result, indent=2))

    print("\n=================")
    print("=== SEO REPORT ===")
    print("=================")
    print(json.dumps(seo_report, indent=2))


if __name__ == "__main__":
    main()
