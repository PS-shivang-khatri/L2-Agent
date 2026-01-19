# L2 Project

## Overview
This project demonstrates an AI agent that can call custom Python functions (tools) using the MCP protocol and an LLM (Mistral 7B via Ollama). The agent can:
- Get weather for coordinates
- Recommend books by topic
- Tell a random joke
- Show a random dog image
- Give a trivia question

## Setup
1. Clone this repository and open the folder in VS Code.
2. Create and activate a Python virtual environment:
   ```
   python -m venv .venv
   .venv\Scripts\activate  # On Windows
   ```
3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Install and run Ollama (see https://ollama.com/download) and pull the Mistral 7B model:
   ```
   ollama pull mistral:7b
   ```

## Usage
1. Start the MCP server:
   ```
   python server.py
   ```
2. In a new terminal (with the venv activated), run the agent:
   ```
   python agent_fun.py
   ```
3. Try queries like:
   - Tell me a joke.
   - Get weather for latitude 40.7 and longitude -74.
   - Recommend books about science.
   - Show me a random dog.
   - Give me a trivia question.

## Notes
- If you encounter errors about missing packages, rerun `pip install -r requirements.txt`.
- If you see errors about pywin32, run:
  ```
  python Scripts/pywin32_postinstall.py -install
  ```
- Make sure Ollama is running and the Mistral model is pulled before starting the agent.

---

For questions or issues, contact the project maintainer.
