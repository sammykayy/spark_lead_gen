"""Google Sheets as primary store + CSV download. Deduplicates by linkedin_url."""
import json
import csv
import io
from typing import List, Dict, Optional

import gspread
from google.oauth2.service_account import Credentials

from .config import get_google_sa_json, SALES_SHEET_NAME, CREATOR_SHEET_NAME

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

SALES_COLS = [
    "Name", "Title", "School", "LinkedIn URL", "Email",
    "Subject", "Email Body", "Approved", "Email Sent", "Date Sent",
]

CREATOR_COLS = [
    "Name", "Title", "Domain", "Country", "LinkedIn URL",
    "Subject", "Email Body", "Approved", "Email Sent", "Date Sent",
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
    return {r.get("LinkedIn URL", "") for r in records}


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
            l.get("name", ""), l.get("title", ""), l.get("school", ""),
            l.get("linkedin_url", ""), l.get("email", ""),
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
            "Name": l.get("name", ""),
            "Title": l.get("title", ""),
            "School": l.get("school", ""),
            "LinkedIn URL": l.get("linkedin_url", ""),
            "Email": l.get("email", ""),
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
            l.get("name", ""), l.get("title", ""),
            l.get("domain", ""), l.get("country", ""),
            l.get("linkedin_url", ""),
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
            "Name": l.get("name", ""),
            "Title": l.get("title", ""),
            "Domain": l.get("domain", ""),
            "Country": l.get("country", ""),
            "LinkedIn URL": l.get("linkedin_url", ""),
            "Subject": l.get("subject", ""),
            "Email Body": l.get("email_body", ""),
            "Approved": l.get("approved", ""),
            "Email Sent": l.get("email_sent", ""),
            "Date Sent": l.get("date_sent", ""),
        })
    return buf.getvalue()
