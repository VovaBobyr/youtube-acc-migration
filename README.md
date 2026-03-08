YouTube Subscription Migrator
=============================

This is a Python 3.11+ CLI tool for migrating YouTube channel subscriptions from one personal Google account to another using the official YouTube Data API v3.

## 📊 Quick Setup Slides

For a **visual step-by-step setup guide**, see:

👉 **[Setup Slides](docs/setup-slides.md)**

The tool:

- Authenticates a **source** Google account
- Reads all subscribed YouTube channels from that account
- Saves the subscriptions locally as a JSON backup
- Authenticates a **target** Google account
- Subscribes the target account to the same channels
- Supports safe retry, resume, dry-run, and rate limiting


> **Note**  
> This tool is intended for **personal account migration only**. Use it responsibly and within YouTube API quota limits.

Project structure
-----------------

The project is structured as follows:

- `README.md`: this documentation
- `requirements.txt`: Python dependencies
- `.env.example`: example environment configuration
- `main.py`: CLI entry point
- `config.py`: configuration loading from environment variables and defaults
- `auth.py`: OAuth login flow and token storage for source/target accounts
- `youtube_client.py`: wrapper around YouTube Data API v3 calls
- `exporter.py`: export source subscriptions to JSON
- `migrator.py`: migration logic from JSON to target account
- `state.py`: migration progress and resume state persistence
- `logger.py`: structured logging setup
- `utils.py`: helpers for retries, sleeps, and JSON I/O
- `data/`: exported subscriptions, state, and summary reports
- `tokens/`: OAuth token files per account
- `logs/`: application log files

Prerequisites
-------------

- Python **3.11+**
- A Google account for the **source** YouTube channel
- A Google account for the **target** YouTube channel
- Ability to create and manage a project in Google Cloud Console

Google Cloud project and API setup
----------------------------------

1. **Create or select a Google Cloud project**

   - Visit the Google Cloud Console (`https://console.cloud.google.com/`).
   - If you don’t already have a project for this tool, create a new one.

2. **Enable the YouTube Data API v3**

   - In the Cloud Console, go to **APIs & Services → Library**.
   - Search for **“YouTube Data API v3”**.
   - Open it and click **Enable** for your project.

3. **Configure the OAuth consent screen (one-time)**

   - Go to **APIs & Services → OAuth consent screen**.
   - Click **Get started** (if you haven’t configured it yet).
   - **User type / Audience**: choose **External**.
   - Fill in **App information** (e.g., app name and support email).
   - Add your email as a test user if prompted.
   - Click through to **Finish**. You do **not** need to publish the app; testing mode is sufficient for personal use.

4. **Create OAuth client credentials (Desktop app)**

   - Go to **APIs & Services → Credentials**.
   - Click **Create Credentials → OAuth client ID**.
   - For **Application type**, choose **Desktop app**.
   - Click **Create**. Google will show:
     - **Client ID**
     - **Client secret**
     - A **Download JSON** button
   - Click **Download JSON** and save the file directly (do not create or edit it manually).

5. **Place `credentials.json`**

   - Save the downloaded JSON file as `credentials.json` in the **project root** directory (this directory), or adjust the path using the `GOOGLE_API_CLIENT_SECRETS_FILE` environment variable.
   - Confirm the file is valid JSON by opening it in a text editor: it should start with something like:

     ```json
     {
       "installed": {
         ...
     }
     ```

     and must not be empty or contain HTML or error text.

Environment configuration
-------------------------

1. Copy the example environment file:

   ```bash
   cp .env.example .env
   ```

2. Edit `.env` as needed:

- `GOOGLE_API_CLIENT_SECRETS_FILE`: path to your OAuth client credentials JSON (default `credentials.json` in the project root).
- `LOG_LEVEL`: logging level (`INFO`, `DEBUG`, etc.).
- `DEFAULT_DELAY_SECONDS`: default delay between subscription write operations.
- `MAX_DELAY_SECONDS`: maximum delay used by exponential backoff.
- `MAX_RETRY_ATTEMPTS`: maximum retry attempts for retryable API errors.

Installation
------------

