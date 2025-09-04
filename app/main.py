\
import os, time, json, random, re, datetime, uuid
from dataclasses import dataclass, asdict
import pandas as pd
import requests
from jinja2 import Template

# ---------------- Config ----------------
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama").lower()
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://ollama:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "mistral")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

SMTP_HOST = os.getenv("SMTP_HOST", "mailhog")
SMTP_PORT = int(os.getenv("SMTP_PORT", "1025"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASS = os.getenv("SMTP_PASS", "")
FROM_NAME = os.getenv("FROM_NAME", "Acme SDR")
FROM_EMAIL = os.getenv("FROM_EMAIL", "sdr@acme.test")

LEADS_CSV = os.getenv("LEADS_CSV", "/data/leads.csv")
OUTPUT_CSV = os.getenv("OUTPUT_CSV", "/data/leads_out.csv")
GENERATE_FAKE_REPLIES = os.getenv("GENERATE_FAKE_REPLIES", "true").lower() == "true"
MAX_LEADS = int(os.getenv("MAX_LEADS", "0"))

MAILHOG_API = "http://mailhog:8025/api/v2/messages"
REPORTS_DIR = "/reports"

# -------------- Utilities ---------------

def wait_for_ollama():
    if LLM_PROVIDER != "ollama":
        return
    for _ in range(60):
        try:
            r = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=5)
            if r.ok:
                return
        except Exception:
            pass
        print("Waiting for Ollama ...")
        time.sleep(2)
    print("Warning: Ollama may not be ready, continuing anyway.")

def llm(prompt: str, temperature: float = 0.4, max_tokens: int = 512) -> str:
    if LLM_PROVIDER == "ollama":
        # Ensure model is pulled
        try:
            requests.post(f"{OLLAMA_HOST}/api/pull", json={"name": OLLAMA_MODEL}, timeout=10)
        except Exception:
            pass
        # Stream generate
        url = f"{OLLAMA_HOST}/api/generate"
        resp = requests.post(url, json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False, "options":{"temperature":temperature}}, timeout=120)
        resp.raise_for_status()
        data = resp.json()
        return data.get("response","").strip()
    elif LLM_PROVIDER == "groq":
        if not GROQ_API_KEY:
            raise RuntimeError("GROQ_API_KEY missing")
        headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type":"application/json"}
        url = "https://api.groq.com/openai/v1/chat/completions"
        payload = {"model": GROQ_MODEL, "messages":[{"role":"user","content":prompt}], "temperature":temperature, "max_tokens":max_tokens}
        r = requests.post(url, headers=headers, json=payload, timeout=120)
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"].strip()
    else:
        raise RuntimeError(f"Unsupported LLM_PROVIDER: {LLM_PROVIDER}")

def send_email(to_email, subject, body, message_id=None):
    import smtplib
    from email.mime.text import MIMEText
    from email.utils import formataddr, make_msgid
    
    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = formataddr((FROM_NAME, FROM_EMAIL))
    msg["To"] = to_email
    msg["Message-ID"] = message_id or make_msgid(domain="acme.test")
    
    if SMTP_USER and SMTP_PASS:
        server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
    else:
        server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
    server.send_message(msg)
    server.quit()
    return msg["Message-ID"]

def fetch_mailhog_messages():
    try:
        r = requests.get(MAILHOG_API, timeout=30)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print("MailHog fetch error:", e)
        return {"total":0,"items":[]}

def classify_response(text: str) -> str:
    # Quick rules first
    t = text.lower()
    rules = [
        ("unsubscribe" in t or "remove me" in t, "Unsubscribe"),
        ("out of office" in t or "ooo" in t, "Out of Office"),
        ("not interested" in t or "no thanks" in t, "Not Interested"),
        ("interested" in t or "let's talk" in t or "book a call" in t, "Interested"),
        ("bounce" in t or "delivery failed" in t, "Bounce"),
    ]
    for cond, label in rules:
        if cond:
            return label
    # Backstop with LLM
    prompt = f"""Classify the email reply into one of: Interested, Not Interested, Out of Office, Follow Up Later, Unsubscribe, Bounce, Other.
Reply with only the label.

Email:
{text}
"""
    try:
        return llm(prompt, temperature=0.0, max_tokens=5).splitlines()[0].strip()
    except Exception:
        return "Other"

EMAIL_TEMPLATE = Template("""\
Hi {{ first_name or name }},

I noticed {{ company or 'your team' }} {{ insight }}. We help {{ persona }} teams save time by {{ value_prop }}.

Would you be open to a quick chat next week? Happy to share a short demo tailored to {{ company or 'your context' }}.

Best,
{{ from_name }}
""")

def draft_email(lead, persona, insight, value_prop):
    subject = f"Quick idea for {lead.get('company','your team')}"
    body = EMAIL_TEMPLATE.render(
        first_name=lead.get("first_name",""),
        name=lead.get("name",""),
        company=lead.get("company",""),
        persona=persona,
        insight=insight,
        value_prop=value_prop,
        from_name=FROM_NAME,
    )
    return subject, body

