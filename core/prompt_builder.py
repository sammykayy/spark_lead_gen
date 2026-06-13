"""Builds ready-to-paste Claude Teams prompts for email generation."""
from typing import List, Dict


SALES_PROMPT_TEMPLATE = """\
I need personalised cold outreach emails for EduSpark (eduspark.world) — a professional online \
learning platform for educators. Award winner: EduTech Asia Best EdTech Deployment K-12 2025. \
Key courses: Kath Murdoch on inquiry, Tania Lattanzio and Dr. Jennifer Chang Wathall on UDL, \
safeguarding, leadership. Free/Pro/Spark+ tiers.

Please write one email per lead below. Return ONLY a JSON array — no markdown, no explanation — \
in exactly this format:
[
  {{
    "linkedin_url": "...",
    "subject": "...",
    "email": "..."
  }}
]

Rules (no exceptions):
- No em dashes anywhere. Use commas or full stops instead.
- No bullet points in the body. Flowing prose only.
- Subject: 8-12 words, references something specific from their posts or role, conversational.
- Body: 4 paragraphs max.
  1. Specific observation from their posts or role (never a generic opener).
  2. One sentence: introduce Sam and EduSpark naturally.
  3. Relevant value connecting EduSpark to their context.
  4. Warm, low-pressure chat invite. CTA: eduspark.world/book-a-demo
- Sign-off: Best wishes, / Sam / EduSpark | eduspark.world

LEADS:
{leads}"""


CREATOR_PROMPT_TEMPLATE = """\
I need personalised creator-invitation emails for EduSpark (eduspark.world) — a professional \
online learning platform for educators. We are building a community of world-class educator-creators \
who build courses and reach a global audience. Creators earn revenue, grow their brand, and \
contribute to a mission-driven community.

Please write one email per lead below. Return ONLY a JSON array — no markdown, no explanation — \
in exactly this format:
[
  {{
    "linkedin_url": "...",
    "subject": "...",
    "email": "..."
  }}
]

Rules (no exceptions):
- No em dashes anywhere. Use commas or full stops instead.
- No bullet points in the body. Flowing prose only.
- Subject: 8-12 words, references something specific from their posts or expertise, conversational.
- Body: 4 paragraphs max.
  1. Specific observation from their posts, a talk, resource, or strong opinion they expressed.
  2. One sentence: introduce Sam and EduSpark as a creator platform.
  3. Why they would be a great fit: connect their domain and audience to the creator opportunity.
  4. Warm, low-pressure invite. CTA: eduspark.world/become-a-creator
- Sign-off: Best wishes, / Sam / EduSpark | eduspark.world

LEADS:
{leads}"""


def _format_lead_sales(l: Dict, i: int) -> str:
    lines = [
        f"Lead {i + 1}:",
        f"  linkedin_url: {l.get('linkedin_url', '')}",
        f"  name: {l.get('name', '')}",
        f"  title: {l.get('title', '')}",
        f"  country: {l.get('country', '')}",
    ]
    return "\n".join(lines)


def _format_lead_creator(l: Dict, i: int) -> str:
    lines = [
        f"Lead {i + 1}:",
        f"  linkedin_url: {l.get('linkedin_url', '')}",
        f"  name: {l.get('name', '')}",
        f"  title: {l.get('title', '')}",
        f"  domain: {l.get('domain', '')}",
        f"  specialty: {l.get('specialty', '')}",
        f"  why_a_good_fit: {l.get('notes', '')}",
    ]
    posts = l.get("posts", [])
    if posts:
        lines.append("  recent_posts:")
        for j, p in enumerate(posts[:3], 1):
            excerpt = p[:600].replace("\n", " ")
            lines.append(f"    post_{j}: \"{excerpt}\"")
    return "\n".join(lines)


def build_sales_prompt(leads: List[Dict]) -> str:
    leads_text = "\n\n".join(_format_lead_sales(l, i) for i, l in enumerate(leads))
    return SALES_PROMPT_TEMPLATE.format(leads=leads_text)


def build_creator_prompt(leads: List[Dict]) -> str:
    leads_text = "\n\n".join(_format_lead_creator(l, i) for i, l in enumerate(leads))
    return CREATOR_PROMPT_TEMPLATE.format(leads=leads_text)
