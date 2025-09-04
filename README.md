AI Sales Campaign CRM (MVP)

One-command demo:

docker compose up --build

What Happens

20+ sample leads are ingested from data/leads.csv.

Leads are scored, enriched, and persona-suggested.

Personalized emails are drafted using a free LLM (Ollama by default).

Emails are sent to MailHog (view at http://localhost:8025
).

CSV is updated at data/leads_out.csv with persona, priority, and status.

A Markdown campaign summary is written to reports/ (PDF optional).

Configure (Optional)

Override defaults via .env:

LLM_PROVIDER=ollama           # or 'groq' if you set GROQ_API_KEY
OLLAMA_MODEL=gemma-3-4b       # default is 'mistral'; pulled automatically
SMTP_HOST=mailhog
SMTP_PORT=1025
FROM_NAME=Acme SDR
FROM_EMAIL=sdr@acme.test
LEADS_CSV=/data/leads.csv
OUTPUT_CSV=/data/leads_out.csv
GENERATE_FAKE_REPLIES=true
MAX_LEADS=0                   # 0 = process all leads


Restart Docker Compose after changing .env:

docker compose down
docker compose up --build

Using the Leads CSV

Place your leads in data/leads.csv:

Name,Email,Company,Notes
John Doe,john@example.com,ACME Corp,Interested in AI solutions
Jane Smith,jane@example.com,Globex,Follow up next week


Output CSV is automatically saved as data/leads_out.csv.

Google Sheets (Optional)

This MVP focuses on CSV for simplicity.

To use Google Sheets later:

Install gspread and oauth2client.

Add a small adapter to fetch leads and write back results.

The interfaces in main.py are already separated to make integration easy.

Development Tips

MailHog UI: http://localhost:8025

Ollama API: http://localhost:11434

Reports: reports/report-*.md (PDF can be generated from Markdown)

Example: Generate PDF Report from Markdown
import markdown2, pdfkit

md_file = "reports/report.md"
pdf_file = "reports/report.pdf"

html = markdown2.markdown(open(md_file).read())
pdfkit.from_string(html, pdf_file)

Example: Draft Email via Ollama API
import os
import requests

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma-3-4b")

prompt = "Write a personalized outreach email for John Doe at ACME Corp"
resp = requests.post(
    f"{OLLAMA_HOST}/api/completions",
    json={"model": OLLAMA_MODEL, "prompt": prompt, "max_tokens": 200}
)
email_text = resp.json()["completion"]
print(email_text)

Customizing Behavior
Variable	Description
OLLAMA_MODEL	Choose AI model (e.g., mistral, gemma-3-4b)
OLLAMA_FORCE_GPU	Force GPU usage
LEADS_CSV	Input CSV path
OUTPUT_CSV	Enriched CSV path
SMTP_HOST / SMTP_PORT	Email server configuration
FROM_NAME / FROM_EMAIL	Sender info
MAX_LEADS	Max leads to process
GENERATE_FAKE_REPLIES	Use realistic replies for demo/testing
Stopping the System
docker compose down


Ollama models remain in ollama-data Docker volume.

Troubleshooting
Issue	Fix
MailHog empty	Check SMTP_HOST / SMTP_PORT, refresh UI
GPU not used	Set OLLAMA_FORCE_GPU=true and verify NVIDIA Docker runtime
Model not found	Run docker compose exec ollama ollama pull gemma-3-4b
CSV not updating	Check folder permissions (data/ folder)
