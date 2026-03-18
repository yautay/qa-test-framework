import os
from datetime import datetime, timezone

import requests
import urllib3
from requests.auth import HTTPBasicAuth

# =====================================================
# KONFIGURACJA (jak w innych skryptach tools/jira)
# =====================================================
jira_url = "https://jira.netcorner.pl"
USERNAME = "michal.pielaszkiewicz"  # login do JIRA
PASSWORD = "Tereska15@"  # hasło / token (zależy od instancji)
VERIFY = False  # lepiej: True lub ścieżka do CA.pem

# Numer zadania podajesz tutaj
ISSUE_KEY = "NN-23107"

# Treść komentarza (domyślnie z timestampem UTC)
COMMENT_TEXT = f"[API TEST] Komentarz testowy dodany {datetime.now(timezone.utc).isoformat()}"

# Opcjonalnie: ścieżka do obrazka/pliku do załączenia w issue
# Przykład: r"C:\repos\nc-functional-tests-py\screenshot.png"
ATTACHMENT_PATH = ""

# Czy usuwać komentarz po teście
DELETE_AFTER_TEST = True


def main() -> None:
    if VERIFY is False:
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    auth = HTTPBasicAuth(USERNAME, PASSWORD)
    session = requests.Session()

    issue_url = f"{jira_url.rstrip('/')}/rest/api/2/issue/{ISSUE_KEY}"
    issue_resp = session.get(
        issue_url,
        params={"fields": "summary"},
        auth=auth,
        verify=VERIFY,
        timeout=30,
    )
    issue_resp.raise_for_status()

    issue_summary = (issue_resp.json().get("fields") or {}).get("summary", "")
    print(f"OK: issue dostępne: {ISSUE_KEY} | {issue_summary}")

    comment_text = COMMENT_TEXT
    if ATTACHMENT_PATH:
        if not os.path.isfile(ATTACHMENT_PATH):
            raise RuntimeError(f"Plik nie istnieje: {ATTACHMENT_PATH}")

        attachments_url = f"{jira_url.rstrip('/')}/rest/api/2/issue/{ISSUE_KEY}/attachments"
        filename = os.path.basename(ATTACHMENT_PATH)
        with open(ATTACHMENT_PATH, "rb") as file_handle:
            upload_resp = session.post(
                attachments_url,
                files={"file": (filename, file_handle)},
                headers={"X-Atlassian-Token": "no-check"},
                auth=auth,
                verify=VERIFY,
                timeout=60,
            )

        if upload_resp.status_code not in {200, 201}:
            print(f"ERROR: nie udało się dodać załącznika. HTTP {upload_resp.status_code}")
            print(upload_resp.text)
            upload_resp.raise_for_status()

        uploaded = upload_resp.json() or []
        if uploaded:
            uploaded_name = uploaded[0].get("filename", filename)
        else:
            uploaded_name = filename
        print(f"OK: załącznik dodany: {uploaded_name}")

        comment_text = f"{COMMENT_TEXT}\n\nZałączony obrazek: !{uploaded_name}!"

    comment_url = f"{jira_url.rstrip('/')}/rest/api/2/issue/{ISSUE_KEY}/comment"
    create_resp = session.post(
        comment_url,
        json={"body": comment_text},
        auth=auth,
        verify=VERIFY,
        timeout=30,
    )

    if create_resp.status_code not in {200, 201}:
        print(f"ERROR: nie udało się dodać komentarza. HTTP {create_resp.status_code}")
        print(create_resp.text)
        create_resp.raise_for_status()

    created = create_resp.json()
    comment_id = str(created.get("id", ""))
    print(f"OK: komentarz dodany. comment_id={comment_id}")

    if DELETE_AFTER_TEST and comment_id:
        delete_url = f"{jira_url.rstrip('/')}/rest/api/2/issue/{ISSUE_KEY}/comment/{comment_id}"
        delete_resp = session.delete(
            delete_url,
            auth=auth,
            verify=VERIFY,
            timeout=30,
        )
        if delete_resp.status_code not in {200, 204}:
            print(f"WARN: komentarz dodany, ale nie usunięty. HTTP {delete_resp.status_code}")
            print(delete_resp.text)
        else:
            print("OK: testowy komentarz został usunięty.")


if __name__ == "__main__":
    main()