1. Create and activate a virtual environment (recommended):

   ```bash
   python -m venv .venv
   # Windows
   .venv\Scripts\activate
   # Linux/macOS
   source .venv/bin/activate
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

CLI usage
---------

The main entrypoint is `main.py` in the project root.

### Interactive mode (menu)

If you simply run:

```bash
python main.py
```

you will enter an interactive text menu with options such as:

- `1` – Authenticate **source** account
- `2` – Authenticate **target** account
- `3` – Export subscriptions from source account
- `4` – Migrate subscriptions to target account
- `5` – Show migration status
- `0` – Exit

This is the easiest way to step through authentication and migration without remembering individual commands.

Before using the interactive menu for the first time, make sure you have:

- Enabled **YouTube Data API v3** for your Google Cloud project.
- Downloaded the **Desktop app OAuth client JSON** from the Google Cloud Console.
- Placed it as `credentials.json` in the project root (or configured `GOOGLE_API_CLIENT_SECRETS_FILE` accordingly).

#### Quick start: default interactive scenario

From a fresh setup, the typical flow is to run the menu and then select options **1 → 2 → 3 → 4** in order:

1. **Start the menu**

   ```bash
   python main.py
   ```

2. **Option 1 – Authenticate SOURCE account**

   - In the menu, enter `1`.
   - When the browser opens, sign in with your **source** YouTube/Google account.
   - When this succeeds once, the tool saves a source token file and you usually do not need to repeat this step.

3. **Option 2 – Authenticate TARGET account**

   - In the menu, enter `2`.
   - When the browser opens, sign in with your **target** YouTube/Google account (use “Use another account” if needed).
   - When this succeeds once, the tool saves a target token file and you usually do not need to repeat this step.

4. **Option 3 – Export subscriptions from SOURCE**

   - In the menu, enter `3`.
   - When prompted for the output path, you can normally accept the default:

     ```text
     data/source_subscriptions.json
     ```

   - This creates a JSON backup of all channels from the source account.

5. **Option 4 – Migrate subscriptions to TARGET (actual migration run)**

   - In the menu, enter `4`.
   - When prompted:
     - **Input JSON path for subscriptions**: press Enter to accept the default `data/source_subscriptions.json` (if you used option 3).
     - **Delay between operations in seconds**: choose a small positive value such as `2` to be gentle with rate limits.
     - **Resume from previous migration state if present?**: usually answer **Yes** (`y`) so you can safely restart if something interrupts the run.
     - **Dry run only (no actual subscriptions created)?**:
       - For a test run, answer **Yes** to see what would happen without changing the target account.
       - For a **real migration**, answer **No** so the tool actually subscribes the target account to each channel.
     - **Retry only previously failed channels?**:
       - On the **first** full run, answer **No** so all channels are processed.
       - Later, you can answer **Yes** if you only want to retry channels that failed in an earlier run.
     - **Limit number of subscriptions to process (blank for no limit)**:
       - Press Enter to migrate **all** channels.
       - Or provide a number (for example `50`) to process only that many in this run.

   - After you answer these questions, the migration will start. Watch the console and `logs/app.log` for progress; a summary JSON is written to `data/migration_summary.json`.

### Direct command usage

You can also run individual commands directly:

```bash
python main.py <command> [options]
```

Available commands
------------------

### Authenticate accounts

- **Authenticate source account** (read-only access for subscriptions):

  ```bash
  python main.py auth-source
  ```

- **Authenticate target account** (manage subscriptions):

  ```bash
  python main.py auth-target
  ```

- **Clear stored credentials** (optional, for troubleshooting or switching accounts):

  ```bash
  python main.py clear-auth --source --target
  ```

This will delete the cached tokens stored under `tokens/`.

### Export subscriptions

Export all subscriptions from the **source** account to a JSON file:

```bash
python main.py export-subscriptions --output data/source_subscriptions.json
```

The output file will look like:

```json
[
  {
    "channel_id": "UCxxxxxxxxxx",
    "title": "Channel Name"
  }
]
```

If `--output` is omitted, a default path (configured by `DEFAULT_EXPORT_FILENAME`) in the `data/` directory will be used.

### Migrate subscriptions

Run a full migration from a JSON export to the **target** account:

```bash
python main.py migrate --input data/source_subscriptions.json --delay 3 --resume
```

Options:

- `--input / -i`: path to the exported JSON file.
- `--delay / -d`: delay in seconds between subscription **write operations** (default: from config).
- `--resume / --no-resume`: whether to resume from an existing migration state file.
- `--dry-run`: do everything except actually create subscriptions.
- `--limit`: process at most N subscriptions in this run.
- `--retry-failed-only`: process only channels recorded as failed in the migration state file.

Examples:

- **Dry run** (no actual subscriptions created):

  ```bash
  python main.py migrate --input data/source_subscriptions.json --dry-run
  ```

- **Migrate with delay and resume**:

  ```bash
  python main.py migrate --input data/source_subscriptions.json --delay 3 --resume
  ```

- **Limit number of processed subscriptions**:

  ```bash
  python main.py migrate --input data/source_subscriptions.json --limit 50
  ```

- **Retry only previously failed channels**:

  ```bash
  python main.py migrate --input data/source_subscriptions.json --retry-failed-only
  ```

Resume and state file
---------------------

Migration progress is stored in a JSON **state file**, by default:

- `data/migration_state.json`

The format is:

```json
{
  "input_file": "data/source_subscriptions.json",
  "processed": [
    "UCxxxx1",
    "UCxxxx2"
  ],
  "failed": [
    {
      "channel_id": "UCxxxx3",
      "reason": "quotaExceeded"
    }
  ],
  "last_updated": "ISO_TIMESTAMP"
}
```

If the migration is interrupted or partially completes, re-running `migrate` with `--resume` will:

- Skip already processed channels
- Retain the list of failed channels
- Continue from where it left off

Dry-run mode
------------

With `--dry-run`, the tool:

- Checks which channels the target account is already subscribed to
- Logs which channels **would** be subscribed
- Does **not** perform any `subscriptions.insert` calls
- Updates the migration state as if they were successfully processed (for planning / what-if analysis)

Logging
-------

Logging is configured to write to:

- Console output
- `logs/app.log` (rotating log files)

Each log entry includes:

- Timestamp
- Log level
- Logger name
- Message

During migration, key summary information is logged:

- Total subscriptions found
- Already subscribed on target
- Newly subscribed
- Failed
- Skipped

Final summary report
--------------------

After a migration run, a JSON **summary report** is written (by default):

- `data/migration_summary.json`

It includes:

- `input_file`: path to the input subscriptions JSON
- `total`: total number of entries in the input
- `already_subscribed`: count already present on the target account
- `newly_subscribed`: count successfully subscribed during this run
- `failed`: count of failures
- `skipped`: count of skipped entries (e.g., already processed or invalid)
- `state_file`: path to the migration state file

Status command
--------------

To inspect the current migration state:

```bash
python main.py status
```

This prints:

- Input file path
- Processed count
- Failed count
- Last updated timestamp

Error handling
--------------

The tool attempts to handle and log:

- Invalid or missing credentials
- Expired tokens (refreshed automatically when possible)
- `quotaExceeded` and `rateLimitExceeded`
- `forbidden` / subscription-not-allowed errors
- Other network/transient API failures (with retries)

Failures for individual channels are:

- Logged with a reason
- Recorded in the `failed` array in the state file
- Do **not** stop the entire migration

Architecture overview
---------------------

- `config.py`: defines application configuration using environment variables and creates required directories.
- `auth.py`: manages OAuth 2.0 installed-app flow for separate **source** and **target** accounts, storing tokens under `tokens/`.
- `youtube_client.py`: wraps YouTube Data API v3 client (`subscriptions.list` and `subscriptions.insert`), and provides helpers:
  - `list_all_subscriptions()`
  - `is_already_subscribed(channel_id)`
  - `subscribe_to_channel(channel_id)`
- `exporter.py`: uses the source `YouTubeClient` to enumerate all subscriptions and save them to JSON.
- `state.py`: maintains migration state and provides methods to load/save/mark processed/failed channels.
- `migrator.py`: orchestrates reading from JSON, checking existing subscriptions, creating new ones with rate limiting, resume, limit, and retry-failed-only behaviors; writes a final summary report.
- `logger.py`: central logging configuration for console and rotating file handlers.
- `main.py`: Typer-based CLI that exposes commands:
  - `auth-source`
  - `auth-target`
  - `clear-auth`
  - `export-subscriptions`
  - `migrate`
  - `status`

Limitations and quota notes
---------------------------

- This tool depends on YouTube Data API v3 quotas associated with your Google Cloud project.
- Subscribing to a very large number of channels may consume significant quota or hit rate limits.
- The `--delay` parameter and built-in exponential backoff reduce the risk of hitting short-term limits but cannot override daily quota caps.
- Only personal accounts and standard YouTube channels are supported; brand accounts or restricted channels may behave differently.

Troubleshooting
---------------

- **`FileNotFoundError` for credentials**  
  Ensure your OAuth client JSON is accessible and `GOOGLE_API_CLIENT_SECRETS_FILE` points to the correct location.

- **`Expecting value: line 1 column 1 (char 0)` or similar JSON errors when authenticating**  
  Your `credentials.json` file is empty or not valid JSON. Re-download the OAuth **Desktop app** client JSON from the Google Cloud Console and save it directly to the project root as `credentials.json` (do not create or edit it manually).

- **Browser does not open for OAuth**  
  Copy and paste the URL from the terminal into a browser manually, then paste the authorization code if prompted.

- **Quota or rate limit errors**  
  Try increasing `--delay`, limiting the run with `--limit`, or retrying failed channels later with `--retry-failed-only`.

- **Unexpected crashes**  
  Check `logs/app.log` for stack traces and reasons. Since state is persisted, you can often safely re-run with `--resume`.

Platform support
----------------

The project is designed to work on **Windows** and **Linux** (and should also work on macOS) as long as Python 3.11+ is available and the required packages can be installed.

