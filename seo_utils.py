# seo_utils.py
import re
from typing import List, Dict, Any
from model_client import call_llm

# --- simple utilities ---
def normalize_kw_list(keywords) -> List[str]:
    if not keywords:
        return []
    if isinstance(keywords, str):
        kws = [k.strip() for k in keywords.split(",") if k.strip()]
    elif isinstance(keywords, list):
        kws = [str(k).strip() for k in keywords if str(k).strip()]
    else:
        kws = []
    return [k.lower() for k in kws]

def count_occurrences(text: str, token: str) -> int:
    if not text or not token:
        return 0
    return len(re.findall(r"\b" + re.escape(token) + r"\b", text.lower()))

# --- Analyzer (metrics + suggestions) ---
def analyze_seo(product_texts: Dict[str, Any], primary_keywords: List[str]) -> Dict[str, Any]:
    """
    product_texts: expects keys 'title','meta_description','long_description'
    primary_keywords: list of primary keywords (lowercased)
    returns: metrics and suggestions
    """
    title = (product_texts.get("title") or "").strip()
    meta = (product_texts.get("meta_description") or "").strip()
    long = (product_texts.get("long_description") or "").strip()
    kws = [k.lower() for k in primary_keywords]

    metrics = {}
    metrics["title_length"] = len(title)
    metrics["meta_length"] = len(meta)
    metrics["title_has_primary"] = {k: (count_occurrences(title, k) > 0) for k in kws}
    metrics["meta_has_primary"] = {k: (count_occurrences(meta, k) > 0) for k in kws}
    # keyword density in long_description per keyword (words)
    long_words = len(re.findall(r"\w+", long)) or 1
    metrics["keyword_density"] = {k: round(100.0 * count_occurrences(long, k) / long_words, 3) for k in kws}

    suggestions = []
    if metrics["title_length"] > 60:
        suggestions.append("Title is longer than 60 chars — consider shortening to <=60 chars, keep primary keyword near start.")
    if metrics["meta_length"] > 160:
        suggestions.append("Meta description exceeds 160 chars — shorten to 120-155 chars and include primary keyword once.")
    for k, present in metrics["title_has_primary"].items():
        if not present:
            suggestions.append(f"Primary keyword '{k}' not found in title — consider adding it near the start.")
    for k, present in metrics["meta_has_primary"].items():
        if not present:
            suggestions.append(f"Primary keyword '{k}' not found in meta description — include it naturally.")
    # density check: warn if density > 3% or = 0
    for k, dens in metrics["keyword_density"].items():
        if dens == 0:
            suggestions.append(f"Primary keyword '{k}' not found in long description — include it naturally.")
        elif dens > 3.0:
            suggestions.append(f"Keyword '{k}' density in description is {dens}%. Consider reducing repetition to avoid keyword stuffing (aim <3%).")

    return {"metrics": metrics, "suggestions": suggestions}

# --- Light auto-fixes (non-LLM) ---
def truncate_to_words(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    # cut at last whitespace before max_chars
    trunc = text[:max_chars+1].rsplit(" ", 1)[0]
    return trunc.rstrip(" ,.-")  # tidy up

def ensure_title_meta_constraints(result: Dict[str, Any], primary_keywords: List[str]) -> Dict[str, Any]:
    """
    Simple safety fixes:
      - Ensure title <= 60 chars (truncate if needed)
      - Ensure meta <= 160 chars (truncate if needed)
      - If primary keyword missing from title, prepend keyword (if short enough)
    """
    title = (result.get("title") or "").strip()
    meta = (result.get("meta_description") or "").strip()
    kws = normalize_kw_list(primary_keywords)

    # If title too long, truncate
    if len(title) > 60:
        title = truncate_to_words(title, 60)
    # If meta too long, truncate
    if len(meta) > 160:
        meta = truncate_to_words(meta, 160)

    # If no primary keyword in title, try to add first keyword at start if space allows
    if kws:
        first_kw = kws[0]
        if count_occurrences(title, first_kw) == 0:
            candidate = f"{first_kw.capitalize()} — {title}"
            if len(candidate) <= 60:
                title = candidate
            else:
                # try placing keyword + short form
                short_candidate = f"{first_kw.capitalize()} {title}"
                if len(short_candidate) <= 60:
                    title = short_candidate
                # else keep original truncated title

    result["title"] = title
    result["meta_description"] = meta
    return result

# --- Use LLM to propose optimized title/meta suggestions (optional but recommended) ---
def llm_refine_title_meta(product_input: Dict[str, Any], primary_keywords: List[str], n_titles: int = 3) -> Dict[str, Any]:
    """
    Ask the LLM to propose title and meta variants that respect length constraints.
    Returns a dict: { "title_suggestions": [...], "meta_suggestions":[...] }
    """
    kws = ", ".join(primary_keywords) if primary_keywords else ""
    short_prompt = f"""
You are an SEO copywriter. Given this product info, produce {n_titles} SEO-friendly title suggestions (<=60 chars) and {n_titles} meta description suggestions (<=160 chars).
Product JSON:
{product_input}

Primary keywords: {kws}

Output JSON ONLY in this structure:
{{
  "titles": ["...","..."],
  "metas": ["...","..."]
}}
"""
    raw = call_llm(short_prompt)
    # Try to parse JSON block
    import json, re
    m = re.search(r"\{.*\}", raw, flags=re.DOTALL)
    if not m:
        raise RuntimeError("LLM did not return JSON for title/meta suggestions:\n" + raw)
    return json.loads(m.group(0))
