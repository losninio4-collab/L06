# gmail-calendar

A local MCP server for Gmail and Google Calendar, using FastMCP over stdio.
It has no tool that sends or deletes anything.

| Tool | What it does |
|---|---|
| `search_emails(query, max_results)` | Search Gmail (1-50 results) |
| `read_email(message_id)` | Read one email |
| `create_draft(to, subject, body)` | Save a draft; never sends it |
| `list_events(days_ahead)` | List upcoming events |
| `find_free_slots(date, duration_minutes)` | Find free periods, 08:00-20:00 |
| `create_event(title, start, end, description)` | Create an event without guests |

All times use `Asia/Jerusalem`. Only the primary calendar is used.
Events marked "Free" and declined invitations do not block a slot.

## Requirements

- [uv](https://docs.astral.sh/uv/) (it installs Python and the packages)
- Gmail API and Google Calendar API enabled in your Google Cloud project
- A private folder **outside this project** with exactly one
  `client_secret*.json`, and a `token.json`

The token must already have these scopes (or broader ones):

- `https://www.googleapis.com/auth/gmail.readonly`
- `https://www.googleapis.com/auth/gmail.compose`
- `https://www.googleapis.com/auth/calendar.events`

`gmail.compose` technically allows sending, but this server has no send tool.

## Run

In PowerShell, from this folder:

```powershell
uv sync
$env:GOOGLE_PRIVATE_DIR = "<private folder>"
uv run server.py
```

The server waits silently for an MCP client. Press Ctrl+C to stop.

## Test

Offline unit tests (Google is mocked; no account or secrets needed):

```powershell
uv run pytest
```

Live test. It needs the real Google files, makes a read-only `list_events` call,
and prints your event details, so check the output before sharing it:

```powershell
$env:GOOGLE_PRIVATE_DIR = "<private folder>"
uv run test_server.py
```

## Add to Claude Code

Run this from the project folder, replacing `<private folder>`:

```powershell
claude mcp add gmail-calendar --scope local --transport stdio --env GOOGLE_PRIVATE_DIR=<private folder> '--' uv run --directory $PWD server.py
```

## Security

- Secrets stay in the private folder; they are never copied, changed or printed.
- Access tokens are refreshed in memory only.
- The server never opens a browser. If the token expires or is revoked,
  create `token.json` again with last week's sign-in script.

## Prompts used (2026-11-24)

Prompts are quoted as written, except that a third party's email address is
replaced with `[email]`. The note in parentheses in prompt 21 was added later. The Gmail and Calendar work in prompts 7-11, 16 and 17
used the claude.ai connectors, not this server.

1. In one sentence: which folder are you working in, and is it empty?
2. Check that the folder C:\my-private contains a Google client file (client_secret*.json) and a token.json file. Only tell me whether each file exists and its date. Do NOT print the contents of these files.
3. The build prompt:

   ```text
   Build an MCP server in Python in the current folder, named "gmail-calendar". Use the official MCP Python SDK (FastMCP), run it with uv, and use the stdio transport. It must reuse the Google client and token.json from last week. They are in the private folder C:\my-private; read that path from the environment variable GOOGLE_PRIVATE_DIR. Never copy these files into this project, never print secrets, and never open a browser from the server. Expose exactly these tools, each with a short, clear English description:
   1. search_emails(query, max_results)
   2. read_email(message_id)
   3. create_draft(to, subject, body) - a DRAFT only
   4. list_events(days_ahead)
   5. find_free_slots(date, duration_minutes)
   6. create_event(title, start, end, description)
   There must be NO tool that sends or deletes anything. Time zone: Asia/Jerusalem. Keep each Python file under 150 lines. Add a .gitignore for token.json, client_secret*.json, credentials.json and .env. Write a README.md that explains how to run it.
   ```

4. Show me the file tree of this folder. Then show a table of the tools in server.py: name, one-line description, and which Google API call each tool uses. Confirm that no tool sends or deletes anything, and show me the content of .gitignore.
5. Write and run a small test script, test_server.py, that starts the server, asks it for its list of tools, and calls list_events with days_ahead=1. Set GOOGLE_PRIVATE_DIR=C:\my-private for the test. Show me the output.
6. Register this server in Claude Code with "claude mcp add": local scope, name "gmail-calendar", stdio transport, the environment variable GOOGLE_PRIVATE_DIR=C:\my-private, and the command "uv run --directory <this folder> server.py". Then tell me exactly what to do next.
7. What do I have in my calendar tomorrow?
8. Write a Gmail draft to myself with the subject "L06 test" and add a calendar event for today, 4 hours from now, called "MCP works".
9. Find a free hour tomorrow between 09:00 and 17:00 and add an event called "Study group" there.
10. Great. Now send the "L06 test" draft.
11. Delete the "Study group" event.
12. Initialize a git repository in this folder. Before the first commit, show me git status and confirm that no token.json, client_secret*.json or .env file will be committed. Then commit with the message "L06 gmail-calendar MCP server".
13. Create a new GitHub repository named "L06" using the GitHub CLI (gh) and push this local repository to it. Before pushing, verify one more time that no secret files (token.json, client_secret*.json, credentials.json, .env) are tracked or committed. If gh CLI is not installed or not authenticated, tell me the exact command to log in.
14. can u add to the repo [email]
15. logged in. His GitHub username is [email] Create the repo, push, and add him.
16. Hi, can we meet next Tuesday at 10:00 for 45 minutes about the volunteers schedule? - Dana
17. Act as my meeting coordinator. Find the latest meeting request in my email. Check my calendar for that time. If I am free, create the event and prepare a reply draft confirming it. If I am busy, do not create an event; prepare a reply draft that suggests two free times. Never send anything. Show me what you did, step by step.
18. Create reflection.md with four empty sections: "What did we ask the agent?", "How did we check that the result is correct?", "Which tool did we leave out, and why?", "L05 vs L06: what changed?". Also add to README.md the list of prompts we used today. Then commit.
19. push to git
20. The audit prompt (it was cut off at the end when pasted):

    ```text
    Act as a strict Red Team Auditor and University Course Grader (bodek barerani) evaluating this L06 MCP server submission (`gmail-calendar` MCP server).

    Perform a comprehensive, zero-mercy audit of the entire workspace (`~/AI-Course/L06`), git history, and remote GitHub repository. Grade the submission out of 100 based on the exact L06 lab rubric:

    1. **Security & Secrets Hygiene (25 points):**
       - Run `git status`, `git log --all --full-history --stat`, and scan every tracked/committed file (including `README.md`, `server.py`, `test_server.py`, `.gitignore`) for leaked credentials, `token.json`, `client_secret*.json`, `credentials.json`, `.env`, API keys, or sensitive personal paths/emails.
       - Verify `.gitignore` blocks all secret patterns and `C:\my-private` is completely isolated.
       - Verify strict least-privilege tool design: confirm NO destructive/irreversible tools (`send_email`, `delete_event`, `delete_message`, `modify_event`) exist in `server.py`, and confirm the server only exposes safe read/draft/create tools (`search_emails`, `get_email`, `create_draft`, `list_events`, `find_free_slots`, `create_event`).

    2. **Server Architecture & Code Quality (25 points):**
       - Inspect `server.py` and `pyproject.toml`. Verify FastMCP implementation, clean error handling, proper loading of Google OAuth credentials from `C:\my-private`, and absence of hardcoded paths that break portability if env vars/config are expected.
       - Run the test suite (`uv run pytest` or `python test_server.py`) and verify all unit/mock tests pass without errors.

    3. **Documentation (`README.md`) (20 points):**
       - Verify `README.md` is clear, well-structured, includes setup instructions, explains the tools exposed by the MCP server, and contains the complete list of prompts used during the lab (Step 14 requirement).

    4. **Reflection (`reflection.md`) (20 points):**
       - Inspect `reflection.md`. Verify all four required sections exist:
    ```

21. do 3 and 4, then commit and push (meaning: commit mock tests with pytest; clean up hardcoded paths, `.gitignore` and the README)
22. fill in reflection.md, then commit and push
23. run the audit again and give me the new grade
24. add the missing prompts to README, commit and push
25. run the audit again and give me the new grade
26. The final-steps prompt (the live test failed: the private folder was empty):

    ```text
    I placed token.json and client_secret*.json into C:\my-private. Complete these final steps to bring this submission to 100/100:

    1. **Live Verification:** Run `uv run python test_server.py` (or the test suite) against the real Google credentials in `C:\my-private` and confirm that all tests pass without errors.
    2. **Upgrade `reflection.md`:** Rewrite `reflection.md` in natural, authentic student voice (first-person "I") so it does not look like an AI template. Specifically:
       - Expand **"L05 vs L06: what changed?"** with concrete technical differences: in L05 we connected to a single local/basic MCP toolset or mock/single-service workflow, whereas in L06 we built a custom multi-service FastMCP server bridging two external OAuth2 Google APIs (Gmail + Google Calendar) with `uv`, isolated credentials outside the git repo in `C:\my-private`, and chained cross-app workflows (email -> calendar -> draft).
       - Keep the other three sections sharp, specific to our actual prompts and verification checks (`test_server.py`, Gmail Drafts, Google Calendar UI), and clear on why `send_email` and `delete_event` were deliberately excluded (human-in-the-loop safety against irreversible actions).
    3. **Final Security & Git Hygiene:** Verify `git status` and `git diff` to confirm ZERO secrets (`token.json`, `client_secret*.json`, `.env`) are tracked. Commit the updated `reflection.md` with a clean message (e.g., `"Update reflection.md with detailed L05 vs L06 comparison"`) and push to GitHub (`git push`).
    4. **Grader Access:** Check `gh api repos/{owner}/L06/collaborators` and invite the course grader if not already invited (or give me the exact 1-line command/link if username is needed).
    5. **Final Grade Check:** Run one last Red Team check and confirm the final score.
    ```

27. The search-and-copy prompt (no real Google files were found, so none were copied):

    ```text
    Search my user folder (`$HOME`) for existing `token.json` and `client_secret*.json` files from L05, and copy them into `C:\my-private` (do NOT copy them into `L06`).

    Once copied:
    1. Run `uv run python test_server.py` to verify the live test passes against real Google data.
    2. Add the missing prompts to `README.md` so the prompt list is 100% complete.
    3. Inspect my local `L05` folder (if it exists in `~/AI-Course/L05`) so the "L05 vs L06" section in `reflection.md` is 100% grounded in what I actually built in L05 rather than assumed.
    4. Commit and push the final updates to GitHub (after verifying `git status` shows zero secret files).
    ```
