---
marp: true
theme: default
paginate: true
---

# YouTube Account Migration Tool

Move all YouTube subscriptions from one account to another.

GitHub:
https://github.com/VovaBobyr/youtube-acc-migration

---

# Step 1 — Create Google Cloud Project

1. Open Google Cloud Console
2. Click **Select project**
3. Click **New project**

Name it:

youtube-subscription-migrator

---

# Step 2 — Enable YouTube API

Go to:

APIs & Services → Library

Search for:

YouTube Data API v3

Click **Enable**

---

# Step 3 — Create OAuth Client

Clients → Create client

Application type: Desktop app

Download:

credentials.json

---

# Step 4 — Prepare Project Folder

1. Clone or download the project:

   ```bash
   git clone https://github.com/VovaBobyr/youtube-acc-migration.git
   cd youtube-acc-migration
   ```

2. Put the downloaded OAuth JSON into the project root and name it:

   ```text
   credentials.json
   ```

---

# Step 5 — Configure `.env`

1. Copy example env file:

   ```bash
   cp .env.example .env
   ```

2. Open `.env` and check:

- `GOOGLE_API_CLIENT_SECRETS_FILE=credentials.json`
- `LOG_LEVEL=INFO` (or `DEBUG`)
- `DEFAULT_DELAY_SECONDS=2.0`
- `MAX_DELAY_SECONDS=30.0`
- `MAX_RETRY_ATTEMPTS=5`

---

# Step 6 — Install Dependencies

From the project folder:

```bash
python -m venv .venv
```

Activate virtual env:

- Windows: `.venv\Scripts\activate`
- macOS/Linux: `source .venv/bin/activate`

Install packages:

```bash
pip install -r requirements.txt
```

---

# Step 7 — Start Interactive Menu

Run the tool:

```bash
python main.py
```

Menu options:

- `1` — Authenticate **source** account
- `2` — Authenticate **target** account
- `3` — Export subscriptions from source
- `4` — Migrate subscriptions to target
- `5` — Show migration status
- `0` — Exit

---

# Step 8 — Default Flow (1 → 2 → 3 → 4)

**Step 1 — Option 1: Source auth**

- Choose `1`
- In browser: sign in with **source** YouTube/Google account

**Step 2 — Option 2: Target auth**

- Choose `2`
- In browser: sign in with **target** YouTube/Google account  
  (use “Use another account” if needed)

**Step 3 — Option 3: Export**

- Choose `3`
- When asked for path: accept default `data/source_subscriptions.json`

**Step 4 — Option 4: Migrate**

- Choose `4`
- Input JSON path: press Enter for `data/source_subscriptions.json`
- Delay between operations: type `2` (safe default)
- Resume from previous state: **Yes**
- Dry run only: **No** to really subscribe (use **Yes** only for testing)
- Retry only failed channels: **No** on the first full run
- Limit subscriptions: leave blank to migrate all

Then migration starts and writes logs + summary.

---

# Step 9 — Important Files

- `data/source_subscriptions.json`  
  Exported list of channels from source

- `data/migration_state.json`  
  Progress + which channels were processed / failed

- `data/migration_summary.json`  
  Final run statistics (total, newly subscribed, failed, skipped)

- `tokens/source_token.json` / `tokens/target_token.json`  
  OAuth tokens for source and target accounts

- `logs/app.log`  
  Detailed log for debugging

---

# Step 10 — Quick Troubleshooting

- **Credentials file missing**  
  Make sure `credentials.json` exists in project root and `.env` points to it.

- **Invalid JSON / empty `credentials.json`**  
  Re-download the Desktop app JSON from Google Cloud and save directly as `credentials.json`.

- **403: app not verified / test users**  
  Add both source and target emails as **Test users** on the OAuth consent screen.

- **All channels skipped**  
  Check you did **not** run in dry-run mode and did **not** enable “retry failed only” on the first run.
