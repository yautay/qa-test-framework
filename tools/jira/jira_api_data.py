import re
import urllib3
import requests
from requests.auth import HTTPBasicAuth
import pandas as pd

# =====================================================
# KONFIGURACJA API
# =====================================================
jira_url = "https://jira.netcorner.pl"
USERNAME = "michal.pielaszkiewicz"  # login do JIRA
PASSWORD = "Tereska15@"  # hasło / token (zależy od instancji)
VERIFY = False  # lepiej: ścieżka do CA.pem

# Opcja 1: podaj JQL wprost (jak w UI)
# JQL = 'issuekey = NN-23020 OR parent = NN-23020'

# Opcja 2: albo podaj listę parentów i zbuduj JQL automatycznie
main_issues = ["NN-23107"]
JQL = " OR ".join([f'issuekey = {k} OR parent = {k}' for k in main_issues])

MAX_RESULTS = 100  # paginacja search

# =====================================================
# ŚCIEŻKI WYJŚCIA
# =====================================================
OUT_BY_ISSUE = r"C:\repos\nc-functional-tests-py\worklog_summary.csv"
OUT_BY_USER = r"C:\repos\nc-functional-tests-py\worklog_total_per_user.csv"
OUT_BY_GROUP = r"C:\repos\nc-functional-tests-py\worklog_total_per_group.csv"
OUT_CUSTOM = r"C:\repos\nc-functional-tests-py\worklog_custom_structure.csv"
OUT_SUBTASK_COUNT = r"C:\repos\nc-functional-tests-py\worklog_subtask_count.csv"


# =====================================================
# MAPOWANIA / STRUKTURA
# =====================================================
USER_GROUPS = {
    # PM
    "anna.liszka": "pm",
    "maciej.walczak": "pm",
    "tomasz.bolt": "pm",

    # TESTERS
    "michal.pielaszkiewicz": "testers",
    "marek.wleklik": "testers",
    "agnieszka.jezierska": "testers",
    "bogna.konstanty": "testers",
    "weronika.bakowska": "testers",
    "mariola.szczurek": "testers",
}

CUSTOM_STRUCTURE = [
    # DEV
    ("adam.sobocinski", "Adam Sobociński", "Dev"),
    ("sergii.khrystenko", "Sergii Khrystenko", "Dev"),
    ("andrii.khrystenko", "Andrii Khrystenko", "Dev"),
    ("marcin.hedrzak", "Marcin Hędrzak", "Dev"),
    ("filip.kotlinski", "Filip Kotliński", "Dev"),
    ("franciszek.andruszkiewicz", "Franciszek Andruszkiewicz", "Dev"),
    ("pawel.klopotek", "Paweł Kłopotek-Główczewski", "Dev"),
    ("dawid.hirsz", "Dawid Hirsz", "Dev"),
    ("maciej.kieruzal", "Maciej Kieruzal", "Dev"),
    ("rafal.strachowski", "Rafał Strachowski", "Dev"),
    ("oleh.tsapok", "Oleh Tsapok", "Dev"),
    ("piotr.jedrzejak", "Piotr Jędrzejak", "Dev"),
    ("lukasz.kitajczuk", "Łukasz Kitajczuk", "Dev"),
    ("__DEV__", "Dev Total", "Dev"),

    # TEST
    ("michal.pielaszkiewicz", "Michał Pielaszkiewicz", "Test"),
    ("karolina.krajewska", "Karolina Krajewska", "Test"),
    ("marek.wleklik", "Marek Wleklik", "Test"),
    ("mariola.szczurek", "Mariola Szczurek", "Test"),
    ("agnieszka.jezierska", "Agnieszka Jezierska", "Test"),
    ("bogna.konstanty", "Bogna Konstanty", "Test"),
    # UWAGA: poniżej celowo mapujesz login -> wyświetlana nazwa
    ("weronika.bakowska", "Weronika Truscelli", "Test"),
    ("bartosz.michalak", "Bartosz Michalak", "Test"),
    ("__TEST__", "Test Total", "Test"),

    # PM
    ("maciej.walczak", "Maciej Walczak", "PM"),
    ("tomasz.bolt", "Tomasz Bolt", "PM"),
    ("anna.liszka", "Anna Liszka", "PM"),
    ("aneta.metel", "Anna Metel", "PM"),
    ("__PM__", "PM Total", "PM"),

    # DEVOPS
    ("rafal.bisingier", "Rafał Bisingier", "DevOps"),
    ("wojciech.iwanik", "Wojciech Iwanik", "DevOps"),
    ("marcin.pietrzak", "Marcin Pietrzak", "DevOps"),
    ("__DEVOPS__", "DevOps Total", "DevOps"),
]

