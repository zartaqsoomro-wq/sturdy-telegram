<<<<<<< HEAD
"This is the backend" 
=======
# sturdy-telegram

## Configure the environnement

1.**Installing uv** : <https://docs.astral.sh/uv/#installation>
> It's an extremely fast Python package and project manager like `pip`, written in Rust.

2.**Installing dependencies**
Once uv installed, you're going to install project's dependencies (listed in pyproject.toml) through this command:

```bash
uv sync
```

3.**Setting up your API Keys**

- Create a `.env` file (like `.env`.exemple) at the root of the project and add your API keys. You can generate them using the links below:
- Bright Data: [Billing & Keys Overview](https://brightdata.com/cp/billing/overview)
- AI/ML API: [Get API Key](https://aimlapi.com/app/keys?from=get-api-key)
- Cognee: [Documentation](https://www.cognee.ai/) (Note: Cognee uses the AI/ML API key under the hood for its LLM engine).

Your `.env` file should look like this:

```env
BRIGHT_DATA_API_KEY="your_bright_data_key_here"
AIML_API_KEY="your_aiml_api_key_here"
```

## Test individual modules

Before running the full dashboard, you can verify that each step of the pipeline works perfectly in isolation:

1.Test Search & Scraping (Bright Data)

```bash
uv run python -m backend.services.serp_client
```

2.Test AI Processing & Structuring (AI/ML API)
*(Make sure to run step 1 first to generate the `test_output.json` file)*

```bash
uv run python -m backend.services.data_processor
```

3.Test Knowledge Graph Memory (Cognee)

```bash
uv run python -m backend.services.cognee_client
```

## Run the app

You should be place in root project. To run the server, for now, you you can use:

```bash
uv run steamlit run app.py
```
>>>>>>> 810d71c75b2369e80723010920b0325ff723823d
