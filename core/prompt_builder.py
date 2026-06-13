"""Builds ready-to-paste Claude Teams prompts for email generation."""
from typing import List, Dict


SALES_SYSTEM = """\
You write warm, personalised cold outreach emails for Sam at EduSpark (eduspark.world).

EduSpark is a professional online learning platform for educators. Award winner: EduTech Asia \
Best EdTech Deployment K-12 2025. Key courses: Kath Murdoch on inquiry, Tania Lattanzio and \
Dr. Jennifer Chang Wathall on UDL, safeguarding, leadership. Free/Pro/Spark+ tiers.

Rules — no exceptions:
- No em dashes. Use commas or full stops instead.
- No bullet points. Flowing prose only.
- UK spelling throughout.
- Subject line: 8-12 words, conversational, references their role or context specifically.
- Body: 4 short paragraphs.
  1. Acknowledge their role and context — what it means to be in that position, in that location.
  2. Introduce Sam and EduSpark in one sentence, naturally.
  3. One clear value relevant to their role.
  4. Warm, low-pressure invite. CTA: eduspark.world/book-a-demo
- Sign-off: Best wishes, / Sam / EduSpark | eduspark.world

Return ONLY a JSON array — no markdown fences, no extra text:
[{{"linkedin_url":"...","subject":"...","email":"..."}}]"""


CREATOR_SYSTEM = """\
You write warm, personalised creator-invitation emails for Sam at EduSpark (eduspark.world).

EduSpark is building a community of world-class educator-creators who build courses and reach \
a global audience of professional educators. Creators earn revenue, grow their brand, and \
contribute to a mission-driven community.

Rules — no exceptions:
- No em dashes. Use commas or full stops instead.
- No bullet points. Flowing prose only.
- UK spelling throughout.
- Subject line: 8-12 words, references their specific expertise or work.
- Body: 4 short paragraphs.
  1. Specific acknowledgement of their expertise and why it stands out.
  2. Introduce Sam and EduSpark as a creator platform in one sentence.
  3. Why their specialty is exactly what EduSpark's educator audience needs.
  4. Warm, low-pressure invite to a conversation. CTA: eduspark.world/become-a-creator
- Sign-off: Best wishes, / Sam / EduSpark | eduspark.world

Return ONLY a JSON array — no markdown fences, no extra text:
[{{"linkedin_url":"...","subject":"...","email":"..."}}]"""


def build_sales_prompt(leads: List[Dict]) -> str:
    lines = [SALES_SYSTEM, "", "LEADS:", ""]
    for i, l in enumerate(leads):
        lines += [
            f"Lead {i + 1}:",
            f"  linkedin_url: {l.get('linkedin_url', '')}",
            f"  name: {l.get('first_name', '')} {l.get('last_name', '')}".strip(),
            f"  role: {l.get('role', '')}",
            f"  city: {l.get('city', '')}",
            f"  country: {l.get('country', '')}",
            "",
        ]
    return "\n".join(lines)


def build_creator_prompt(leads: List[Dict]) -> str:
    lines = [CREATOR_SYSTEM, "", "LEADS:", ""]
    for i, l in enumerate(leads):
        lines += [
            f"Lead {i + 1}:",
            f"  linkedin_url: {l.get('linkedin_url', '')}",
            f"  name: {l.get('first_name', '')} {l.get('last_name', '')}".strip(),
            f"  specialty: {l.get('specialty', '')}",
            f"  city: {l.get('city', '')}",
            f"  country: {l.get('country', '')}",
        ]
        if l.get("website"):
            lines.append(f"  website: {l.get('website', '')}")
        if l.get("notes"):
            lines.append(f"  why_a_good_fit: {l.get('notes', '')}")
        posts = l.get("posts", [])
        if posts:
            lines.append("  recent_posts:")
            for j, p in enumerate(posts[:3], 1):
                lines.append(f"    post_{j}: \"{p[:500].replace(chr(10), ' ')}\"")
        lines.append("")
    return "\n".join(lines)