# =====================================================
# TLS warnings (jeśli VERIFY=False)
# =====================================================
if not VERIFY:
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

AUTH = HTTPBasicAuth(USERNAME, PASSWORD)


# =====================================================
# FORMAT CZASU
# =====================================================
def format_duration(hours: float) -> str:
    total_minutes = int(round(hours * 60))
    minutes = total_minutes % 60
    total_hours = total_minutes // 60

    h = total_hours % 8
    total_days = total_hours // 8

    d = total_days % 5
    w = total_days // 5

    parts = []
    if w: parts.append(f"{w}w")
    if d: parts.append(f"{d}d")
    if h: parts.append(f"{h}h")
    if minutes: parts.append(f"{minutes}m")

    return " ".join(parts) if parts else "0m"


# =====================================================
# API helper
# =====================================================
def jira_get(path: str, params=None):
    url = f"{jira_url}{path}"
    r = requests.get(url, auth=AUTH, params=params, verify=VERIFY, timeout=60)
    r.raise_for_status()
    return r.json()


def search_issues(jql: str):
    start_at = 0
    issues = []
    while True:
        data = jira_get(
            "/rest/api/2/search",
            params={
                "jql": jql,
                "startAt": start_at,
                "maxResults": MAX_RESULTS,
                "fields": "summary"
            }
        )
        issues.extend(data.get("issues", []))
        start_at += data.get("maxResults", 0)
        if start_at >= data.get("total", 0):
            break
    return issues


def get_all_worklogs(issue_key: str):
    start_at = 0
    max_results = 1000
    worklogs = []
    while True:
        data = jira_get(
            f"/rest/api/2/issue/{issue_key}/worklog",
            params={"startAt": start_at, "maxResults": max_results}
        )
        worklogs.extend(data.get("worklogs", []))
        start_at += data.get("maxResults", 0)
        if start_at >= data.get("total", 0):
            break
    return worklogs


def extract_login(author: dict) -> str:
    """
    Data Center/Server bywa różne: 'name' lub 'key' (login), czasem tylko displayName.
    FAIL-FAST: jeśli nie ma loginu, przerywamy (bo mapowanie i agregacje mają być deterministyczne).
    """
    login = author.get("name") or author.get("key")
    return (login or "").strip()


def get_issue_subtasks(issue_key: str):
    data = jira_get(f"/rest/api/2/issue/{issue_key}", params={"fields": "summary,subtasks"})
    fields = data.get("fields", {}) or {}
    summary = fields.get("summary", "")
    subtasks = fields.get("subtasks", []) or []
    return summary, subtasks



# =====================================================
# 1) Pobierz issue listę z JQL (jak w UI)
# =====================================================
issues = search_issues(JQL)

# =====================================================
# 2) Pobierz worklogi i zbuduj tabelę jak wcześniej z CSV
# =====================================================
rows = []
for it in issues:
    key = it.get("key")
    summary = (it.get("fields") or {}).get("summary", "")

    if not key:
        continue

    for wl in get_all_worklogs(key):
        author = wl.get("author") or {}
        login = extract_login(author)
        if not login:
            raise RuntimeError(
                f"[FAIL FAST] Nie udało się ustalić loginu autora worklog (issue={key}). "
                f"Author keys: {list(author.keys())}"
            )

        seconds = int(wl.get("timeSpentSeconds", 0))
        rows.append({
            "Issue key": key,
            "Summary": summary,
            "User": login,
            "Group": USER_GROUPS.get(login, "dev"),
            "Hours": seconds / 3600.0
        })

parsed = pd.DataFrame(rows)

# Jeżeli JQL nie zwróciło worklogów, nie ma co agregować
if parsed.empty:
    raise RuntimeError("[FAIL FAST] Brak worklogów do przetworzenia (parsed jest puste).")

