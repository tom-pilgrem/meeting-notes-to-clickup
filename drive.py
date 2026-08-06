"""Google Drive access: list meeting note docs in the watched folder and pull their text."""

from google.oauth2 import service_account
from googleapiclient.discovery import build

from config import GOOGLE_DRIVE_FOLDER_ID, GOOGLE_SERVICE_ACCOUNT_FILE

SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]


def _drive_service():
    credentials = service_account.Credentials.from_service_account_file(
        GOOGLE_SERVICE_ACCOUNT_FILE, scopes=SCOPES
    )
    return build("drive", "v3", credentials=credentials)


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
