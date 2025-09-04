# 🚀 AI Sales Campaign CRM (MVP)

[![Docker](https://img.shields.io/badge/Docker-Ready-blue?logo=docker)](https://www.docker.com/)
[![Ollama](https://img.shields.io/badge/Ollama-Supported-green?logo=ollama)](https://ollama.ai/)
[![MailHog](https://img.shields.io/badge/MailHog-Integrated-orange)](https://github.com/mailhog/MailHog)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A lightweight, Docker-ready CRM system that uses **local AI (Ollama)** to automatically score leads, generate buyer personas, create personalized outreach emails, and provide campaign analytics. **Zero external API costs** - runs entirely on your machine!

## ✨ Features

- 🎯 **AI-Powered Lead Scoring** - Automatic prioritization using local LLMs
- 🧠 **Buyer Persona Generation** - AI-generated customer profiles  
- 📧 **Personalized Email Creation** - Custom outreach for each lead
- 📊 **Campaign Analytics** - AI-written markdown reports with insights
- 🐳 **One-Command Deploy** - Complete Docker Compose setup
- 📨 **Email Testing** - Built-in MailHog for email preview
- 🔄 **CSV Pipeline** - Import leads → Enrich → Export results
- 🆓 **100% Free** - No API costs, runs locally with Ollama

---

## 🚀 **One-Command Demo**

```bash
docker compose up --build
```

**What Happens:**
1. 📥 25+ sample leads are ingested from `data/leads.csv`
2. 🤖 Leads are **scored, enriched, and persona-suggested** using local AI
3. ✍️ Personalized emails are drafted using Ollama LLM 
4. 📧 Emails are **sent to MailHog** (view at http://localhost:8025)
5. 💾 CSV is updated at `data/leads_out.csv` with persona, priority, and status
6. 📋 A **Markdown campaign summary** is written to `reports/`

**Access Points:**
- **MailHog Email UI:** http://localhost:8025
- **Ollama API:** http://localhost:11434  
- **Campaign Reports:** `reports/report-*.md`

---

## ⚙️ **Configuration (Optional)**

Override defaults via `.env`:

```bash
LLM_PROVIDER=ollama           # or 'groq' if you set GROQ_API_KEY
OLLAMA_MODEL=gemma2:2b        # default is 'gemma3'; pulled automatically
SMTP_HOST=mailhog
SMTP_PORT=1025
FROM_NAME=Acme SDR
FROM_EMAIL=sdr@acme.test
LEADS_CSV=/data/leads.csv
OUTPUT_CSV=/data/leads_out.csv
GENERATE_FAKE_REPLIES=true    # Creates realistic reply demos
MAX_LEADS=0                   # 0 = process all leads
```

**Restart after changing `.env`:**
```bash
docker compose down
docker compose up --build
```

---

## 📊 **Using Your Own Leads**

Place your leads in `data/leads.csv`:

```csv
Name,Email,Company,Title,Industry,Notes
John Doe,john@example.com,ACME Corp,CTO,Technology,Interested in AI solutions
Jane Smith,jane@globex.com,Globex Inc,VP Sales,Manufacturing,Follow up next week
Mike Johnson,mike@startup.io,StartupXYZ,CEO,SaaS,High priority prospect
```

**Output CSV** is automatically saved as `data/leads_out.csv` with:
- ✅ AI Lead Scores (1-100)
- ✅ Priority Levels (High/Medium/Low)  
- ✅ Buyer Personas
- ✅ Email Status & Timestamps
- ✅ Generated Email Content

---

## 🧠 **AI Models & Performance**

| Model | Size | Speed | Quality | RAM Usage |
|-------|------|-------|---------|-----------|
| `gemma2:2b` | 1.6GB | ⚡⚡⚡ | ⭐⭐⭐ | 4GB |
| `mistral` | 4.1GB | ⚡⚡ | ⭐⭐⭐⭐ | 8GB |  
| `llama3:8b` | 4.7GB | ⚡ | ⭐⭐⭐⭐⭐ | 16GB |

**Change model** via `.env`:
```bash
OLLAMA_MODEL=llama3:8b
```

**GPU Acceleration** (NVIDIA):
```bash
OLLAMA_FORCE_GPU=true
```

---

## 📁 **Project Structure**

```
ai-sales-crm/
├── 🐳 docker-compose.yml     # Container orchestration
├── 🐍 Dockerfile             # Python app container  
├── ⚡ main.py                # FastAPI application
├── 🧠 src/
│   ├── crm_pipeline.py       # Campaign workflow logic
│   ├── llm_service.py        # AI/Ollama integration
│   ├── models.py             # Data models
│   └── email_templates.py    # Email template fallbacks
├── 📊 data/
│   ├── leads.csv             # Input leads (sample included)
│   └── leads_out.csv         # Enriched output
├── 📋 reports/               # AI-generated campaign reports
└── 📝 logs/                  # Application logs
```

---

## 🔧 **Advanced Usage**

### **Generate PDF Reports from Markdown**

```python
import markdown2, pdfkit

md_file = "reports/report-20241201-143022.md"
pdf_file = "reports/report.pdf"

html = markdown2.markdown(open(md_file).read())
pdfkit.from_string(html, pdf_file)
```

### **Direct Ollama API Usage**

```python
import requests

OLLAMA_HOST = "http://localhost:11434"
OLLAMA_MODEL = "gemma2:2b"

prompt = "Write a personalized outreach email for John Doe at ACME Corp"
response = requests.post(
    f"{OLLAMA_HOST}/api/generate",
    json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False}
)
email_text = response.json()["response"]
print(email_text)
```

### **Google Sheets Integration** (Future Enhancement)

```python
# This MVP focuses on CSV for simplicity
# To add Google Sheets support:
# 1. pip install gspread oauth2client
# 2. Add OAuth credentials
# 3. Replace CSV read/write with Sheets API calls

import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Example adapter code for future enhancement
def read_from_sheets(sheet_id, range_name):
    # Implementation for Google Sheets integration
    pass
```

---

## 🎛️ **Configuration Reference**

| Variable | Description | Default |
|----------|-------------|---------|
| `LLM_PROVIDER` | AI provider (`ollama` or `groq`) | `ollama` |
| `OLLAMA_MODEL` | Ollama model name | `mistral` |
| `OLLAMA_FORCE_GPU` | Force GPU usage | `false` |
| `LEADS_CSV` | Input CSV file path | `/data/leads.csv` |
| `OUTPUT_CSV` | Output CSV file path | `/data/leads_out.csv` |
| `SMTP_HOST` / `SMTP_PORT` | Email server config | `mailhog` / `1025` |
| `FROM_NAME` / `FROM_EMAIL` | Sender information | `Acme SDR` / `sdr@acme.test` |
| `MAX_LEADS` | Max leads to process (0=all) | `0` |
| `GENERATE_FAKE_REPLIES` | Create demo email replies | `true` |

---

## 📧 **Sample Output**

### **Enriched Lead Data**
```csv
Name,Email,Company,Score,Priority,Buyer_Persona,Email_Sent,Email_Content
Sarah Johnson,sarah@techcorp.com,TechCorp,87,High,"Strategic CTO focused on innovation and scalability...",true,"Hi Sarah, I noticed TechCorp's recent expansion..."
```

### **AI Campaign Report**
```markdown
# 📊 Sales Campaign Report
*Generated: 2024-12-01 14:30:22*

## Executive Summary
- **Total Leads Processed:** 25
- **High Priority Prospects:** 8 (32%)  
- **Average Lead Score:** 72.3/100
- **Emails Sent:** 25/25 (100%)

## Top Industries
- Technology: 8 leads
- Healthcare: 5 leads  
- Finance: 4 leads

## Key Insights
High-scoring leads show strong decision-making authority...
```

---

## 🐛 **Troubleshooting**

| Issue | Fix |
|-------|-----|
| 📧 MailHog shows no emails | Check `SMTP_HOST`/`SMTP_PORT`, refresh UI |
| 🐌 Slow AI responses | Try smaller model: `OLLAMA_MODEL=gemma2:2b` |
| 🚫 GPU not detected | Set `OLLAMA_FORCE_GPU=true`, verify NVIDIA Docker runtime |
| 📝 Model not found | Run: `docker compose exec ollama ollama pull mistral` |
| 📁 CSV not updating | Check folder permissions for `data/` directory |
| 💾 Out of memory | Use lighter model or increase Docker memory limit |

---

## 🏭 **Production Deployment**

### **Replace MailHog with Real SMTP:**
```bash
# .env for production
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com  
SMTP_PASSWORD=your_app_password
FROM_EMAIL=your_email@gmail.com
```

### **Scale for Large Campaigns:**
- Add rate limiting for email sending
- Implement Redis for job queuing
- Use PostgreSQL for lead storage
- Add monitoring and alerting

---

## 🛠️ **Development**

### **Local Development (without Docker)**
```bash
# Install dependencies
pip install -r requirements.txt

# Install and start Ollama locally
curl -fsSL https://ollama.com/install.sh | sh
ollama serve &
ollama pull mistral

# Run application
export LLM_PROVIDER=ollama
python main.py
```

### **Adding Features**
- **New AI Provider:** Extend `LLMService` class
- **Custom Templates:** Modify `EmailTemplates`  
- **New Data Sources:** Update `ingest_leads()` method
- **Enhanced Analytics:** Improve `generate_campaign_report()`

---

## 🧪 **Testing**

```bash
# Run with test data
docker compose up --build

# View test emails
open http://localhost:8025

# Check generated reports
ls -la reports/

# View enriched leads
head data/leads_out.csv
```

---

## 📄 **License**

MIT License - see [LICENSE](LICENSE) file for details.

---

## 🤝 **Contributing**

1. Fork the repository
2. Create feature branch: `git checkout -b feature-name`
3. Commit changes: `git commit -am 'Add feature'`
4. Push branch: `git push origin feature-name`
5. Submit pull request

---

## ⭐ **Star History**

If this project helped you, please consider giving it a star! ⭐

---

## 🔗 **Related Projects**

- [Ollama](https://ollama.ai/) - Local AI models
- [MailHog](https://github.com/mailhog/MailHog) - Email testing
- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework

---

## 📞 **Support**

- 🐛 **Issues:** [GitHub Issues](https://github.com/Shehjad-Ishan/ai-sales-crm/issues)
- 📧 **Email:** shehjadishan211@gmail.com
- 💬 **Discussions:** [GitHub Discussions](https://github.com/Shehjad-Ishan/ai-sales-crm/discussions)

---

**Ready to supercharge your sales outreach with AI?** 🚀

```bash
git clone https://github.com/yourusername/ai-sales-crm.git
cd ai-sales-crm
docker compose up --build
```

**Visit http://localhost:8025 to see your AI-generated emails in action!** 📧✨
