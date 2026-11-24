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
