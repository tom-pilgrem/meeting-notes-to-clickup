"""Google Drive access: list meeting note docs in the watched folder and pull their text."""

import os

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from config import (
    GOOGLE_DRIVE_FOLDER_ID,
    GOOGLE_OAUTH_CLIENT_SECRETS_FILE,
    GOOGLE_OAUTH_TOKEN_FILE,
)

SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]


def _get_credentials() -> Credentials:
    creds = None
    if os.path.exists(GOOGLE_OAUTH_TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(GOOGLE_OAUTH_TOKEN_FILE, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                GOOGLE_OAUTH_CLIENT_SECRETS_FILE, SCOPES
            )
            creds = flow.run_local_server(port=0)
        with open(GOOGLE_OAUTH_TOKEN_FILE, "w", encoding="utf-8") as f:
            f.write(creds.to_json())

    return creds


def _drive_service():
    return build("drive", "v3", credentials=_get_credentials())


def list_docs(folder_id: str = GOOGLE_DRIVE_FOLDER_ID) -> list[dict]:
    """Return Google Docs in the folder as [{id, name, modifiedTime}, ...]."""
    service = _drive_service()
    query = (
        f"'{folder_id}' in parents "
        "and mimeType = 'application/vnd.google-apps.document' "
        "and trashed = false"
    )
    docs = []
    page_token = None
    while True:
        response = (
            service.files()
            .list(
                q=query,
                fields="nextPageToken, files(id, name, modifiedTime)",
                pageToken=page_token,
            )
            .execute()
        )
        docs.extend(response.get("files", []))
        page_token = response.get("nextPageToken")
        if not page_token:
            break
    return docs


def get_doc_text(doc_id: str) -> str:
    """Export a Google Doc's content as plain text."""
    service = _drive_service()
    content = service.files().export(fileId=doc_id, mimeType="text/plain").execute()
    return content.decode("utf-8") if isinstance(content, bytes) else content
