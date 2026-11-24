# Reflection

## What did we ask the agent?

We asked Claude Code to build a Python MCP server, `gmail-calendar`, with FastMCP,
uv and stdio. It had to expose exactly six tools, reuse last week's Google client
and token from a private folder, never print or copy secrets, and have no tool
that sends or deletes. We then asked it to test and register the server, publish
it to a private GitHub repository, and audit the result.

We also asked for everyday tasks: reading tomorrow's calendar, writing a draft,
adding events and coordinating a meeting. The full list is in `README.md`.

## How did we check that the result is correct?

- A real MCP client (`test_server.py`) started the server and saw exactly six tools.
- 13 unit tests pass with Google mocked. They check, for example, that a draft is
  never sent, events have no guests, and errors do not reveal details.
- We searched the code for send, delete and modify calls and found none.
- We checked tracked files and git history for secret files and known secret
  formats before pushing, and compared the local and GitHub commits.

**What we did not prove:** the private folder was empty, so the live `list_events`
call failed (`token.json was not found`) and the server never ran against real
Google data. The Gmail and Calendar tasks in the session ran through the claude.ai
connectors instead. The "MCP works" event therefore does not show that our server
works. Claude Code's "Connected" status only showed that the server starts.

## Which tool did we leave out, and why?

We left out sending email and deleting emails or events. Sending cannot be taken
back, and a delete can lose data. The agent also reads email written by other
people, which could contain malicious instructions. A draft lets a person check
the text before anything leaves the account.

We learned that this protects only our server. In the same session, the claude.ai
connectors sent the "L06 test" email and deleted the "Study group" event when we
asked. The token scopes also allow more than our tools do. Real protection means
limiting the other connected tools and the permissions too.

## L05 vs L06: what changed?

From L05 we reused the Google client and `token.json` sign-in, by design.
In L06 we put Gmail and Calendar behind an MCP server: named tools with
descriptions that an MCP client can discover and call, instead of code tied to one
program. The server also sets the boundary: it holds the credentials, exposes six
chosen actions, and hides secrets and raw Google errors from the agent.

The new lesson was to check which tool actually did the work, because several
connected tools can give the same answer.
