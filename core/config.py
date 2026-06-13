"""Reads secrets from Streamlit Cloud (st.secrets) with .env fallback for local dev."""
import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parents[1] / ".env")
except ImportError:
    pass

try:
    import streamlit as st
    def _secret(key: str) -> str:
        try:
            return st.secrets[key]
        except Exception:
            return os.getenv(key, "")
except ImportError:
    def _secret(key: str) -> str:
        return os.getenv(key, "")


def get_surfe_key() -> str:
    return _secret("SURFE_API_KEY")

def get_anthropic_key() -> str:
    return _secret("ANTHROPIC_API_KEY")

def get_google_sa_json() -> str:
    return _secret("GOOGLE_SERVICE_ACCOUNT_JSON")


SALES_SHEET_NAME   = "EduSpark Sales Leads MASTER"
CREATOR_SHEET_NAME = "EduSpark Creator Leads MASTER"

SALES_ROLES = [
    "Principal",
    "Vice Principal",
    "Head of School",
    "Deputy Head of School",
    "IB Coordinator",
    "PYP Coordinator",
    "MYP Coordinator",
    "DP Coordinator",
    "Teaching & Learning Coordinator",
    "Director of Learning",
    "Curriculum Coordinator",
    "Academic Coordinator",
    "Professional Development Lead",
    "Director of Studies",
    "Admissions Director",
    "Other",
]

COURSE_CATEGORIES = [
    "Pedagogy & Teaching Practice",
    "Curriculum & Assessment",
    "Leadership & School Management",
    "Wellbeing & Mental Health",
    "Inclusion & Special Needs (SEN/SEND)",
    "International Baccalaureate (IB)",
    "Early Childhood Education",
    "Technology & EdTech",
    "Social-Emotional Learning (SEL)",
    "Diversity, Equity & Inclusion",
    "Language & Literacy",
    "STEM / STEAM",
    "Arts Education",
    "Physical Education & Sport",
    "Safeguarding & Child Protection",
    "Teacher Professional Development",
    "Other",
]

LEARNING_DOMAINS = [
    "Mathematics",
    "Science",
    "English / Literacy",
    "Inquiry-Based Learning",
    "Universal Design for Learning (UDL)",
    "Project-Based Learning (PBL)",
    "Differentiated Instruction",
    "Assessment for Learning",
    "School Leadership",
    "Coaching & Mentoring",
    "Safeguarding",
    "Wellbeing",
    "EdTech Integration",
    "Early Years",
    "SEN / SEND",
    "EAL / Language Acquisition",
    "IB Framework",
    "Curriculum Design",
    "Other",
]

COUNTRIES = [
    "United Kingdom",
    "United States",
    "Australia",
    "Canada",
    "Singapore",
    "United Arab Emirates",
    "Hong Kong",
    "India",
    "New Zealand",
    "South Africa",
    "Malaysia",
    "Qatar",
    "Saudi Arabia",
    "Germany",
    "Netherlands",
    "Ireland",
    "Thailand",
    "Vietnam",
    "Indonesia",
    "Philippines",
    "Japan",
    "China",
    "South Korea",
    "Turkey",
    "Egypt",
    "Kenya",
    "Nigeria",
    "Other",
]
