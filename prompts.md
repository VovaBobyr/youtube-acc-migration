Create a complete, production-ready Python CLI project that migrates YouTube channel subscriptions from one Google account to another using the official YouTube Data API v3.

Project goal:
- Authenticate a source Google account
- Read all subscribed YouTube channels from that account
- Save the subscriptions locally as a backup
- Authenticate a target Google account
- Subscribe the target account to the same channels
- Support safe retry and resume

Important note:
This tool is for personal account migration only. Build it conservatively, with clear rate limiting, logging, and resume support.

Technical requirements:
1. Language:
   - Python 3.11+

2. API and auth:
   - Use the official Google / YouTube Data API v3
   - Use OAuth 2.0 installed-app flow
   - Support two separate account sessions:
     - source account
     - target account
   - Store OAuth tokens separately for each account

3. Core functionality:
   - Fetch all subscriptions from the source account
   - Handle pagination correctly
   - Extract at minimum:
     - channelId
     - channelTitle
   - Save the exported subscriptions to a local JSON file
   - Read that JSON file for migration
   - Subscribe the target account to each channel
   - Before subscribing, check whether the target account is already subscribed and skip duplicates
   - Support resume if the script is interrupted

4. Rate limiting and quota safety:
   - Add configurable delay between write operations
   - Add exponential backoff for retryable API errors
   - Respect quota limitations
   - Log quota-related errors clearly
   - Add a dry-run mode that performs everything except the actual subscribe calls

5. CLI commands:
   Build a proper CLI with argparse or typer with commands like:
   - auth-source
   - auth-target
   - export-subscriptions
   - import-subscriptions
   - migrate
   - status

   Example desired usage:
   - python main.py auth-source
   - python main.py auth-target
   - python main.py export-subscriptions --output data/source_subscriptions.json
   - python main.py migrate --input data/source_subscriptions.json --delay 3 --resume
   - python main.py migrate --input data/source_subscriptions.json --dry-run

6. Project structure:
Create a clean project structure like this:

youtube_subscription_migrator/
  README.md
  requirements.txt
  .env.example
  main.py
  config.py
  auth.py
  youtube_client.py
  exporter.py
  migrator.py
  state.py
  logger.py
  utils.py
  data/
  tokens/
  logs/

7. File responsibilities:
   - config.py:
     configuration loading from environment variables and defaults
   - auth.py:
     OAuth login flow and token storage for both accounts
   - youtube_client.py:
     wrapper around YouTube API calls
   - exporter.py:
     export source subscriptions to JSON
   - migrator.py:
     migration logic from JSON to target account
   - state.py:
     persist migration progress and resume state
   - logger.py:
     structured logging setup
   - utils.py:
     retry helpers, sleep helpers, JSON helpers
   - main.py:
     CLI entry point

8. Data format:
Use a JSON format like:

[
  {
    "channel_id": "UCxxxxxxxxxx",
    "title": "Channel Name"
  }
]

Also keep a migration state file like:

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

9. Logging:
   - Log to console and file
   - Use readable timestamps
   - Log summary statistics:
     - total found
     - already subscribed
     - newly subscribed
     - failed
     - skipped
   - Make logs easy to debug

10. Error handling:
   - Handle invalid credentials
   - Handle expired tokens
   - Handle quotaExceeded
   - Handle rateLimitExceeded
   - Handle forbidden / subscription not allowed cases
   - Handle network/transient errors
   - Never crash on one failed channel; continue and record failures

11. README:
Create a detailed README.md with:
   - project overview
   - prerequisites
   - how to create a Google Cloud project
   - how to enable YouTube Data API v3
   - how to create OAuth client credentials for a desktop app
   - where to place credentials.json
   - how to authenticate both accounts
   - how to export subscriptions
   - how to migrate subscriptions
   - how resume works
   - how dry-run works
   - limitations and quota notes
   - troubleshooting section

12. requirements.txt:
Include the required dependencies, preferably:
   - google-api-python-client
   - google-auth
   - google-auth-oauthlib
   - google-auth-httplib2
   - requests
   - python-dotenv
Optionally:
   - typer or argparse only if chosen
   - tenacity for retries

13. Code quality:
   - Write clean, modular, readable code
   - Add type hints
   - Add docstrings
   - Avoid unnecessary complexity
   - Use classes only where they help
   - Keep functions small and focused
   - Make the project runnable immediately after credentials are supplied

14. Implementation details for YouTube API:
   - Read subscriptions using subscriptions().list with:
     - part="snippet"
     - mine=True
     - maxResults=50
   - Create subscriptions using subscriptions().insert with appropriate snippet.resourceId.kind and channelId
   - Build helper methods for:
     - list_subscriptions()
     - export_subscriptions()
     - is_already_subscribed()
     - subscribe_to_channel()

15. Deliverables:
Generate all project files with full code, not placeholders.
After generating the files, also provide:
   - a short explanation of the architecture
   - exact setup instructions
   - example commands to run the full migration

16. Constraints:
   - Do not use Docker
   - Do not use a database; use JSON files only
   - Do not use unsafe browser automation or scraping
   - Use only the official API
   - Keep it suitable for Windows and Linux

17. Extra improvement:
   - Add an option to limit the number of subscriptions processed in one run
   - Add an option to retry only failed channels
   - Add a final summary report JSON file

Please generate the full project now, with all files and code included.