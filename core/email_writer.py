"""Direct Claude API email generation — no copy-paste needed."""
import json
from typing import List, Dict

import anthropic

from .config import get_anthropic_key

_client = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=get_anthropic_key())
    return _client


SALES_SYSTEM = """\
You write warm, personalised cold outreach emails for Sam at EduSpark (eduspark.world).

EduSpark is a professional online learning platform for educators. Award winner: EduTech Asia \
Best EdTech Deployment K-12 2025. Key courses: Kath Murdoch on inquiry, Tania Lattanzio and \
Dr. Jennifer Chang Wathall on UDL, safeguarding, leadership. Free/Pro/Spark+ tiers.

Rules — no exceptions:
- No em dashes. Use commas or full stops instead.
- No bullet points. Flowing prose only.
- UK spelling throughout.
- Subject: 8-12 words, conversational, references their role or location specifically.
- Body: 4 short paragraphs.
  1. Acknowledge their role and context — what it means to be in that position, in that city/country.
  2. Introduce Sam and EduSpark in one sentence, naturally.
  3. One clear value relevant to their role.
  4. Warm, low-pressure invite. CTA: eduspark.world/book-a-demo
- Sign-off: Best wishes, / Sam / EduSpark | eduspark.world

Return ONLY a JSON array — no markdown fences, no extra text:
[{"linkedin_url":"...","subject":"...","email":"..."}]"""


CREATOR_SYSTEM = """\
You write warm, personalised creator-invitation emails for Sam at EduSpark (eduspark.world).

EduSpark is building a community of world-class educator-creators who build courses and reach \
a global audience of professional educators. Creators earn revenue, grow their brand, and \
contribute to a mission-driven community.

Rules — no exceptions:
- No em dashes. Use commas or full stops instead.
- No bullet points. Flowing prose only.
- UK spelling throughout.
- Subject: 8-12 words, references their specific expertise or a post they wrote.
- Body: 4 short paragraphs.
  1. Specific observation from their posts or work — never a generic opener.
  2. Introduce Sam and EduSpark as a creator platform in one sentence.
  3. Why their specialty is exactly what EduSpark's educator audience needs.
  4. Warm, low-pressure invite. CTA: eduspark.world/become-a-creator
- Sign-off: Best wishes, / Sam / EduSpark | eduspark.world

Return ONLY a JSON array — no markdown fences, no extra text:
[{"linkedin_url":"...","subject":"...","email":"..."}]"""


def _call(system: str, leads_text: str) -> List[Dict]:
    resp = _get_client().messages.create(
        model="claude-opus-4-8",
        max_tokens=8000,
        system=system,
        messages=[{"role": "user", "content": f"Generate emails for these leads:\n\n{leads_text}"}],
    )
    raw = resp.content[0].text.strip()
    # Strip markdown fences if present
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1].rsplit("```", 1)[0]
    return json.loads(raw)


def _format_sales(leads: List[Dict]) -> str:
    lines = []
    for i, l in enumerate(leads):
        lines += [
            f"Lead {i+1}:",
            f"  linkedin_url: {l.get('linkedin_url','')}",
            f"  name: {l.get('first_name','')} {l.get('last_name','')}",
            f"  role: {l.get('role','')}",
            f"  city: {l.get('city','')}",
            f"  country: {l.get('country','')}",
            "",
        ]
    return "\n".join(lines)


def _format_creator(leads: List[Dict]) -> str:
    lines = []
    for i, l in enumerate(leads):
        lines += [
            f"Lead {i+1}:",
            f"  linkedin_url: {l.get('linkedin_url','')}",
            f"  name: {l.get('first_name','')} {l.get('last_name','')}",
            f"  specialty: {l.get('specialty','')}",
            f"  city: {l.get('city','')}",
            f"  country: {l.get('country','')}",
        ]
        if l.get("website"):
            lines.append(f"  website: {l['website']}")
        if l.get("notes"):
            lines.append(f"  why_a_good_fit: {l['notes']}")
        posts = l.get("posts", [])
        if posts:
            lines.append("  recent_posts:")
            for j, p in enumerate(posts[:3], 1):
                lines.append(f"    post_{j}: \"{p[:500].replace(chr(10), ' ')}\"")
        lines.append("")
    return "\n".join(lines)


def generate_sales_emails(leads: List[Dict]) -> List[Dict]:
    return _call(SALES_SYSTEM, _format_sales(leads))


def generate_creator_emails(leads: List[Dict]) -> List[Dict]:
    return _call(CREATOR_SYSTEM, _format_creator(leads))
