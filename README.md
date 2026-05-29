# sturdy-telegram

## Configure the environnement

1.Installing uv : <https://docs.astral.sh/uv/#installation>
> It's an extremely fast Python package and project manager like `pip`, written in Rust.

2.Installing dependencies
Once uv installed, you're going to install project's dependencies (listed in pyproject.toml) through this command:

```bash
uv sync
```

3.Putting your Bright Data Key API
On the .env file, replace the '<..>' with your Bright data key API

## Run the app

You should be place in root project. To run the server, for now, you you can use:

```bash
uv run steamlit run app.py
```
