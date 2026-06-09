# Claude Code — Quick Guide

Welcome to your hackathon workspace. This is a real Linux environment running in your browser, with an AI assistant called **Claude Code** ready to help you build things.

## Starting Claude Code

Open a terminal (top menu → **Terminal → New Terminal**) and run:

```
claude
```

You're in. Type what you want done; it'll either ask clarifying questions or get to work.

## Things you can ask it

- "Build a Python web server that returns 'hello' on port 8080."
- "Read every file in this folder and tell me what each does."
- "I'm getting this error: `<paste the error>` — fix it."
- "Turn this Streamlit script into a polished demo with charts."
- "Translate this Python code into Node.js."
- "Set me up a Vite + React project."
- "List the S3 buckets I can read, then pull a file from one."
- "Use boto3 to call Bedrock and summarize this document."

Claude Code can read files, edit them, run shell commands, search the web, and tell you honestly when it's stuck.

## When it asks permission

Some actions (running scripts, installing packages, deleting things) trigger a confirmation:

- **`y`** — allow this once
- **`Y`** — allow always for this kind of action
- **`n`** — refuse

Hit `Esc` to interrupt anytime.

## Sharing your app with teammates

When Claude builds a web app, it'll typically run it on a port like 3000, 5173, or 8080. **Make sure the app binds to `0.0.0.0`** (not `127.0.0.1`) — most frameworks have a `--host 0.0.0.0` flag.

Once running, look at the **Ports panel** in code-server (bottom of the screen). It auto-detects the port and gives you a URL like:

```
https://<your-team>.dragonarmy.rocks/proxy/<port>/
```

Send that URL to a teammate. They sign in with the same workspace password and see your running app live.

## Useful slash commands inside Claude Code

- `/help` — built-in command list
- `/cost` — see how many tokens you've used so far
- `/clear` — start the conversation fresh
- `/model` — confirm which model is being used

`Ctrl+C` exits Claude Code. Run `claude` again to come back.

## Bonus: supercharge Claude Code with Superpowers

**Superpowers** is a community plugin that adds structured workflows — brainstorming, test-driven development, systematic debugging, planning — that Claude Code pulls in automatically when they fit. Install it from inside Claude Code:

```
/plugin marketplace add obra/superpowers-marketplace
/plugin install superpowers@superpowers-marketplace
```

Then just work as normal — it kicks in on its own. Good practice for learning how the plugin system works.

## What's pre-installed

**Languages & runtimes**
- **Python 3.13** (pip + venv)
- **Node.js 22** + npm, and **Bun** (JavaScript/TypeScript runtimes)

**AI & AWS**
- **Claude Code** (terminal + VS Code extension), pre-wired to **Amazon Bedrock** — no API keys
- **AWS CLI** — read access to S3 and Bedrock via your workspace's IAM role
- Python SDKs: **boto3** (AWS) and **anthropic** (Bedrock-enabled)

**Quick-demo web frameworks** (great for shipping a clickable demo fast)
- **Streamlit**, **Gradio**, **FastAPI** + **Uvicorn**

**CLI tooling**
- **git**, **jq**, **ripgrep** (`rg`), **fd**, **make** + **gcc** (build-essential), curl, unzip

Need something else? Just ask Claude Code: "Install `<tool>` for me." It knows `apt-get`, `pip`, `npm`, and `bun`.

## Two important things to know

1. **This workspace is ephemeral.** If it restarts, files in your home folder vanish. Push to a git repo early and often. Claude Code can do this for you: "Initialize git, make a first commit, and push to a new GitHub repo."
2. **Bedrock is already authenticated for you.** No API keys to manage. No quotas to babysit. Just build.

## Stuck?

Tell Claude Code: "I'm stuck — here's what I tried, here's what happened." Paste any error messages verbatim. It almost always finds the fix from there.

Have fun. Build something cool.
