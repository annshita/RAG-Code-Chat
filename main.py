import streamlit as st
import os

# Fix for Streamlit Cloud "Security Violation [pathsec.open]: refusing multiply-linked file"
# Force NLTK and LlamaIndex to use a temporary writable directory instead of the bundled static cache.
os.environ["NLTK_DATA"] = "/tmp/nltk_data"
os.environ["LLAMA_INDEX_CACHE_DIR"] = "/tmp/llama_index_cache"

from llama_index.core import Settings, VectorStoreIndex, PromptTemplate
from llama_index.embeddings.gemini import GeminiEmbedding
from llama_index.llms.gemini import Gemini
from llama_index.readers.github import GithubRepositoryReader, GithubClient
import re
from dotenv import load_dotenv

# Load environment variables (built-in keys - never surfaced in UI)
load_dotenv()

# ---------------------------------------------------------------------------
# Helper: detect quota / rate-limit errors
# ---------------------------------------------------------------------------
QUOTA_KEYWORDS = [
    "quota", "rate limit", "resource_exhausted", "resource exhausted",
    "429", "too many requests", "limit exceeded", "rateLimitExceeded",
]

def is_quota_error(exc: Exception) -> bool:
    msg = str(exc).lower()
    return any(kw.lower() in msg for kw in QUOTA_KEYWORDS)


# ---------------------------------------------------------------------------
# Key resolution: prefer user-supplied keys, fall back to built-in
# ---------------------------------------------------------------------------
def get_gemini_key() -> str:
    return (
        st.session_state.get("user_gemini_key") or
        os.getenv("GEMINI_API_KEY", "")
    )

def get_github_token() -> str:
    return (
        st.session_state.get("user_github_token") or
        os.getenv("GITHUB_TOKEN", "")
    )


# ---------------------------------------------------------------------------
# API key dialog (shown when quota is hit or user clicks Add API Keys)
# ---------------------------------------------------------------------------
@st.dialog("API Limit Reached - Add Your Own Keys")
def show_api_key_dialog():
    st.markdown(
        "The built-in API quota has been exceeded. "
        "Enter your own keys below to continue. "
        "Your keys are stored only for this session and are **never** saved or logged."
    )
    st.markdown("---")

    gemini_key = st.text_input(
        "Gemini API Key",
        type="password",
        placeholder="AIza...",
        value=st.session_state.get("user_gemini_key", ""),
        help="Get yours at https://aistudio.google.com/app/apikey",
    )
    github_token = st.text_input(
        "GitHub Personal Access Token",
        type="password",
        placeholder="github_pat_...",
        value=st.session_state.get("user_github_token", ""),
        help="Get yours at https://github.com/settings/tokens",
    )

    col_save, col_cancel = st.columns(2)
    with col_save:
        if st.button("Save & Retry", type="primary", use_container_width=True):
            if gemini_key.strip():
                st.session_state["user_gemini_key"] = gemini_key.strip()
            if github_token.strip():
                st.session_state["user_github_token"] = github_token.strip()
            st.session_state["show_api_dialog"] = False
            st.success("Keys saved! Please retry your last action.")
            st.rerun()
    with col_cancel:
        if st.button("Cancel", use_container_width=True):
            st.session_state["show_api_dialog"] = False
            st.rerun()

def parse_github_url(url):
    pattern = r"https?://github\.com/([^/]+)/([^/]+)(?:/tree/([^/]+))?"
    match = re.match(pattern, url)
    if not match:
        raise ValueError("Invalid GitHub repository URL")
    owner, repo, branch = match.groups()
    return owner, repo, branch if branch else "main"

@st.cache_resource
def load_github_data(github_token, owner, repo, branch="main"):
    github_client = GithubClient(github_token)
    loader = GithubRepositoryReader(
        github_client,
        owner=owner,
        repo=repo,
        filter_file_extensions=(
            [".py", ".ipynb", ".js", ".ts", ".md"], 
            GithubRepositoryReader.FilterType.INCLUDE
        ),
        verbose=False,
        concurrent_requests=5,
    )
    return loader.load_data(branch=branch)

