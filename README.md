# 🧜‍♀️ RAG Code Chat

A Streamlit application that uses the Google Gemini API and LlamaIndex to let you chat with GitHub repositories!

## Features

- 💬 **Chat with any GitHub repo** — ask questions about code, docs, and more
- 🔍 **RAG-powered answers** — powered by LlamaIndex vector search + Gemini LLM
- 🔑 **Bring Your Own API Keys** — if the built-in quota is exceeded, a popup lets you add your own Gemini and GitHub keys without restarting the app
- 🔒 **Key privacy** — built-in keys are never shown in the UI; user-provided keys are stored only for the current browser session and never persisted to disk

## Steps to Run

### 1. Navigate to the Project Directory
Change into the directory containing `main.py` and `requirements.txt`:
```sh
cd rag_code_chat
```

### 2. Setup the Virtual Environment and Dependencies
It's recommended to use a virtual environment. Create and activate it, then install the required Python packages:

**On Windows:**
```powershell
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

**On Linux/macOS:**
```shell
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Setup API Keys
Rename or copy `.env.example` to `.env` and fill it with your secrets. You will need:
- A **GitHub Personal Access Token** (for `GITHUB_TOKEN`).
- A **Gemini API Key** (for `GEMINI_API_KEY`), which you can get for free from [Google AI Studio](https://aistudio.google.com/app/apikey).

> **Note:** The `.env` keys are the built-in defaults. They are loaded server-side and are never exposed in the UI.

### 4. Run the Application
Start the Streamlit web interface:
```shell
streamlit run main.py
```
The app will open in your default browser. Paste a GitHub repository URL and start chatting!

## Using Your Own API Keys (Quota Exceeded)

If the built-in API quota runs out, the app will automatically show a popup dialog asking for your own keys. You can also open it manually at any time by clicking the **🔑 Add API Keys** button.

| Field | Where to get it |
|---|---|
| Gemini API Key | [Google AI Studio](https://aistudio.google.com/app/apikey) |
| GitHub Personal Access Token | [GitHub Settings → Tokens](https://github.com/settings/tokens) |

- Keys you enter are stored **only for the current session** — they disappear when you close or refresh the browser tab.
- A green banner is displayed at the top whenever your own keys are active.
- You can update your keys at any time by clicking **Add API Keys** again.
