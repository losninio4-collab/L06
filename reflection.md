# Reflection

## What did we ask the agent?

I asked Claude Code to build `gmail-calendar`, a Python MCP server using FastMCP,
uv and stdio. I fixed the limits in the prompt: exactly six tools, Google files read
from a folder named in `GOOGLE_PRIVATE_DIR`, no secrets copied or printed, no
browser, and nothing that sends or deletes.

After that I asked it to write `test_server.py`, register the server, push to a
private GitHub repository and audit the result. I also tried everyday requests:
tomorrow's calendar, an "L06 test" draft, a "Study group" event in a free hour, and
acting as my meeting coordinator. All the prompts are in `README.md`.

## How did we check that the result is correct?

- `test_server.py` starts the server as a real MCP client and compares the tool list
  with the six I asked for. That part passes.
- 13 pytest tests run with Google mocked. They check that a draft is never sent, an
  event has no guests, and overlapping events are merged when finding free time.
- Before each push, the tracked files were checked for secret filenames, and the
  audits searched the whole git history for secret formats.

The live `list_events` call in `test_server.py` failed because `token.json` was not
in the private folder, so I have not shown the server working with real Google data.
The draft and the calendar events were made through the claude.ai connectors. This
taught me that "Connected" and an event named "MCP works" are not proof: I have to
check which tool did the work.

## Which tool did we leave out, and why?

I left out `send_email` and `delete_event`. A sent email cannot be taken back and a
deleted event may be lost, so I want a human to make those decisions. The agent also
reads emails from other people, and an email could contain text that tries to give it
instructions. With drafts only, the worst result is a bad draft that I can throw away.

This protects only my server. When I asked Claude to send the draft and delete
"Study group", it did both through the claude.ai connectors. The token scopes are
also wider than my six tools. To really block these actions I would have to turn off
those connectors as well.

## L05 vs L06: what changed?

- **Services:** in L05 I worked with a basic, single-service workflow. In L06 the
  server covers two Google APIs, Gmail and Calendar, using one OAuth2 sign-in.
- **Who defines the tools:** in L06 I chose the tool names, inputs and descriptions
  myself, and any MCP client can discover them over stdio.
- **Secrets:** the client file and token are meant to stay in `C:\my-private`, outside
  the repository. The code gets the folder from an environment variable and refreshes
  the access token only in memory.
- **Running it:** uv manages Python and the packages, and `uv.lock` pins the versions.
- **Combining apps:** the goal was a chain from email to calendar to draft. When I
  tried it with the connectors, it found no meeting request, so it correctly stopped
  without creating an event or a draft. I have not completed the full chain yet.
