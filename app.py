"""EduSpark Lead Generation App — Sales & Creator pipelines."""
import csv as _csv
import io as _io
import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).parent))

from core.config import (
    SALES_ROLES, COURSE_CATEGORIES, LEARNING_DOMAINS, COUNTRIES,
    get_surfe_key, get_google_sa_json,
)
from core.search_builder import (
    sales_linkedin_url, sales_google_queries, sales_google_url,
    creator_search_prompt,
)
from core.prompt_builder import build_sales_prompt, build_creator_prompt
from core.email_parser import parse_claude_response, merge_emails_into_leads

# ── Page config ───────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="EduSpark Lead Gen",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
  section[data-testid="stSidebar"] { background:#0d1117; }
  .badge {
    display:inline-block; padding:3px 14px; border-radius:20px;
    font-size:11px; font-weight:700; letter-spacing:.8px; margin-bottom:8px;
  }
  .badge-sales   { background:#1a237e; color:#90caf9; }
  .badge-creator { background:#1b5e20; color:#a5d6a7; }
  .step-header { font-size:15px; font-weight:700; margin:18px 0 6px 0; }
  .search-box {
    background:#161b22; border:1px solid #30363d; border-radius:8px;
    padding:10px 14px; font-family:monospace; font-size:12px;
    word-break:break-all; margin-bottom:6px;
  }
  .lead-card {
    background:#161b22; border-radius:8px; padding:14px 18px;
    margin-bottom:10px; border-left:4px solid #5c6bc0;
  }
  .lead-card.creator { border-left-color:#66bb6a; }
  .lead-name  { font-size:15px; font-weight:700; margin-bottom:3px; }
  .lead-meta  { font-size:12px; color:#8b949e; margin-bottom:6px; }
  .lead-email { font-size:12px; color:#58a6ff; margin-bottom:6px; }
  .subj       { font-size:13px; font-weight:600; margin-bottom:4px; }
  .body-text  { font-size:12px; color:#cdd9e5; white-space:pre-wrap; }
  .tag {
    display:inline-block; background:#21262d; border-radius:4px;
    padding:2px 8px; font-size:11px; margin:2px; color:#8b949e;
  }
</style>
""", unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────────────────────────

for k, v in {
    "sales_leads": [],
    "creator_leads": [],
    "mode": "Sales",
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("## ⚡ EduSpark")
    st.markdown("**Lead Generation Hub**")
    st.markdown("---")
    mode = st.radio("Pipeline", ["Sales", "Creator Outreach"])
    st.session_state.mode = mode
    st.markdown("---")

    has_surfe  = bool(get_surfe_key())
    has_sheets = bool(get_google_sa_json())

    st.markdown("**Integrations**")
    st.markdown(f"{'✅' if has_surfe  else '❌'} Surfe {'connected' if has_surfe else '— add key'}")
    st.markdown(f"{'✅' if has_sheets else '⚠️'} Google Sheets {'connected' if has_sheets else '— optional'}")
    st.markdown("---")

    if mode == "Sales":
        n  = len(st.session_state.sales_leads)
        ne = sum(1 for l in st.session_state.sales_leads if l.get("email"))
        nw = sum(1 for l in st.session_state.sales_leads if l.get("email_body"))
        st.markdown(f"**Session**  \n{n} leads · {ne} emails found · {nw} written")
    else:
        n  = len(st.session_state.creator_leads)
        ne = sum(1 for l in st.session_state.creator_leads if l.get("email"))
        nw = sum(1 for l in st.session_state.creator_leads if l.get("email_body"))
        st.markdown(f"**Session**  \n{n} creators · {ne} emails found · {nw} written")

    st.markdown("---")
    st.caption("eduspark.world")


# ═══════════════════════════════════════════════════════════════════════════════
# SALES
# ═══════════════════════════════════════════════════════════════════════════════

if mode == "Sales":
    st.markdown('<span class="badge badge-sales">SALES</span>', unsafe_allow_html=True)
    st.title("School Leader Lead Generation")
    st.caption("Build your search, find profiles on LinkedIn, enrich emails via Surfe, generate personalised outreach.")

    t1, t2, t3, t4 = st.tabs(["🔍 Build Search", "➕ Add Profiles", "📧 Enrich Emails", "✍️ Emails & Export"])

    # ── Tab 1: Build search ───────────────────────────────────────────────────
    with t1:
        st.markdown("### Build your LinkedIn search")
        st.caption("Select the roles and location you're targeting. The tool generates ready-to-use search links.")

        roles = st.multiselect("Roles *", SALES_ROLES, placeholder="Select one or more roles…")
        col_a, col_b = st.columns(2)
        with col_a:
            country = st.selectbox("Country", [""] + COUNTRIES)
        with col_b:
            city = st.text_input("City (optional)", placeholder="e.g. Dubai, Singapore, London…")

        if roles:
            final_country = "" if country == "Other" else country
            st.markdown("---")
            st.markdown('<div class="step-header">LinkedIn search — click to open</div>', unsafe_allow_html=True)
            li_url = sales_linkedin_url(roles, final_country, city)
            st.link_button("Open LinkedIn People Search ↗", li_url, type="primary")
            st.caption("Tip: once on LinkedIn, use the Connections and Location filters to narrow further.")

            st.markdown('<div class="step-header">Google searches — find LinkedIn profiles</div>', unsafe_allow_html=True)
            for q in sales_google_queries(roles, final_country, city):
                st.markdown(f'<div class="search-box">{q}</div>', unsafe_allow_html=True)
                st.link_button(f"Search Google ↗", sales_google_url(q), key=q)

            st.markdown("---")
            st.info("Found some profiles? Head to the **Add Profiles** tab to add them.")

    # ── Tab 2: Add profiles ───────────────────────────────────────────────────
    with t2:
        st.markdown("### Add profiles from LinkedIn")

        col_form, col_list = st.columns([1, 1])

        with col_form:
            with st.form("sales_add", clear_on_submit=True):
                c1, c2 = st.columns(2)
                with c1:
                    first_name = st.text_input("First name *")
                with c2:
                    last_name = st.text_input("Last name *")
                role = st.selectbox("Role *", SALES_ROLES)
                custom_role = st.text_input("Custom role (if Other above)", "")
                c3, c4 = st.columns(2)
                with c3:
                    p_country = st.selectbox("Country *", [""] + COUNTRIES, key="s_country")
                with c4:
                    p_city = st.text_input("City", placeholder="e.g. Dubai")
                linkedin_url = st.text_input("LinkedIn URL *", placeholder="https://www.linkedin.com/in/…")
                submitted = st.form_submit_button("Add Lead", type="primary")

            if submitted:
                if not first_name or not last_name or not linkedin_url:
                    st.error("First name, last name, and LinkedIn URL are required.")
                else:
                    final_role    = custom_role.strip() if role == "Other" else role
                    final_country = "" if p_country == "Other" else p_country
                    existing = {l["linkedin_url"] for l in st.session_state.sales_leads}
                    if linkedin_url.strip() in existing:
                        st.warning("Already in your list.")
                    else:
                        st.session_state.sales_leads.append({
                            "first_name":   first_name.strip(),
                            "last_name":    last_name.strip(),
                            "role":         final_role,
                            "city":         p_city.strip(),
                            "country":      final_country,
                            "linkedin_url": linkedin_url.strip(),
                            "email":        "",
                            "subject":      "",
                            "email_body":   "",
                        })
                        st.success(f"Added {first_name} {last_name}.")

        with col_list:
            leads = st.session_state.sales_leads
            st.markdown(f"**{len(leads)} profiles**")
            for i, l in enumerate(leads):
                c = st.columns([5, 1])
                with c[0]:
                    em = f" · {l['email']}" if l.get("email") else " · no email yet"
                    wr = " ✅" if l.get("email_body") else ""
                    st.markdown(f"**{l['first_name']} {l['last_name']}** — {l.get('role','')} · {l.get('city','')} {l.get('country','')}{em}{wr}")
                with c[1]:
                    if st.button("✕", key=f"ds{i}"):
                        st.session_state.sales_leads.pop(i)
                        st.rerun()

        st.markdown("---")
        st.markdown("**Or import from CSV** (columns: first_name, last_name, role, city, country, linkedin_url)")
        up = st.file_uploader("", type="csv", key="s_csv")
        if up:
            reader = _csv.DictReader(_io.StringIO(up.read().decode()))
            existing = {l["linkedin_url"] for l in st.session_state.sales_leads}
            added = 0
            for row in reader:
                url = row.get("linkedin_url","").strip()
                if url and url not in existing:
                    st.session_state.sales_leads.append({
                        "first_name":   row.get("first_name",""),
                        "last_name":    row.get("last_name",""),
                        "role":         row.get("role",""),
                        "city":         row.get("city",""),
                        "country":      row.get("country",""),
                        "linkedin_url": url,
                        "email": "", "subject": "", "email_body": "",
                    })
                    added += 1
            st.success(f"Imported {added} leads.")

    # ── Tab 3: Enrich emails ──────────────────────────────────────────────────
    with t3:
        st.markdown("### Enrich emails via Surfe")
        needs = [l for l in st.session_state.sales_leads if not l.get("email")]

        if not has_surfe:
            st.error("Surfe API key not configured. Add `SURFE_API_KEY` to your app secrets.")
        elif not st.session_state.sales_leads:
            st.info("Add profiles in the 'Add Profiles' tab first.")
        elif not needs:
            st.success("All leads already have emails.")
        else:
            st.info(f"**{len(needs)} leads** need enrichment — uses **{len(needs)}** of your 1,000 monthly Surfe credits.")
            if st.button("Enrich Emails", type="primary"):
                from core.surfe import enrich
                with st.spinner("Contacting Surfe…"):
                    try:
                        results = enrich(needs)
                        found = 0
                        for lead in st.session_state.sales_leads:
                            email = results.get(lead["linkedin_url"])
                            if email:
                                lead["email"] = email
                                found += 1
                        missed = len(needs) - found
                        st.success(f"Found **{found}** emails. {missed} had no match — keep them for LinkedIn-only outreach or remove.")
                    except Exception as e:
                        st.error(f"Surfe error: {e}")

        if st.session_state.sales_leads:
            st.markdown("---")
            for l in st.session_state.sales_leads:
                icon = "✅" if l.get("email") else "❌"
                st.markdown(f"{icon} **{l['first_name']} {l['last_name']}** — {l.get('email','no email found')}")

    # ── Tab 4: Emails & export ────────────────────────────────────────────────
    with t4:
        ready = [l for l in st.session_state.sales_leads if l.get("email")]

        st.markdown("### Generate outreach emails")

        if not ready:
            st.info("Enrich emails in the 'Enrich Emails' tab first.")
        else:
            st.markdown(f"**{len(ready)} leads with confirmed emails.**")
            st.markdown('<div class="step-header">Step 1 — Copy this prompt and paste it into Claude Teams</div>', unsafe_allow_html=True)
            prompt = build_sales_prompt(ready)
            st.code(prompt, language=None)

            st.markdown('<div class="step-header">Step 2 — Paste Claude\'s response here</div>', unsafe_allow_html=True)
            resp = st.text_area("", height=180, placeholder='[{"linkedin_url":"...","subject":"...","email":"..."}]', key="s_resp")
            if st.button("Apply Emails", type="primary", key="s_apply"):
                emails, err = parse_claude_response(resp)
                if err:
                    st.error(err)
                else:
                    st.session_state.sales_leads = merge_emails_into_leads(st.session_state.sales_leads, emails)
                    st.success(f"Applied {len(emails)} emails.")

        st.markdown("---")
        st.markdown("### Review & export")

        if not st.session_state.sales_leads:
            st.info("No leads yet.")
        else:
            for lead in st.session_state.sales_leads:
                st.markdown(f"""
<div class="lead-card">
  <div class="lead-name">{lead['first_name']} {lead['last_name']}</div>
  <div class="lead-meta"><span class="tag">{lead.get('role','')}</span><span class="tag">{lead.get('city','')}</span><span class="tag">{lead.get('country','')}</span></div>
  <div class="lead-email">{'✅ ' + lead['email'] if lead.get('email') else '❌ No email'} &nbsp;·&nbsp; <a href="{lead.get('linkedin_url','')}" target="_blank">LinkedIn ↗</a></div>
  {'<div class="subj">📧 ' + lead.get('subject','') + '</div>' if lead.get('subject') else ''}
  {'<div class="body-text">' + lead.get('email_body','')[:500] + ('…' if len(lead.get('email_body',''))>500 else '') + '</div>' if lead.get('email_body') else ''}
</div>""", unsafe_allow_html=True)

            col1, col2, col3 = st.columns(3)
            with col1:
                from core.store import sales_to_csv
                st.download_button("⬇ Download CSV", sales_to_csv(st.session_state.sales_leads).encode(),
                                   "eduspark_sales_leads.csv", "text/csv")
            with col2:
                if has_sheets:
                    if st.button("Save to Google Sheets"):
                        from core.store import save_sales
                        try:
                            n = save_sales(st.session_state.sales_leads)
                            st.success(f"Saved {n} rows.")
                        except Exception as e:
                            st.error(str(e))
            with col3:
                if st.button("Clear session", key="cs"):
                    st.session_state.sales_leads = []
                    st.rerun()


# ═══════════════════════════════════════════════════════════════════════════════
# CREATOR OUTREACH
# ═══════════════════════════════════════════════════════════════════════════════

else:
    st.markdown('<span class="badge badge-creator">CREATOR OUTREACH</span>', unsafe_allow_html=True)
    st.title("Creator Lead Generation")
    st.caption("Find expert educators for your course topic, enrich their emails via Surfe, generate personalised creator invitations.")

    t1, t2, t3, t4 = st.tabs(["🔍 Generate Searches", "➕ Add Profiles", "📧 Enrich Emails", "✍️ Emails & Export"])

    # ── Tab 1: Generate searches ──────────────────────────────────────────────
    with t1:
        st.markdown("### Generate search queries for your topic")
        st.caption("Describe the expert you're looking for. The tool generates a prompt — paste it into Claude Teams to get tailored LinkedIn and Google search queries.")

        with st.form("creator_search"):
            cat = st.selectbox("Course Category *", COURSE_CATEGORIES)
            domain = st.selectbox("Learning Domain *", LEARNING_DOMAINS)
            open_query = st.text_area(
                "Describe the expert you're looking for *",
                height=90,
                placeholder='e.g. "expert in third culture kids and identity in international schools"\n"IB mathematics specialist who also writes about inquiry"\n"trauma-informed teaching practitioner with school experience"',
            )
            gen_btn = st.form_submit_button("Generate Search Prompt", type="primary")

        if gen_btn:
            if not open_query.strip():
                st.error("Please describe the expert you're looking for.")
            else:
                final_cat = cat if cat != "Other" else ""
                prompt = creator_search_prompt(final_cat, domain, open_query)
                st.markdown("---")
                st.markdown("#### Copy this prompt → paste into Claude Teams → use the search queries it gives you")
                st.code(prompt, language=None)
                st.info("Claude Teams will return 8–10 varied LinkedIn and Google search queries. Use them to find profiles, then add them in the 'Add Profiles' tab.")

    # ── Tab 2: Add profiles ───────────────────────────────────────────────────
    with t2:
        st.markdown("### Add creator profiles")

        col_form, col_list = st.columns([1, 1])

        with col_form:
            with st.form("creator_add", clear_on_submit=True):
                c1, c2 = st.columns(2)
                with c1:
                    first_name = st.text_input("First name *")
                with c2:
                    last_name = st.text_input("Last name *")
                specialty = st.text_input(
                    "Specialty *",
                    placeholder="e.g. IB Mathematics, Trauma-Informed Teaching, Third Culture Kids…",
                )
                linkedin_url = st.text_input("LinkedIn URL *", placeholder="https://www.linkedin.com/in/…")
                website = st.text_input("Website (if any)", placeholder="https://…")
                c3, c4 = st.columns(2)
                with c3:
                    p_country = st.selectbox("Country *", [""] + COUNTRIES, key="c_country")
                with c4:
                    p_city = st.text_input("City", placeholder="e.g. London")
                notes = st.text_area(
                    "Why are they a good fit?",
                    height=70,
                    placeholder="e.g. Published author, runs CPD workshops, 10k LinkedIn followers, speaks at IB conferences…",
                )
                st.markdown("**Recent posts** (paste up to 3 — used to personalise the email)")
                post1 = st.text_area("Post 1 *", height=80, placeholder="Paste their most relevant post…")
                post2 = st.text_area("Post 2", height=70)
                post3 = st.text_area("Post 3", height=70)
                submitted = st.form_submit_button("Add Creator", type="primary")

            if submitted:
                if not first_name or not last_name or not linkedin_url or not post1:
                    st.error("First name, last name, LinkedIn URL, and at least one post are required.")
                else:
                    final_country = "" if p_country == "Other" else p_country
                    posts = [p.strip() for p in [post1, post2, post3] if p.strip()]
                    existing = {l["linkedin_url"] for l in st.session_state.creator_leads}
                    if linkedin_url.strip() in existing:
                        st.warning("Already in your list.")
                    else:
                        st.session_state.creator_leads.append({
                            "first_name":   first_name.strip(),
                            "last_name":    last_name.strip(),
                            "specialty":    specialty.strip(),
                            "linkedin_url": linkedin_url.strip(),
                            "website":      website.strip(),
                            "city":         p_city.strip(),
                            "country":      final_country,
                            "notes":        notes.strip(),
                            "posts":        posts,
                            "email":        "",
                            "subject":      "",
                            "email_body":   "",
                        })
                        st.success(f"Added {first_name} {last_name}.")

        with col_list:
            creators = st.session_state.creator_leads
            st.markdown(f"**{len(creators)} profiles**")
            for i, l in enumerate(creators):
                c = st.columns([5, 1])
                with c[0]:
                    em = f" · {l['email']}" if l.get("email") else " · no email yet"
                    wr = " ✅" if l.get("email_body") else ""
                    st.markdown(f"**{l['first_name']} {l['last_name']}** — {l.get('specialty','')} · {l.get('city','')} {l.get('country','')}{em}{wr}")
                with c[1]:
                    if st.button("✕", key=f"dc{i}"):
                        st.session_state.creator_leads.pop(i)
                        st.rerun()

        st.markdown("---")
        st.markdown("**Or import from CSV** (columns: first_name, last_name, specialty, linkedin_url, website, city, country, notes, post1, post2, post3)")
        up = st.file_uploader("", type="csv", key="c_csv")
        if up:
            reader = _csv.DictReader(_io.StringIO(up.read().decode()))
            existing = {l["linkedin_url"] for l in st.session_state.creator_leads}
            added = 0
            for row in reader:
                url = row.get("linkedin_url","").strip()
                if url and url not in existing:
                    posts = [row.get(f"post{j}","").strip() for j in range(1,4) if row.get(f"post{j}","").strip()]
                    st.session_state.creator_leads.append({
                        "first_name":   row.get("first_name",""),
                        "last_name":    row.get("last_name",""),
                        "specialty":    row.get("specialty",""),
                        "linkedin_url": url,
                        "website":      row.get("website",""),
                        "city":         row.get("city",""),
                        "country":      row.get("country",""),
                        "notes":        row.get("notes",""),
                        "posts":        posts,
                        "email": "", "subject": "", "email_body": "",
                    })
                    added += 1
            st.success(f"Imported {added} creators.")

    # ── Tab 3: Enrich emails ──────────────────────────────────────────────────
    with t3:
        st.markdown("### Enrich emails via Surfe")
        needs = [l for l in st.session_state.creator_leads if not l.get("email")]

        if not has_surfe:
            st.error("Surfe API key not configured. Add `SURFE_API_KEY` to your app secrets.")
        elif not st.session_state.creator_leads:
            st.info("Add profiles in the 'Add Profiles' tab first.")
        elif not needs:
            st.success("All creators already have emails.")
        else:
            st.info(f"**{len(needs)} creators** need enrichment — uses **{len(needs)}** of your 1,000 monthly Surfe credits.")
            if st.button("Enrich Emails", type="primary", key="c_enrich"):
                from core.surfe import enrich
                with st.spinner("Contacting Surfe…"):
                    try:
                        results = enrich(needs)
                        found = 0
                        for lead in st.session_state.creator_leads:
                            email = results.get(lead["linkedin_url"])
                            if email:
                                lead["email"] = email
                                found += 1
                        missed = len(needs) - found
                        st.success(f"Found **{found}** emails. {missed} had no match.")
                    except Exception as e:
                        st.error(f"Surfe error: {e}")

        if st.session_state.creator_leads:
            st.markdown("---")
            for l in st.session_state.creator_leads:
                icon = "✅" if l.get("email") else "❌"
                st.markdown(f"{icon} **{l['first_name']} {l['last_name']}** — {l.get('email','no email found')}")

    # ── Tab 4: Emails & export ────────────────────────────────────────────────
    with t4:
        ready = [l for l in st.session_state.creator_leads if l.get("posts")]

        st.markdown("### Generate creator invitation emails")

        if not ready:
            st.info("Add creators with at least one post in the 'Add Profiles' tab.")
        else:
            st.markdown(f"**{len(ready)} creators ready.**")
            st.markdown('<div class="step-header">Step 1 — Copy this prompt and paste it into Claude Teams</div>', unsafe_allow_html=True)
            prompt = build_creator_prompt(ready)
            st.code(prompt, language=None)

            st.markdown('<div class="step-header">Step 2 — Paste Claude\'s response here</div>', unsafe_allow_html=True)
            resp = st.text_area("", height=180, placeholder='[{"linkedin_url":"...","subject":"...","email":"..."}]', key="c_resp")
            if st.button("Apply Emails", type="primary", key="c_apply"):
                emails, err = parse_claude_response(resp)
                if err:
                    st.error(err)
                else:
                    st.session_state.creator_leads = merge_emails_into_leads(st.session_state.creator_leads, emails)
                    st.success(f"Applied {len(emails)} emails.")

        st.markdown("---")
        st.markdown("### Review & export")

        if not st.session_state.creator_leads:
            st.info("No creators yet.")
        else:
            for lead in st.session_state.creator_leads:
                st.markdown(f"""
<div class="lead-card creator">
  <div class="lead-name">{lead['first_name']} {lead['last_name']}</div>
  <div class="lead-meta">
    <span class="tag">{lead.get('specialty','')}</span>
    <span class="tag">{lead.get('city','')}</span>
    <span class="tag">{lead.get('country','')}</span>
    {('<span class="tag"><a href="' + lead.get('website','') + '" target="_blank">website ↗</a></span>') if lead.get('website') else ''}
  </div>
  <div class="lead-email">{'✅ ' + lead['email'] if lead.get('email') else '❌ No email'} &nbsp;·&nbsp; <a href="{lead.get('linkedin_url','')}" target="_blank">LinkedIn ↗</a></div>
  {'<div class="subj">📧 ' + lead.get('subject','') + '</div>' if lead.get('subject') else ''}
  {'<div class="body-text">' + lead.get('email_body','')[:500] + ('…' if len(lead.get('email_body',''))>500 else '') + '</div>' if lead.get('email_body') else ''}
</div>""", unsafe_allow_html=True)

            col1, col2, col3 = st.columns(3)
            with col1:
                from core.store import creator_to_csv
                st.download_button("⬇ Download CSV", creator_to_csv(st.session_state.creator_leads).encode(),
                                   "eduspark_creator_leads.csv", "text/csv")
            with col2:
                if has_sheets:
                    if st.button("Save to Google Sheets", key="cgs"):
                        from core.store import save_creator
                        try:
                            n = save_creator(st.session_state.creator_leads)
                            st.success(f"Saved {n} rows.")
                        except Exception as e:
                            st.error(str(e))
            with col3:
                if st.button("Clear session", key="cc"):
                    st.session_state.creator_leads = []
                    st.rerun()
