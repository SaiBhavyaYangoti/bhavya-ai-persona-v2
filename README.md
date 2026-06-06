# Bhavya AI Persona

An AI representative of Yangoti Sai Bhavya that can answer questions about her background, projects, and experience - and book interviews directly on her calendar. No human in the loop.

## Live Demo

| Interface | Link |
|-----------|------|
| 📞 Voice Agent | Call **+1 (239) 663 4199** |
| 💬 Chat UI | [huggingface.co/spaces/Bhavya077/bhavya-ai](https://huggingface.co/spaces/Bhavya077/bhavya-ai) |


## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        PART A — VOICE AGENT                     │
│                                                                  │
│  Caller → Vapi → Deepgram (STT) → GPT-4o → Naina TTS → Caller  │
│                       ↓                                         │
│              FastAPI backend (Render)                            │
│                       ↓                                         │
│                   Cal.com API                                    │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                      PART B — CHAT INTERFACE                    │
│                                                                  │
│  User → Streamlit (HuggingFace Spaces)                          │
│              ↓                                                   │
│     RAG Pipeline:                                               │
│       Resume (section-aware chunks)  ──┐                        │
│       GitHub READMEs (120-word chunks) ┼→ ChromaDB              │
│                                        ↓                        │
│              all-MiniLM-L6-v2 embeddings                        │
│                        ↓                                        │
│              Groq LLaMA-3.3-70B                                 │
│                        ↓                                        │
│                   Cal.com API                                    │
└─────────────────────────────────────────────────────────────────┘

             Shared: Cal.com → Google Calendar
```


## Tech Stack

| Component | Technology |
|-----------|-----------|
| Voice orchestration | Vapi |
| Speech-to-text | Deepgram (flux-general-en) |
| Voice LLM | GPT-4o |
| Text-to-speech | Vapi Naina |
| Voice tool backend | FastAPI on Render |
| Chat UI | Streamlit on HuggingFace Spaces |
| Embeddings | all-MiniLM-L6-v2 (sentence-transformers) |
| Vector store | ChromaDB (ephemeral, built on startup) |
| Chat LLM | Groq LLaMA-3.3-70B-Versatile |
| Calendar | Cal.com API + Google Calendar |


## Repository Structure

```
bhavya-ai/
├── voice-backend/
│   └── main.py                  # FastAPI server for Vapi tool calls
│   └── requirements.txt
├── chat/
│   └── streamlit_app.py         # Streamlit RAG chat app
│   └── Yangoti Sai Bhavya Resume.pdf
│   └── requirements.txt
└── README.md
```


## Setup Instructions

### Part A — Voice Agent

#### 1. Deploy the FastAPI backend

```bash
git clone https://github.com/SaiBhavyaYangoti/bhavya-ai-backend
cd voice-backend
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```

Or deploy directly to Render — connect your GitHub repo and it auto-deploys.

#### 2. Configure Vapi

1. Sign up at [vapi.ai](https://vapi.ai)
2. Create a new assistant → Blank template
3. Set the system prompt (see `voice-backend/system_prompt.txt`)
4. Add two function tools:
   - `checkAvailability` → POST `https://your-render-url.onrender.com/check-availability`
   - `bookMeeting` → POST `https://your-render-url.onrender.com/book-meeting`
5. Set timeout to 30 seconds on both tools
6. Get a free US phone number from Vapi → assign it to the assistant

#### 3. Configure Cal.com

1. Sign up at [cal.com](https://cal.com)
2. Connect Google Calendar under Settings → Calendars
3. Create a 30-minute event type
4. Generate an API key under Settings → Developer → API Keys
5. Add the API key to your Render environment variables as `CAL_API_KEY`


### Part B — Chat Interface

#### Local Setup

```bash
git clone https://github.com/SaiBhavyaYangoti/bhavya-ai
cd chat
pip install -r requirements.txt
```

Create `.streamlit/secrets.toml`:

```toml
GROQ_API_KEY_1 = "your_groq_api_key_1"
GROQ_API_KEY_2 = "your_groq_api_key_2"
CAL_API_KEY = "your_cal_api_key"
```

Run the app:

```bash
streamlit run streamlit_app.py
```

#### Deploy to HuggingFace Spaces

1. Go to [huggingface.co/spaces](https://huggingface.co/spaces) → New Space
2. Select Docker → Streamlit template
3. Upload `streamlit_app.py`, `requirements.txt`, and `Yangoti Sai Bhavya Resume.pdf` to the `src/` folder
4. Go to Settings → Variables and Secrets and add:
   - `GROQ_API_KEY_1`
   - `GROQ_API_KEY_2`
   - `CAL_API_KEY`

The app will build automatically and be publicly accessible.


## RAG Design

The chat interface uses a two-source RAG pipeline:

**Resume** — chunked by section (not fixed-size), so each chunk contains a semantically complete unit:
- `personal_info` — name, contact, links
- `skills` — full skills list
- `experience` — all 3 internships in one chunk
- `education` — degree, institution, CGPA
- `publications` — both IEEE papers
- `projects` — all resume projects
- `achievements` — GATE rank, awards

**GitHub READMEs** — fetched dynamically via GitHub API at startup, chunked at 120 words with 20-word overlap.

All resume sections are always injected into retrieval context before GitHub chunks, preventing GitHub content from overriding verified resume facts. Follow-up queries are expanded using the previous user message to maintain conversation context across turns.


## Cost Breakdown

### Voice Agent (per call)

| Component | Rate | Typical 3-min call |
|-----------|------|-------------------|
| Vapi platform | $0.05/min | $0.15 |
| Deepgram STT | $0.01/min | $0.03 |
| GPT-4o | $0.02/min | $0.06 |
| Naina TTS | $0.02/min | $0.06 |
| **Total** | **~$0.10/min** | **~$0.30/call** |

### Chat Interface (per session)

| Component | Rate | Typical session (10 messages) |
|-----------|------|-------------------------------|
| Groq LLaMA-3.3-70B | Free tier | $0.00 |
| HuggingFace Spaces hosting | Free tier | $0.00 |
| ChromaDB (ephemeral, in-memory) | Free | $0.00 |
| **Total** | **Free** | **$0.00/session** |

> The chat interface runs entirely on free tiers. Groq's free tier allows 100K tokens/day — sufficient for evaluation traffic. Voice calls cost ~$0.30 each on Vapi's pay-as-you-go plan with $10 free credits on signup.


## Evals Summary

| Metric | Result |
|--------|--------|
| Voice first-response latency | ~1.15s average |
| Transcription accuracy | ~94% |
| Booking completion rate | 8/8 test calls |
| Chat hallucination rate | 1/15 questions (7%) |
| Retrieval precision | 13/15 (87%) |

Full evaluation methodology and failure analysis in [`eval_report.pdf`](./eval_report.pdf).


## Known Limitations

- Email transcription via voice is error-prone for complex addresses — a fallback booking link is recommended for production
- Groq free tier has a 100K token/day limit — two API keys are used with automatic fallback
- The RAG knowledge base is built in-memory on every cold start (~15 seconds) since HuggingFace Spaces doesn't persist binary files
