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

# Load environment variables
load_dotenv()

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
    llm = Gemini(
        model="models/gemini-3.5-flash",
        api_key=os.getenv("GEMINI_API_KEY")
    )

    embed_model = GeminiEmbedding(
        model_name="models/gemini-embedding-2",
        api_key=os.getenv("GEMINI_API_KEY")
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

def main():
    st.set_page_config(page_title="Code Chat", layout="wide")

    @st.fragment
    def download_response(response:str) :
        st.download_button(
                label="Download message",
                type="secondary",
                data=response,
                file_name="chatbot_response.md",
                mime="text/plain",
                icon=":material/download:",
            )
    
    # Initialize session states
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "docs" not in st.session_state:
        st.session_state.docs = None
    
    # Header
    st.title("🧚🏻‍♀️Code Chat")
    st.caption("Powered by 🍓 Google Gemini and 🌷 LlamaIndex")
    
    # GitHub URL Input
    st.subheader("GitHub Repository")
    repo_url = st.text_input("GitHub Repository URL", placeholder="Enter repository URL", label_visibility="collapsed")
    
    if st.button("Load Repository", type="primary"):
        if repo_url:
            try:
                github_token = os.getenv("GITHUB_TOKEN")
                gemini_api_key = os.getenv("GEMINI_API_KEY")
                
                if not github_token or not gemini_api_key:
                    st.error("Missing API keys")
                    st.stop()
                
                owner, repo, branch = parse_github_url(repo_url)
                with st.spinner("Loading repository..."):
                    st.session_state.docs = load_github_data(github_token, owner, repo, branch)
                st.success("✓ Repository loaded successfully")
            except Exception as e:
                st.error(f"Error: {str(e)}")
                
    st.write("") # Add some spacing
    
    # Action Buttons
    col1, col2 = st.columns(2)
    with col1:
        st.link_button("✨ Star Repo", "https://github.com/annshita/RAG-Code-Chat", use_container_width=True)
    with col2:
        if st.button("🍃 Clear Chat", use_container_width=True):
            st.session_state.messages = []
            st.rerun()
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask about the repository..."):
        if not st.session_state.docs:
            st.error("Please load a repository first")
            st.stop()
        
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Generate response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    response = run_rag_completion(prompt, st.session_state.docs)
                    st.markdown(response)
                    st.session_state.messages.append({"role": "assistant", "content": response})
                    download_response(response)
                except Exception as e:
                    st.error(f"Error: {str(e)}")

if __name__ == "__main__":
    main()

