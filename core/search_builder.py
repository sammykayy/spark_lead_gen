"""Generates LinkedIn and Google search strings for both pipelines."""
from typing import List
from urllib.parse import quote_plus


def sales_linkedin_url(roles: List[str], country: str, city: str) -> str:
    """Build a LinkedIn people search URL from roles + location."""
    location_parts = [p for p in [city, country] if p and p != "Other"]
    location = ", ".join(location_parts)
    role_query = " OR ".join(f'"{r}"' for r in roles)
    keyword = f'({role_query}) "{location}"' if location else role_query
    return f"https://www.linkedin.com/search/results/people/?keywords={quote_plus(keyword)}&origin=GLOBAL_SEARCH_HEADER"


def sales_google_queries(roles: List[str], country: str, city: str) -> List[str]:
    """Generate Google search strings to find LinkedIn profiles."""
    location_parts = [p for p in [city, country] if p and p != "Other"]
    location = " ".join(location_parts)
    role_str = " OR ".join(f'"{r}"' for r in roles[:4])
    queries = [
        f'site:linkedin.com/in ({role_str}) "{location}"',
        f'site:linkedin.com/in ({role_str}) international school "{location}"',
    ]
    return queries


def sales_google_url(query: str) -> str:
    return f"https://www.google.com/search?q={quote_plus(query)}"


def creator_search_prompt(category: str, domain: str, open_query: str) -> str:
    """
    Returns a prompt to paste into Claude Teams.
    Claude will respond with optimised LinkedIn/Google search queries
    for finding expert course creators on that topic.
    """
    return f"""I need to find expert educators and subject-matter experts who could become course \
creators on EduSpark (eduspark.world), a professional online learning platform for educators.

Please generate 8 to 10 varied, optimised search queries I can use on LinkedIn and Google to find \
the right people. Make the queries specific and creative — use different angles (job titles, \
credentials, communities, publications, events, hashtags).

Course category: {category}
Learning domain: {domain}
Specific focus: {open_query}

For each query provide:
1. A LinkedIn people search version (keywords to type into LinkedIn search)
2. A Google version (site:linkedin.com/in format)

Return as a numbered list. No explanation, just the queries."""
