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
$env:GOOGLE_PRIVATE_DIR = "C:\my-private"
uv run server.py
```

The server waits silently for an MCP client. Press Ctrl+C to stop.

## Add to Claude Code

```powershell
claude mcp add gmail-calendar --scope local --transport stdio --env GOOGLE_PRIVATE_DIR=C:\my-private '--' uv run --directory C:\Users\Elnin\AI-Course\L06 server.py
```

## Security

- Secrets stay in the private folder; they are never copied, changed or printed.
- Access tokens are refreshed in memory only.
- The server never opens a browser. If the token expires or is revoked,
  create `token.json` again with last week's sign-in script.

## Prompts used (2026-11-24)

Prompts are quoted as written, except that a third party's email address is
replaced with `[email]`. The Gmail and Calendar work in prompts 7-11, 16 and 17
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