def enrich_and_score(lead):
    # Call LLM once to get persona, score, insight, value prop
    context = f"Lead: {json.dumps(lead, ensure_ascii=False)}"
    prompt = f"""
You are an SDR assistant. Given the lead JSON, return a compact JSON with fields:
persona (string), priority (1-100 integer), missing_fields (list of keys to fill), insight (short 1 line), value_prop (short 1 line), enriched (dict with any missing fields guessed).

Return ONLY JSON.
{context}
"""
    try:
        raw = llm(prompt, temperature=0.3, max_tokens=300)
        # Attempt to find JSON in text
        m = re.search(r"\{.*\}", raw, re.S)
        data = json.loads(m.group(0) if m else raw)
    except Exception as e:
        data = {"persona":"Unknown","priority":50,"missing_fields":[],"insight":"recent growth","value_prop":"automate manual steps","enriched":{}}
    # Merge enrichment
    enriched = lead.copy()
    enriched.update(data.get("enriched", {}))
    persona = data.get("persona","Unknown")
    priority = int(data.get("priority",50))
    insight = data.get("insight","recent growth")
    value_prop = data.get("value_prop","automate manual steps")
    return enriched, persona, priority, insight, value_prop

def simulate_replies(sent_records, n=8):
    # Send some fake replies back into MailHog to demonstrate classification
    templates = [
        "Hi, I'm interested. Can we book a call next Tuesday?",
        "Out of office until next week. Please follow up later.",
        "Not interested at the moment, thanks.",
        "Please remove me from your mailing list and unsubscribe.",
        "Delivery failed: user mailbox full (bounce).",
        "Let's talk — Wednesday afternoon works.",
        "No thanks.",
        "Thanks, but we're covered. Try again next quarter."
    ]
    chosen = random.sample(templates, k=min(n, len(templates)))
    for i, rec in enumerate(sent_records):
        if i >= len(chosen):
            break
        reply = chosen[i]
        # From lead back to us
        try:
            send_email(FROM_EMAIL, f"Re: {rec['subject']}", reply, message_id=f"<reply-{uuid.uuid4()}@acme.test>")
        except Exception as e:
            print("Sim reply send failed:", e)

def main():
    wait_for_ollama()
    print("Starting pipeline...")
    df = pd.read_csv(LEADS_CSV)
    if MAX_LEADS and MAX_LEADS > 0:
        df = df.head(MAX_LEADS)
    results = []
    sent_records = []

    for idx, row in df.iterrows():
        lead = {k: (str(row[k]).strip() if pd.notna(row[k]) else "") for k in df.columns}
        enriched, persona, priority, insight, value_prop = enrich_and_score(lead)
        subject, body = draft_email(enriched, persona, insight, value_prop)
        try:
            msgid = send_email(enriched.get("email","test@example.com"), subject, body)
            sent_status = "Sent"
            sent_records.append({"email": enriched.get("email",""), "subject": subject, "msgid": msgid})
        except Exception as e:
            sent_status = f"SendError: {e}"

        results.append({
            **enriched,
            "persona": persona,
            "priority": priority,
            "insight": insight,
            "value_prop": value_prop,
            "email_subject": subject,
            "email_body": body,
            "status": sent_status,
            "last_response": "",
            "response_category": "No Response Yet",
        })
        print(f"[{idx+1}/{len(df)}] {enriched.get('email')} -> {sent_status} (priority {priority})")

    # Simulate some replies for demo
    if GENERATE_FAKE_REPLIES:
        simulate_replies(sent_records, n=8)

    # Classify any replies in MailHog
    msgs = fetch_mailhog_messages().get("items", [])
    inbox_replies = []
    for m in msgs:
        try:
            to_addrs = [h["Mailbox"]+"@"+h["Domain"] for h in m["To"]]
        except Exception:
            to_addrs = []
        if FROM_EMAIL in to_addrs:
            body = m.get("Content",{}).get("Body","")
            inbox_replies.append(body)

    # Map replies back to leads by simple heuristic (first come)
    i = 0
    for r in results:
        if i < len(inbox_replies):
            body = inbox_replies[i]
            cat = classify_response(body)
            r["last_response"] = body[:240]
            r["response_category"] = cat
            r["status"] = "Replied"
            i += 1

    out_df = pd.DataFrame(results).sort_values(by=["response_category","priority"], ascending=[True, False])
    out_df.to_csv(OUTPUT_CSV, index=False)
    print(f"Wrote {OUTPUT_CSV} with {len(out_df)} rows.")

    # ---- Report ----
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    stats = {
        "total": len(out_df),
        "sent": (out_df["status"] == "Sent").sum() + (out_df["status"] == "Replied").sum(),
        "replied": (out_df["status"] == "Replied").sum(),
    }
    by_cat = out_df["response_category"].value_counts().to_dict()
    top_personas = out_df["persona"].value_counts().head(5).to_dict()

    report_md = f"""# Campaign Summary — {now}

- **Total Leads:** {stats['total']}
- **Delivered (Sent+Replied):** {stats['sent']}
- **Replies:** {stats['replied']}

## Responses by Category
{json.dumps(by_cat, indent=2)}

## Top Personas (LLM-suggested)
{json.dumps(top_personas, indent=2)}

## Notable Leads
"""
    for _, r in out_df.sort_values(by="priority", ascending=False).head(5).iterrows():
        report_md += f"- {r.get('name','(no name)')} — {r.get('company','')} — priority {r.get('priority')} — {r.get('response_category')}\n"

    os.makedirs(REPORTS_DIR, exist_ok=True)
    report_path = os.path.join(REPORTS_DIR, f"report-{datetime.datetime.now().strftime('%Y%m%d-%H%M')}.md")
    with open(report_path, "w") as f:
        f.write(report_md)
    print(f"Wrote report to {report_path}")

if __name__ == "__main__":
    main()
