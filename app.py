"""EduSpark Lead Generation App — Sales & Creator pipelines. Zero API cost."""
import json
import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).parent))

from core.config import LEARNING_DOMAINS, COUNTRIES, SALES_PERSONAS, get_surfe_key, get_google_sa_json
from core.prompt_builder import build_sales_prompt, build_creator_prompt
from core.email_parser import parse_claude_response, merge_emails_into_leads

# ── Page setup ────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="EduSpark Lead Gen",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
  section[data-testid="stSidebar"] { background: #0d1117; }
  .badge {
    display:inline-block; padding:3px 12px; border-radius:20px;
    font-size:12px; font-weight:700; letter-spacing:.6px; margin-bottom:8px;
  }
  .badge-sales    { background:#1a237e; color:#90caf9; }
  .badge-creator  { background:#1b5e20; color:#a5d6a7; }
  .step-box {
    background:#1c1f2e; border-radius:10px; padding:18px 22px; margin-bottom:16px;
  }
  .lead-card {
    background:#1c1f2e; border-radius:8px; padding:14px 18px;
    margin-bottom:12px; border-left:4px solid #5c6bc0;
  }
  .lead-card.creator { border-left-color:#66bb6a; }
  .lead-name  { font-size:16px; font-weight:700; margin-bottom:2px; }
  .lead-meta  { font-size:12px; color:#9e9e9e; margin-bottom:8px; }
  .subj       { font-weight:600; font-size:13px; margin-bottom:4px; }
  .body-text  { font-size:12px; color:#cfd8dc; white-space:pre-wrap; }
  .prompt-box {
    background:#0d1117; border:1px solid #30363d; border-radius:8px;
    padding:16px; font-size:12px; font-family:monospace;
    white-space:pre-wrap; max-height:400px; overflow-y:auto;
  }
  .info-pill {
    display:inline-block; background:#263238; border-radius:6px;
    padding:4px 10px; font-size:12px; margin:2px;
  }
</style>
""", unsafe_allow_html=True)

# ── Session state defaults ────────────────────────────────────────────────────

for key, default in {
    "sales_leads": [],
    "creator_leads": [],
    "mode": "Sales — School Leaders",
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("## ⚡ EduSpark")
    st.markdown("**Lead Generation Hub**")
    st.markdown("---")

    mode = st.radio("Pipeline", ["Sales — School Leaders", "Creator Outreach"])
    st.session_state.mode = mode
    st.markdown("---")

    has_surfe = bool(get_surfe_key())
    has_sheets = bool(get_google_sa_json())

    st.markdown("**API Status**")
    st.markdown(f"{'✅' if has_surfe else '❌'} Surfe {'connected' if has_surfe else '— add key in secrets'}")
    st.markdown(f"{'✅' if has_sheets else '⚠️'} Google Sheets {'connected' if has_sheets else '— optional'}")
    st.markdown("---")

    if mode == "Sales — School Leaders":
        count = len(st.session_state.sales_leads)
        enriched = sum(1 for l in st.session_state.sales_leads if l.get("email"))
        emailed = sum(1 for l in st.session_state.sales_leads if l.get("email_body"))
        st.markdown(f"**This session**")
        st.markdown(f"- {count} leads added")
        st.markdown(f"- {enriched} emails found")
        st.markdown(f"- {emailed} emails written")
    else:
        count = len(st.session_state.creator_leads)
        emailed = sum(1 for l in st.session_state.creator_leads if l.get("email_body"))
        st.markdown(f"**This session**")
        st.markdown(f"- {count} creators added")
        st.markdown(f"- {emailed} emails written")

    st.markdown("---")
    st.caption("eduspark.world")


# ═══════════════════════════════════════════════════════════════════════════════
# SALES MODE
# ═══════════════════════════════════════════════════════════════════════════════

if mode == "Sales — School Leaders":
    st.markdown('<span class="badge badge-sales">SALES</span>', unsafe_allow_html=True)
    st.title("School Leader Lead Generation")
    st.caption("Add school leader profiles, enrich emails via Surfe, generate personalised outreach with Claude Teams.")

    tab1, tab2, tab3, tab4 = st.tabs(["➕ Add Leads", "📧 Enrich Emails", "✍️ Generate Emails", "📋 All Leads"])

    # ── Tab 1: Add leads ──────────────────────────────────────────────────────
    with tab1:
        st.markdown("### Add school leader profiles")
        st.caption("Find profiles on LinkedIn, then fill in the details below. Add one at a time or import a CSV.")

        col_form, col_list = st.columns([1, 1])

        with col_form:
            with st.form("add_sales_lead", clear_on_submit=True):
                st.markdown("**Profile details**")
                name = st.text_input("Full name *", placeholder="Jane Smith")
                col_a, col_b = st.columns(2)
                with col_a:
                    first = st.text_input("First name *", placeholder="Jane")
                with col_b:
                    last = st.text_input("Last name *", placeholder="Smith")
                title = st.selectbox("Role / Title *", SALES_PERSONAS)
                custom_title = st.text_input("Custom title (if Other)", "")
                school = st.text_input("School name *", placeholder="International School of...")
                linkedin_url = st.text_input("LinkedIn URL *", placeholder="https://www.linkedin.com/in/...")

                st.markdown("**Recent posts** (paste up to 2 — helps personalise the email)")
                post1 = st.text_area("Post 1", height=80, placeholder="Paste post text here…")
                post2 = st.text_area("Post 2", height=80, placeholder="Paste post text here…")

                add_btn = st.form_submit_button("Add Lead", type="primary")

            if add_btn:
                if not name or not linkedin_url:
                    st.error("Name and LinkedIn URL are required.")
                else:
                    final_title = custom_title.strip() if title == "Other" else title
                    posts = [p.strip() for p in [post1, post2] if p.strip()]
                    existing_urls = [l["linkedin_url"] for l in st.session_state.sales_leads]
                    if linkedin_url.strip() in existing_urls:
                        st.warning("This LinkedIn URL is already in your list.")
                    else:
                        st.session_state.sales_leads.append({
                            "name": name.strip(),
                            "first_name": first.strip() or name.split()[0],
                            "last_name": last.strip() or " ".join(name.split()[1:]),
                            "title": final_title,
                            "school": school.strip(),
                            "linkedin_url": linkedin_url.strip(),
                            "posts": posts,
                            "email": "",
                            "subject": "",
                            "email_body": "",
                        })
                        st.success(f"Added {name}.")

        with col_list:
            st.markdown(f"**{len(st.session_state.sales_leads)} leads in session**")
            for i, l in enumerate(st.session_state.sales_leads):
                cols = st.columns([4, 1])
                with cols[0]:
                    email_badge = f" · {l['email']}" if l.get("email") else ""
                    wrote_badge = " ✅" if l.get("email_body") else ""
                    st.markdown(f"**{l['name']}** — {l.get('title','')} @ {l.get('school','')}{email_badge}{wrote_badge}")
                with cols[1]:
                    if st.button("✕", key=f"del_s_{i}"):
                        st.session_state.sales_leads.pop(i)
                        st.rerun()

        st.markdown("---")
        st.markdown("**Or import from CSV**")
        uploaded = st.file_uploader("Upload CSV (columns: name, first_name, last_name, title, school, linkedin_url)", type="csv", key="sales_csv_upload")
        if uploaded:
            import csv as _csv
            import io as _io
            reader = _csv.DictReader(_io.StringIO(uploaded.read().decode()))
            existing_urls = {l["linkedin_url"] for l in st.session_state.sales_leads}
            added = 0
            for row in reader:
                url = row.get("linkedin_url", "").strip()
                if url and url not in existing_urls:
                    st.session_state.sales_leads.append({
                        "name": row.get("name", ""),
                        "first_name": row.get("first_name", ""),
                        "last_name": row.get("last_name", ""),
                        "title": row.get("title", ""),
                        "school": row.get("school", ""),
                        "linkedin_url": url,
                        "posts": [],
                        "email": "",
                        "subject": "",
                        "email_body": "",
                    })
                    added += 1
            st.success(f"Imported {added} leads.")

    # ── Tab 2: Enrich emails ──────────────────────────────────────────────────
    with tab2:
        st.markdown("### Enrich emails via Surfe")

        needs_enrichment = [l for l in st.session_state.sales_leads if not l.get("email")]

        if not has_surfe:
            st.error("Surfe API key not found. Add `SURFE_API_KEY` to your secrets.")
        elif not needs_enrichment:
            if not st.session_state.sales_leads:
                st.info("Add leads in the 'Add Leads' tab first.")
            else:
                st.success("All leads already have emails.")
        else:
            st.info(f"{len(needs_enrichment)} leads need email enrichment. This will use **{len(needs_enrichment)}** of your 1,000 monthly Surfe credits.")

            if st.button("Enrich Emails", type="primary"):
                from core.surfe import enrich
                with st.spinner("Contacting Surfe…"):
                    try:
                        results = enrich(needs_enrichment)
                        found = 0
                        for lead in st.session_state.sales_leads:
                            url = lead["linkedin_url"]
                            if url in results and results[url]:
                                lead["email"] = results[url]
                                found += 1
                        no_email = [l for l in st.session_state.sales_leads if not l.get("email")]
                        st.success(f"Found {found} emails. {len(no_email)} leads had no match — you can remove them or keep them for LinkedIn-only outreach.")
                    except Exception as e:
                        st.error(f"Surfe error: {e}")

        if st.session_state.sales_leads:
            st.markdown("---")
            st.markdown("**Email status**")
            for l in st.session_state.sales_leads:
                status = f"✅ {l['email']}" if l.get("email") else "❌ No email found"
                st.markdown(f"- **{l['name']}** — {status}")

    # ── Tab 3: Generate emails ────────────────────────────────────────────────
    with tab3:
        st.markdown("### Generate personalised emails via Claude Teams")

        ready = [l for l in st.session_state.sales_leads if l.get("email")]

        if not ready:
            st.info("Enrich emails first (Tab 2), then come back here to generate outreach.")
        else:
            st.markdown(
                f"**{len(ready)} leads ready.** Follow the 3 steps below."
            )

            st.markdown("---")
            st.markdown("#### Step 1 — Copy this prompt")
            prompt = build_sales_prompt(ready)
            st.markdown('<div class="prompt-box">' + prompt.replace("<", "&lt;").replace(">", "&gt;") + '</div>', unsafe_allow_html=True)
            st.code(prompt, language=None)
            st.caption("Click the copy icon in the top-right of the box above.")

            st.markdown("---")
            st.markdown("#### Step 2 — Paste into Claude Teams")
            st.markdown(
                "Open [claude.ai](https://claude.ai) in a new tab, start a new chat, and paste the prompt. "
                "Claude will return a JSON array with one email per lead."
            )

            st.markdown("---")
            st.markdown("#### Step 3 — Paste Claude's response here")
            claude_response = st.text_area(
                "Paste Claude's full response here",
                height=200,
                placeholder='[{"linkedin_url": "...", "subject": "...", "email": "..."}, ...]',
                key="sales_claude_response",
            )

            if st.button("Apply Emails", type="primary", key="apply_sales"):
                if not claude_response.strip():
                    st.error("Paste Claude's response first.")
                else:
                    emails, err = parse_claude_response(claude_response)
                    if err:
                        st.error(err)
                    else:
                        st.session_state.sales_leads = merge_emails_into_leads(
                            st.session_state.sales_leads, emails
                        )
                        st.success(f"Applied {len(emails)} emails. Go to 'All Leads' to review and save.")

    # ── Tab 4: All leads ──────────────────────────────────────────────────────
    with tab4:
        st.markdown("### Review, approve, and save")

        if not st.session_state.sales_leads:
            st.info("No leads yet. Add some in the 'Add Leads' tab.")
        else:
            for i, lead in enumerate(st.session_state.sales_leads):
                card_class = "lead-card"
                st.markdown(f"""
<div class="{card_class}">
  <div class="lead-name">{lead.get('name','')}</div>
  <div class="lead-meta">
    {lead.get('title','')} &nbsp;·&nbsp; {lead.get('school','')} &nbsp;·&nbsp;
    <a href="{lead.get('linkedin_url','')}" target="_blank">LinkedIn ↗</a>
    {(' &nbsp;·&nbsp; ' + lead.get('email','')) if lead.get('email') else ''}
  </div>
  {'<div class="subj">📧 ' + lead.get('subject','') + '</div>' if lead.get('subject') else ''}
  {'<div class="body-text">' + lead.get('email_body','')[:600] + ('…' if len(lead.get('email_body','')) > 600 else '') + '</div>' if lead.get('email_body') else '<div style="color:#9e9e9e;font-size:12px">No email written yet</div>'}
</div>""", unsafe_allow_html=True)

            st.markdown("---")
            col_save, col_dl = st.columns(2)

            with col_save:
                if has_sheets:
                    if st.button("Save to Google Sheets", type="primary"):
                        from core.store import save_sales
                        with st.spinner("Saving…"):
                            try:
                                n = save_sales(st.session_state.sales_leads)
                                st.success(f"Saved {n} new leads to Google Sheets.")
                            except Exception as e:
                                st.error(f"Sheets error: {e}")
                else:
                    st.info("Add Google service account credentials to enable Sheets sync.")

            with col_dl:
                from core.store import sales_to_csv
                csv_data = sales_to_csv(st.session_state.sales_leads)
                st.download_button(
                    "⬇ Download CSV",
                    csv_data.encode(),
                    file_name="eduspark_sales_leads.csv",
                    mime="text/csv",
                )

            if st.button("Clear session leads", key="clear_sales"):
                st.session_state.sales_leads = []
                st.rerun()


# ═══════════════════════════════════════════════════════════════════════════════
# CREATOR MODE
# ═══════════════════════════════════════════════════════════════════════════════

else:
    st.markdown('<span class="badge badge-creator">CREATOR OUTREACH</span>', unsafe_allow_html=True)
    st.title("Creator Lead Generation")
    st.caption("Find educators and subject-matter experts on LinkedIn, add their profiles and posts, then generate personalised creator-invitation emails.")

    tab1, tab2, tab3 = st.tabs(["➕ Add Creators", "✍️ Generate Emails", "📋 All Creators"])

    # ── Tab 1: Add creators ───────────────────────────────────────────────────
    with tab1:
        st.markdown("### Add creator profiles")
        st.caption("Browse LinkedIn for educators in your target domain and country, then add them here.")

        col_form, col_list = st.columns([1, 1])

        with col_form:
            with st.form("add_creator_lead", clear_on_submit=True):
                st.markdown("**Profile details**")
                name = st.text_input("Full name *", placeholder="Alex Johnson")
                title = st.text_input("Title / Role *", placeholder="Education Consultant, Author, Trainer…")
                linkedin_url = st.text_input("LinkedIn URL *", placeholder="https://www.linkedin.com/in/...")

                col_a, col_b = st.columns(2)
                with col_a:
                    domain_choice = st.selectbox("Learning Domain *", LEARNING_DOMAINS)
                    custom_domain = st.text_input("Custom domain", placeholder="e.g. Robotics")
                with col_b:
                    country_choice = st.selectbox("Country *", COUNTRIES)
                    custom_country = st.text_input("Custom country", placeholder="e.g. Japan")

                st.markdown("**Recent posts** (paste up to 3 — these are what Claude uses to personalise the email)")
                post1 = st.text_area("Post 1 *", height=90, placeholder="Paste their most interesting recent post…")
                post2 = st.text_area("Post 2", height=80, placeholder="Paste another post…")
                post3 = st.text_area("Post 3", height=80, placeholder="One more…")

                add_btn = st.form_submit_button("Add Creator", type="primary")

            if add_btn:
                if not name or not linkedin_url or not post1:
                    st.error("Name, LinkedIn URL, and at least one post are required.")
                else:
                    domain = custom_domain.strip() if domain_choice == "Other" else domain_choice
                    country = custom_country.strip() if country_choice == "Other" else country_choice
                    posts = [p.strip() for p in [post1, post2, post3] if p.strip()]
                    existing_urls = {l["linkedin_url"] for l in st.session_state.creator_leads}
                    if linkedin_url.strip() in existing_urls:
                        st.warning("This LinkedIn URL is already in your list.")
                    else:
                        st.session_state.creator_leads.append({
                            "name": name.strip(),
                            "title": title.strip(),
                            "domain": domain,
                            "country": country,
                            "linkedin_url": linkedin_url.strip(),
                            "posts": posts,
                            "subject": "",
                            "email_body": "",
                        })
                        st.success(f"Added {name}.")

        with col_list:
            st.markdown(f"**{len(st.session_state.creator_leads)} creators in session**")
            for i, l in enumerate(st.session_state.creator_leads):
                cols = st.columns([4, 1])
                with cols[0]:
                    wrote_badge = " ✅" if l.get("email_body") else ""
                    st.markdown(
                        f"**{l['name']}** — {l.get('domain','')} · {l.get('country','')}"
                        f" · {len(l.get('posts',[]))} posts{wrote_badge}"
                    )
                with cols[1]:
                    if st.button("✕", key=f"del_c_{i}"):
                        st.session_state.creator_leads.pop(i)
                        st.rerun()

        st.markdown("---")
        st.markdown("**Or import from CSV**")
        uploaded = st.file_uploader(
            "Upload CSV (columns: name, title, domain, country, linkedin_url, post1, post2, post3)",
            type="csv", key="creator_csv_upload",
        )
        if uploaded:
            import csv as _csv
            import io as _io
            reader = _csv.DictReader(_io.StringIO(uploaded.read().decode()))
            existing_urls = {l["linkedin_url"] for l in st.session_state.creator_leads}
            added = 0
            for row in reader:
                url = row.get("linkedin_url", "").strip()
                if url and url not in existing_urls:
                    posts = [row.get(f"post{j}", "").strip() for j in range(1, 4) if row.get(f"post{j}", "").strip()]
                    st.session_state.creator_leads.append({
                        "name": row.get("name", ""),
                        "title": row.get("title", ""),
                        "domain": row.get("domain", ""),
                        "country": row.get("country", ""),
                        "linkedin_url": url,
                        "posts": posts,
                        "subject": "",
                        "email_body": "",
                    })
                    added += 1
            st.success(f"Imported {added} creators.")

    # ── Tab 2: Generate emails ────────────────────────────────────────────────
    with tab2:
        st.markdown("### Generate creator invitation emails via Claude Teams")

        ready = [l for l in st.session_state.creator_leads if l.get("posts")]

        if not ready:
            st.info("Add creators with at least one post in the 'Add Creators' tab first.")
        else:
            st.markdown(f"**{len(ready)} creators ready.**")

            st.markdown("---")
            st.markdown("#### Step 1 — Copy this prompt")
            prompt = build_creator_prompt(ready)
            st.code(prompt, language=None)
            st.caption("Click the copy icon in the top-right of the code box above.")

            st.markdown("---")
            st.markdown("#### Step 2 — Paste into Claude Teams")
            st.markdown(
                "Open [claude.ai](https://claude.ai), start a new chat, and paste the prompt. "
                "Claude will return a JSON array with one invitation email per creator."
            )

            st.markdown("---")
            st.markdown("#### Step 3 — Paste Claude's response here")
            claude_response = st.text_area(
                "Paste Claude's full response here",
                height=200,
                placeholder='[{"linkedin_url": "...", "subject": "...", "email": "..."}, ...]',
                key="creator_claude_response",
            )

            if st.button("Apply Emails", type="primary", key="apply_creator"):
                if not claude_response.strip():
                    st.error("Paste Claude's response first.")
                else:
                    emails, err = parse_claude_response(claude_response)
                    if err:
                        st.error(err)
                    else:
                        st.session_state.creator_leads = merge_emails_into_leads(
                            st.session_state.creator_leads, emails
                        )
                        st.success(f"Applied {len(emails)} emails. Go to 'All Creators' to review and save.")

    # ── Tab 3: All creators ───────────────────────────────────────────────────
    with tab3:
        st.markdown("### Review and save creator leads")

        if not st.session_state.creator_leads:
            st.info("No creators yet. Add some in the 'Add Creators' tab.")
        else:
            for lead in st.session_state.creator_leads:
                st.markdown(f"""
<div class="lead-card creator">
  <div class="lead-name">{lead.get('name','')}</div>
  <div class="lead-meta">
    {lead.get('title','')} &nbsp;·&nbsp; {lead.get('domain','')} &nbsp;·&nbsp; {lead.get('country','')}
    &nbsp;·&nbsp; <a href="{lead.get('linkedin_url','')}" target="_blank">LinkedIn ↗</a>
    &nbsp;·&nbsp; {len(lead.get('posts',[]))} posts
  </div>
  {'<div class="subj">📧 ' + lead.get('subject','') + '</div>' if lead.get('subject') else ''}
  {'<div class="body-text">' + lead.get('email_body','')[:600] + ('…' if len(lead.get('email_body','')) > 600 else '') + '</div>' if lead.get('email_body') else '<div style="color:#9e9e9e;font-size:12px">No email written yet</div>'}
</div>""", unsafe_allow_html=True)

            st.markdown("---")
            col_save, col_dl = st.columns(2)

            with col_save:
                if has_sheets:
                    if st.button("Save to Google Sheets", type="primary", key="save_creator"):
                        from core.store import save_creator
                        with st.spinner("Saving…"):
                            try:
                                n = save_creator(st.session_state.creator_leads)
                                st.success(f"Saved {n} new creators to Google Sheets.")
                            except Exception as e:
                                st.error(f"Sheets error: {e}")
                else:
                    st.info("Add Google service account credentials to enable Sheets sync.")

            with col_dl:
                from core.store import creator_to_csv
                csv_data = creator_to_csv(st.session_state.creator_leads)
                st.download_button(
                    "⬇ Download CSV",
                    csv_data.encode(),
                    file_name="eduspark_creator_leads.csv",
                    mime="text/csv",
                )

            if st.button("Clear session creators", key="clear_creator"):
                st.session_state.creator_leads = []
                st.rerun()
