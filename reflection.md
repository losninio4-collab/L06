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

Both labs use Gmail and Calendar. What changed is how they are used.

- **Script or server:** L05 is one script, `main.py`. Each run creates a fixed test
  draft addressed to the signed-in account and a fixed 30-minute event 4 hours later,
  then exits. L06 is an MCP server over stdio that an agent can call when needed.
- **Who decides:** in L05 the subject, text and event title are written in the code.
  In L06 the agent chooses a tool and its inputs from the descriptions.
- **Reading:** L05 reads no mail or events (only the account address). L06 can also
  search and read email, list events and find free slots.
- **Sign-in:** L05 can open a browser (`run_local_server`) and saves `token.json`.
  L06 never opens a browser, never writes the token, and refreshes it in memory.
- **Private folder:** L05 has `C:\my-private` in the code. L06 reads the folder from
  `GOOGLE_PRIVATE_DIR`. Both keep the Google files outside the project.
- **Scopes:** the L05 script asks for `gmail.modify` and full `calendar`. If L06 reuses
  that token, it has more permission than my six tools need, so the limit is in my
  code and not in the token.
- **Time zone:** L05 uses the computer's zone. L06 always uses Asia/Jerusalem.
- **Tests:** the L05 folder has no tests. L06 has 13 mocked tests and a live test,
  which has not passed yet because the Google files were not in the private folder.
- **Combining apps:** L05 made a draft and an event that were not connected. In L06 I
  tried a chain from email to calendar to draft, using the connectors. It found no
  meeting request and stopped without creating anything, so the chain is not proven.
