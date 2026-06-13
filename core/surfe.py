"""Surfe email enrichment."""
import time
import requests
from typing import Dict, List, Optional

from .config import get_surfe_key

SURFE_BASE = "https://api.surfe.com"


def _headers() -> dict:
    return {"Authorization": f"Bearer {get_surfe_key()}", "Content-Type": "application/json"}


def credits_remaining() -> Optional[int]:
    try:
        r = requests.get(f"{SURFE_BASE}/v1/credits", headers=_headers(), timeout=10)
        return r.json().get("remaining")
    except Exception:
        return None


def enrich(leads: List[Dict]) -> Dict[str, Optional[str]]:
    """
    leads: list of dicts with linkedin_url, first_name, last_name.
    Returns {linkedin_url: email_or_None}.
    """
    people = [
        {
            "externalID": str(i),
            "firstName": l.get("first_name", ""),
            "lastName": l.get("last_name", ""),
            "linkedinUrl": l["linkedin_url"],
        }
        for i, l in enumerate(leads)
    ]

    r = requests.post(
        f"{SURFE_BASE}/v2/people/enrich",
        headers=_headers(),
        json={"include": {"email": True}, "people": people},
        timeout=30,
    )
    r.raise_for_status()
    enrichment_id = r.json()["enrichmentID"]

    result = _poll(enrichment_id)
    id_to_url = {str(i): l["linkedin_url"] for i, l in enumerate(leads)}

    out: Dict[str, Optional[str]] = {}
    for person in result.get("people", []):
        url = id_to_url.get(str(person.get("externalID", "")))
        emails = person.get("emails") or []
        valid_email = next(
            (e["email"] for e in emails if e.get("validationStatus") in ("VALID", "CATCH_ALL")),
            None,
        )
        if url:
            out[url] = valid_email
    return out


def _poll(enrichment_id: str, timeout: int = 120) -> Dict:
    deadline = time.time() + timeout
    while time.time() < deadline:
        r = requests.get(
            f"{SURFE_BASE}/v2/people/enrich/{enrichment_id}",
            headers=_headers(),
            timeout=15,
        )
        r.raise_for_status()
        data = r.json()
        if data.get("status") in ("COMPLETED", "DONE", "SUCCESS"):
            return data
        if data.get("status") in ("FAILED", "ERROR"):
            raise RuntimeError(f"Surfe enrichment failed: {enrichment_id}")
        time.sleep(8)
    raise TimeoutError("Surfe enrichment timed out")
