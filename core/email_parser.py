"""Parse the JSON array that Claude Teams returns and merge into lead records."""
import json
import re
from typing import List, Dict, Tuple


def parse_claude_response(raw: str) -> Tuple[List[Dict], str]:
    """
    Extract the JSON array from Claude's response.
    Returns (list_of_email_dicts, error_message_or_empty).
    """
    raw = raw.strip()

    # Strip markdown code fences if present
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)

    # Find the first [ ... ] block
    match = re.search(r"\[.*\]", raw, re.DOTALL)
    if not match:
        return [], "Could not find a JSON array in the pasted text. Make sure you copied the full response."

    try:
        data = json.loads(match.group())
    except json.JSONDecodeError as e:
        return [], f"JSON parse error: {e}. Try copying the Claude response again."

    if not isinstance(data, list):
        return [], "Expected a JSON array but got something else."

    results = []
    for item in data:
        if not isinstance(item, dict):
            continue
        if "linkedin_url" not in item or "email" not in item:
            continue
        results.append({
            "linkedin_url": item.get("linkedin_url", ""),
            "subject": item.get("subject", ""),
            "email_body": item.get("email", ""),
        })

    if not results:
        return [], "JSON parsed but no valid email entries found. Each entry needs linkedin_url and email."

    return results, ""


def merge_emails_into_leads(leads: List[Dict], email_results: List[Dict]) -> List[Dict]:
    """Merge generated emails back into lead records by linkedin_url."""
    email_map = {e["linkedin_url"]: e for e in email_results}
    for lead in leads:
        match = email_map.get(lead.get("linkedin_url", ""))
        if match:
            lead["subject"] = match["subject"]
            lead["email_body"] = match["email_body"]
    return leads
