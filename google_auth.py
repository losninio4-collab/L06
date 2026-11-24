"""Load the existing Google token. Never opens a browser, never writes files."""

import functools
import json
import os
from pathlib import Path

from google.auth.exceptions import GoogleAuthError, TransportError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

ENV_VAR = "GOOGLE_PRIVATE_DIR"


class GoogleSetupError(RuntimeError):
    """A setup problem, described without any secret values."""


def _read_json(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        # "from None": the original error could quote file contents.
        raise GoogleSetupError(f"Could not read {path.name} as JSON.") from None
    if not isinstance(data, dict):
        raise GoogleSetupError(f"{path.name} has an unexpected format.")
    return data


def _private_dir() -> Path:
    value = os.environ.get(ENV_VAR, "").strip()
    if not value:
        raise GoogleSetupError(f"Environment variable {ENV_VAR} is not set.")
    folder = Path(value)
    if not folder.is_dir():
        raise GoogleSetupError(f"The folder in {ENV_VAR} does not exist.")
    return folder


def _client_info(folder: Path) -> dict:
    files = sorted(folder.glob("client_secret*.json"))
    if len(files) != 1:
        raise GoogleSetupError(
            f"Expected one client_secret*.json in {ENV_VAR}, found {len(files)}."
        )
    data = _read_json(files[0])
    client = data.get("installed") or data.get("web")
    if not isinstance(client, dict):
        raise GoogleSetupError("client_secret*.json has an unexpected format.")
    return client


def load_credentials() -> Credentials:
    """Read token.json, refreshing the access token in memory if needed."""
    folder = _private_dir()
    token_path = folder / "token.json"
    if not token_path.is_file():
        raise GoogleSetupError(f"token.json was not found in {ENV_VAR}.")
    info = _read_json(token_path)
    client = _client_info(folder)
    for key in ("client_id", "client_secret"):
        info.setdefault(key, client.get(key))
    try:
        creds = Credentials.from_authorized_user_info(info)
    except (ValueError, TypeError, AttributeError):
        raise GoogleSetupError(
            "token.json is incomplete. Create it again outside this server."
        ) from None
    if not creds.valid:
        creds.refresh(Request())
    return creds


def gmail_service():
    return build("gmail", "v1", credentials=load_credentials())


def calendar_service():
    return build("calendar", "v3", credentials=load_credentials())


def safe_errors(func):
    """Turn Google errors into short messages that contain no secrets."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except HttpError as error:
            status = error.resp.status
            hint = " Check the token's scopes and enabled APIs." if status == 403 else ""
            raise RuntimeError(f"Google API error (HTTP {status}).{hint}") from None
        except TransportError:
            raise RuntimeError("Could not reach Google. Check the network.") from None
        except GoogleAuthError:
            raise RuntimeError(
                "Google sign-in expired or was revoked. "
                "Create token.json again outside this server."
            ) from None

    return wrapper
