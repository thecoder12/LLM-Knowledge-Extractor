# Jouster Summarizer

A production-ready Django REST API for text summarization and keyword extraction, supporting multiple LLM engines (OpenAI, Gemini) and spaCy NLP, fully containerized with Docker.

## Features
- **Summarization API**: Summarize text using OpenAI, Gemini, or Mistral LLMs.
- **Keyword Extraction**: Extracts keywords from text using spaCy NLP.
- **Multi-engine Support**: Easily switch between LLM providers via API.
- **Dockerized**: Reproducible builds and deployments using Docker.
- **Django REST Framework**: Robust, extensible API backend.
- **Database**: Uses SQLite by default (can be swapped for Postgres).

## Project Structure
```
Jouster/
├── DRF_main/           # Django project settings, URLs, WSGI
├── Summarizer/         # Summarizer app (views, models, migrations)
├── env/                # Local Python virtual environment (ignored in Docker)
├── db.sqlite3          # SQLite database
├── manage.py           # Django management script
├── requirements.txt    # Python dependencies
├── Dockerfile          # Docker build instructions
└── ...
```

## Setup (Local)
1. **Clone the repo**
2. Create a virtual environment:
   ```sh
   python3 -m venv .venv
   source .venv/bin/activate
   ```
3. Install dependencies:
   ```sh
   pip install --upgrade pip
   pip install -r requirements.txt
   ```
4. Run migrations:
   ```sh
   python manage.py makemigrations
   python manage.py migrate
   ```

## Environment Variables
- Set your LLM API keys in `.env` (not included in repo):
  ```
  OPENAI_API_KEY=...
  GEMINI_API_KEY=...
  ```

5. Start the server:
   ```sh
   python manage.py runserver
   ```

## API Usage
- **POST /summarize/**
  - `text`: Text to summarize
  - `engine`: (optional) 'openai' or 'gemini'(default). For openai `?engine=openai`
- **Response**: JSON with summary and keywords



## Notes
- The Docker build creates a Python venv, installs all dependencies, downloads the spaCy model, runs migrations, and starts Django on port 9000.
- For production, use a real database and configure allowed hosts, secrets, etc.

## Troubleshooting
- If Docker build fails on Apple Silicon, always use `--platform linux/amd64`.
- If venv issues persist, ensure Docker Desktop is up to date.

## License
MIT
