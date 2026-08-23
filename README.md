# RAG Code Chat

A Streamlit application that uses the Google Gemini API and LlamaIndex to let you chat with GitHub repositories! 

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

### 4. Run the Application
Start the Streamlit web interface:
```shell
streamlit run main.py
```
The app will open in your default browser. Paste a GitHub repository URL into the sidebar and start chatting!
