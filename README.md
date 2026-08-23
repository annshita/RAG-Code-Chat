# Chat with Code

## Steps to Run

**Navigate to the Project Directory:**
Change to the directory where the `setup.sh`, `main.py`, `requirements.txt`, and `README.md` files are located. For example:
```sh
cd Examples/Chat_with_Code
```

### 1. Run the Setup File
Make the setup.sh Script Executable (if necessary):
On Linux or macOS, you might need to make the setup.sh script executable:
```shell
chmod +x setup.sh
```
Execute the setup.sh script to set up the environment and install dependencies:
```shell
./setup.sh
```
Now, fill in the `.env` file with your secrets. You will need:
- A GitHub Personal Access Token (for `GITHUB_TOKEN`).
- A Gemini API Key (for `GEMINI_API_KEY`), which you can get for free from [Google AI Studio](https://aistudio.google.com/app/apikey).

### 2. Run the Python Script
```shell
source ~/.venvs/chat_with_code/bin/activate

streamlit run main.py
```