def run_rag_completion(query_text: str, docs) -> str:
    api_key = get_gemini_key()

    llm = Gemini(
        model="models/gemini-3.5-flash",
        api_key=api_key,
    )
    embed_model = GeminiEmbedding(
        model_name="models/gemini-embedding-2",
        api_key=api_key,
    )

    Settings.llm = llm
    Settings.embed_model = embed_model

    index = VectorStoreIndex.from_documents(docs)
    query_engine = index.as_query_engine(similarity_top_k=5, streaming=True)

    qa_prompt_tmpl = PromptTemplate(
        "Context information is below.\n"
        "---------------------\n"
        "{context_str}\n"
        "---------------------\n"
        "Given the context information, please answer the query.\n"
        "Query: {query_str}\n"
        "Answer: "
    )

    query_engine.update_prompts({"response_synthesizer:text_qa_template": qa_prompt_tmpl})
    response = query_engine.query(query_text)
    return str(response)


# ---------------------------------------------------------------------------
# Main app
# ---------------------------------------------------------------------------
def main():
    st.set_page_config(page_title="🧜‍♀️Code Chat", layout="wide")

    # -- Session state defaults ----------------------------------------------
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "docs" not in st.session_state:
        st.session_state.docs = None
    if "show_api_dialog" not in st.session_state:
        st.session_state["show_api_dialog"] = False

    # -- Open API-key dialog if flagged --------------------------------------
    if st.session_state["show_api_dialog"]:
        show_api_key_dialog()

    # -- Header --------------------------------------------------------------
    st.title("🧜‍♀️Code Chat")
    st.caption("Powered by 🌈Google Gemini and 🦙LlamaIndex")

    # Show badge when user-supplied keys are active
    if st.session_state.get("user_gemini_key") or st.session_state.get("user_github_token"):
        st.success("Using your custom API keys for this session.", icon="✅")

    # -- GitHub URL Input ----------------------------------------------------
    st.subheader("GitHub Repository")
    repo_url = st.text_input(
        "GitHub Repository URL",
        placeholder="Enter repository URL",
        label_visibility="collapsed",
    )

    if st.button("Load Repository", type="primary"):
        if repo_url:
            try:
                github_token = get_github_token()
                gemini_api_key = get_gemini_key()

                if not github_token or not gemini_api_key:
                    st.error(
                        "Missing API keys. Click **Add API Keys** below to add your own."
                    )
                    st.stop()

                owner, repo, branch = parse_github_url(repo_url)
                with st.spinner("Loading repository..."):
                    st.session_state.docs = load_github_data(github_token, owner, repo, branch)
                st.success("Repository loaded successfully")

            except Exception as e:
                if is_quota_error(e):
                    st.session_state["show_api_dialog"] = True
                    st.rerun()
                else:
                    st.error(f"Error: {str(e)}")

    st.write("")  # spacing

    # -- Action Buttons ------------------------------------------------------
    col1, col2, col3 = st.columns(3)
    with col1:
        st.link_button("Star Repo", "https://github.com/annshita/RAG-Code-Chat", use_container_width=True)
    with col2:
        if st.button("Clear Chat", use_container_width=True):
            st.session_state.messages = []
            st.rerun()
    with col3:
        if st.button("Add API Keys", use_container_width=True):
            st.session_state["show_api_dialog"] = True
            st.rerun()

    # -- Chat messages -------------------------------------------------------
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # -- Chat input ----------------------------------------------------------
    if prompt := st.chat_input("Ask about the repository..."):
        if not st.session_state.docs:
            st.error("Please load a repository first")
            st.stop()

        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    response = run_rag_completion(prompt, st.session_state.docs)
                    st.markdown(response)
                    st.session_state.messages.append({"role": "assistant", "content": response})

                    @st.fragment
                    def download_response(resp: str):
                        st.download_button(
                            label="Download message",
                            type="secondary",
                            data=resp,
                            file_name="chatbot_response.md",
                            mime="text/plain",
                            icon=":material/download:",
                        )

                    download_response(response)

                except Exception as e:
                    if is_quota_error(e):
                        st.session_state["show_api_dialog"] = True
                        st.warning(
                            "API quota exceeded. A dialog has opened — add your own keys to continue."
                        )
                        st.rerun()
                    else:
                        st.error(f"Error: {str(e)}")


if __name__ == "__main__":
    main()