# =====================================================
# FAIL-FAST — WALIDACJA MAPOWANIA LOGINÓW (tak jak wcześniej)
# =====================================================
jira_users = set(parsed["User"].unique())
mapped_users = {u for u, _, _ in CUSTOM_STRUCTURE if not u.startswith("__")}

unmapped = sorted(jira_users - mapped_users)
if unmapped:
    raise RuntimeError(f"[FAIL FAST] Brak mapowania dla loginów Jira: {unmapped}")

# =====================================================
# 1. ISSUE × USER
# =====================================================
by_issue = (
    parsed
    .groupby(["Issue key", "Summary", "User"], as_index=False)["Hours"]
    .sum()
)
by_issue["Hours"] = by_issue["Hours"].round(2)
by_issue.to_csv(OUT_BY_ISSUE, sep=",", index=False, encoding="utf-8")

# =====================================================
# 2. TOTAL PER USER
# =====================================================
by_user = (
    parsed
    .groupby("User", as_index=False)["Hours"]
    .sum()
)
by_user["Hours"] = by_user["Hours"].round(2)
by_user["Total"] = by_user["Hours"].apply(format_duration)
by_user = by_user.sort_values("Hours", ascending=False)
by_user.to_csv(OUT_BY_USER, sep=",", index=False, encoding="utf-8")

# =====================================================
# 3. TOTAL PER GROUP + ALL
# =====================================================
by_group = (
    parsed
    .groupby("Group", as_index=False)["Hours"]
    .sum()
)
by_group["Hours"] = by_group["Hours"].round(2)
by_group["Total"] = by_group["Hours"].apply(format_duration)

all_hours = round(float(parsed["Hours"].sum()), 2)
by_group = pd.concat([
    by_group,
    pd.DataFrame([{
        "Group": "ALL",
        "Hours": all_hours,
        "Total": format_duration(all_hours)
    }])
], ignore_index=True)

by_group.to_csv(OUT_BY_GROUP, sep=",", index=False, encoding="utf-8")

# =====================================================
# 4. CUSTOM STRUCTURE EXPORT
#    - Total puste dla wszystkich poza TOTAL ALL
# =====================================================
user_hours = by_user.set_index("User")["Hours"].to_dict()

rows_custom = []
for login, name, group in CUSTOM_STRUCTURE:
    if login.startswith("__"):
        subtotal = sum(
            r["Hours"] for r in rows_custom if r["Group"] == group and not r["IsTotal"]
        )
        rows_custom.append({
            "Name": name,
            "Hours": round(subtotal, 2),
            "Group": group,
            "IsTotal": True
        })
    else:
        h = float(user_hours.get(login, 0.0))
        rows_custom.append({
            "Name": name,
            "Hours": round(h, 2),
            "Group": group,
            "IsTotal": False
        })

# TOTAL ALL jako ostatni wiersz (z całości)
rows_custom.append({
    "Name": "TOTAL ALL",
    "Hours": all_hours,
    "TotalWDHM": format_duration(all_hours),
    "Group": "ALL",
    "IsTotal": True
})

custom_df = pd.DataFrame(rows_custom)
custom_df["Total"] = ""
custom_df.loc[custom_df["Name"] == "TOTAL ALL", "Total"] = custom_df.loc[
    custom_df["Name"] == "TOTAL ALL", "TotalWDHM"
].astype(str)

custom_df = custom_df[["Name", "Hours", "Total"]]
custom_df.to_csv(OUT_CUSTOM, sep=",", index=False, encoding="utf-8")

print("OK — wszystkie raporty z API wygenerowane poprawnie.")
print(f"- {OUT_BY_ISSUE}")
print(f"- {OUT_BY_USER}")
print(f"- {OUT_BY_GROUP}")
print(f"- {OUT_CUSTOM}")

# =====================================================
# DODATKOWY EKSPORT: liczba sub-tasków per zadanie główne
# =====================================================
subtask_rows = []
for parent_key in main_issues:
    summary, subtasks = get_issue_subtasks(parent_key)
    subtask_rows.append({
        "Parent key": parent_key,
        "Parent summary": summary,
        "Subtasks count": len(subtasks)
    })

pd.DataFrame(subtask_rows).to_csv(OUT_SUBTASK_COUNT, sep=",", index=False, encoding="utf-8")
print(f"- {OUT_SUBTASK_COUNT}")