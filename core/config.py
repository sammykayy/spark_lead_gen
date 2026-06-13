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

def get_google_sa_json() -> str:
    return _secret("GOOGLE_SERVICE_ACCOUNT_JSON")


SALES_SHEET_NAME = "EduSpark Sales Leads MASTER"
CREATOR_SHEET_NAME = "EduSpark Creator Leads MASTER"

LEARNING_DOMAINS = [
    "Mathematics",
    "Science",
    "Literacy / English Language Arts",
    "Inquiry-Based Learning",
    "Universal Design for Learning (UDL)",
    "Leadership & School Management",
    "Safeguarding & Child Protection",
    "Social-Emotional Learning (SEL)",
    "STEM / STEAM",
    "Early Childhood Education",
    "Special Educational Needs (SEN / SEND)",
    "Technology & EdTech",
    "International Baccalaureate (IB)",
    "Curriculum Design",
    "Assessment & Feedback",
    "Teacher Professional Development",
    "Wellbeing & Mental Health",
    "Diversity, Equity & Inclusion",
    "Language Acquisition / EAL",
    "Physical Education & Sport",
    "Arts Education",
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
    "Other",
]

SALES_PERSONAS = [
    "Principal / Head of School",
    "Vice Principal / Deputy Head",
    "IB Coordinator",
    "PYP Coordinator",
    "MYP Coordinator",
    "DP Coordinator",
    "Teaching & Learning Coordinator",
    "Director of Learning",
    "Curriculum Coordinator",
    "Academic Coordinator",
    "Professional Development Lead",
    "Other",
]
