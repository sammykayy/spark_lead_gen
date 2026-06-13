"""Google Sheets as primary store + CSV export. Deduplicates by linkedin_url."""
import json
import csv
import io
from typing import List, Dict

import gspread
from google.oauth2.service_account import Credentials

from .config import get_google_sa_json, SALES_SHEET_NAME, CREATOR_SHEET_NAME

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

SALES_COLS = [
    "First Name", "Last Name", "Role", "Email", "LinkedIn",
    "City", "Country", "Subject", "Email Body",
    "Approved", "Email Sent", "Date Sent",
]

CREATOR_COLS = [
    "First Name", "Last Name", "Specialty", "Email", "LinkedIn",
    "Website", "City", "Country", "Subject", "Email Body",
    "Approved", "Email Sent", "Date Sent",
]


def _gc() -> gspread.Client:
    sa = json.loads(get_google_sa_json())
    creds = Credentials.from_service_account_info(sa, scopes=SCOPES)
    return gspread.authorize(creds)


def _sheet(name: str, cols: List[str]) -> gspread.Worksheet:
    gc = _gc()
    try:
        sh = gc.open(name)
    except gspread.SpreadsheetNotFound:
        sh = gc.create(name)
        sh.sheet1.append_row(cols)
    return sh.sheet1


def _existing_urls(ws: gspread.Worksheet) -> set:
    records = ws.get_all_records()
    return {r.get("LinkedIn", "") for r in records}


# ── Sales ─────────────────────────────────────────────────────────────────────

def load_sales() -> List[Dict]:
    try:
        ws = _sheet(SALES_SHEET_NAME, SALES_COLS)
        return ws.get_all_records()
    except Exception:
        return []


def save_sales(leads: List[Dict]) -> int:
    ws = _sheet(SALES_SHEET_NAME, SALES_COLS)
    existing = _existing_urls(ws)
    count = 0
    for l in leads:
        if l.get("linkedin_url", "") in existing:
            continue
        ws.append_row([
            l.get("first_name", ""), l.get("last_name", ""),
            l.get("role", ""), l.get("email", ""),
            l.get("linkedin_url", ""), l.get("city", ""), l.get("country", ""),
            l.get("subject", ""), l.get("email_body", ""),
            "", "", "",
        ])
        count += 1
    return count


def sales_to_csv(leads: List[Dict]) -> str:
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=SALES_COLS, extrasaction="ignore")
    w.writeheader()
    for l in leads:
        w.writerow({
            "First Name": l.get("first_name", ""),
            "Last Name": l.get("last_name", ""),
            "Role": l.get("role", ""),
            "Email": l.get("email", ""),
            "LinkedIn": l.get("linkedin_url", ""),
            "City": l.get("city", ""),
            "Country": l.get("country", ""),
            "Subject": l.get("subject", ""),
            "Email Body": l.get("email_body", ""),
            "Approved": l.get("approved", ""),
            "Email Sent": l.get("email_sent", ""),
            "Date Sent": l.get("date_sent", ""),
        })
    return buf.getvalue()


# ── Creator ───────────────────────────────────────────────────────────────────

def load_creator() -> List[Dict]:
    try:
        ws = _sheet(CREATOR_SHEET_NAME, CREATOR_COLS)
        return ws.get_all_records()
    except Exception:
        return []


def save_creator(leads: List[Dict]) -> int:
    ws = _sheet(CREATOR_SHEET_NAME, CREATOR_COLS)
    existing = _existing_urls(ws)
    count = 0
    for l in leads:
        if l.get("linkedin_url", "") in existing:
            continue
        ws.append_row([
            l.get("first_name", ""), l.get("last_name", ""),
            l.get("specialty", ""), l.get("email", ""),
            l.get("linkedin_url", ""), l.get("website", ""),
            l.get("city", ""), l.get("country", ""),
            l.get("subject", ""), l.get("email_body", ""),
            "", "", "",
        ])
        count += 1
    return count


def creator_to_csv(leads: List[Dict]) -> str:
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=CREATOR_COLS, extrasaction="ignore")
    w.writeheader()
    for l in leads:
        w.writerow({
            "First Name": l.get("first_name", ""),
            "Last Name": l.get("last_name", ""),
            "Specialty": l.get("specialty", ""),
            "Email": l.get("email", ""),
            "LinkedIn": l.get("linkedin_url", ""),
            "Website": l.get("website", ""),
            "City": l.get("city", ""),
            "Country": l.get("country", ""),
            "Subject": l.get("subject", ""),
            "Email Body": l.get("email_body", ""),
            "Approved": l.get("approved", ""),
            "Email Sent": l.get("email_sent", ""),
            "Date Sent": l.get("date_sent", ""),
        })
    return buf.getvalue()
