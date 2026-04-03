import math
import os
import re

import matplotlib.pyplot as plt
import pandas as pd

# =====================================================
# KONFIG
# =====================================================
EXCEL_PATH = r"C:\repos\nc-functional-tests-py\perf.xlsx"
SHEET_NAME = 0

OUT_DIR = r"C:\repos\nc-functional-tests-py\mpl_out"
os.makedirs(OUT_DIR, exist_ok=True)

# =====================================================
# PARAMETRY WYKRESÓW / ANALIZY
# =====================================================

TOP_ISSUES_BAR = 10  # ile zadań (NN-xxxx) na wykresach
TOP_PEOPLE_BAR = 10  # ile osób na wykresach obciążenia
HEATMAP_TOP_PEOPLE = 12  # ile osób w heatmapie
HEATMAP_TOP_ISSUES = 8  # ile zadań w heatmapie


# Excel ma wiersze 1-based.
# Interesują Cię osoby do wiersza 38 włącznie:
PEOPLE_END_ROW_EXCEL = 38

# Na screenie osoby zaczynają się w okolicach wiersza 6 (Adam).
# Jeśli u Ciebie jest inaczej, zmień to na właściwy numer wiersza.
PEOPLE_START_ROW_EXCEL = 6

# Kolumna z nazwiskami: B = index 1 (0-based)
NAME_COL_IDX = 1

# Wiersz z markerami u1..u17: "pierwszy wiersz" = 1 (Excel) => idx 0 (pandas)
MARKER_ROW_EXCEL = 1

# =====================================================
# ROLE MAPPING (opcjonalne – do metryk wg ról)
# =====================================================
ROLE_BY_NAME = {
    # Dev
    "Adam Sobociński": "Dev",
    "Sergii Khrystenko": "Dev",
    "Andrii Khrystenko": "Dev",
    "Marcin Hędrzak": "Dev",
    "Filip Kotliński": "Dev",
    "Franciszek Andruszkiewicz": "Dev",
    "Paweł Kłopotek-Główczewski": "Dev",
    "Dawid Hirsz": "Dev",
    "Maciej Kieruzal": "Dev",
    "Rafał Strachowski": "Dev",
    "Oleh Tsapok": "Dev",
    "Piotr Jędrzejak": "Dev",
    "Łukasz Kitajczuk": "Dev",
    # Test
    "Michał Pielaszkiewicz": "Test",
    "Karolina Krajewska": "Test",
    "Marek Wleklik": "Test",
    "Mariola Szczurek": "Test",
    "Agnieszka Jezierska": "Test",
    "Bogna Konstanty": "Test",
    "Weronika Truscelli": "Test",
    "Bartosz Michalak": "Test",
    # PM
    "Maciej Walczak": "PM",
    "Tomasz Bolt": "PM",
    "Anna Liszka": "PM",
    "Aneta Mętel": "PM",
    # DevOps
    "Rafał Bisingier": "DevOps",
    "Wojciech Iwanik": "DevOps",
    "Marcin Pietrzak": "DevOps",
}

FAIL_FAST_ROLE_MAP = False  # możesz ustawić False, jeśli chcesz bez fail-fast

# =====================================================
# POMOCNICZE
# =====================================================
U_RE = re.compile(r"^u\d+$", re.IGNORECASE)
NN_RE = re.compile(r"^NN-\d+$", re.IGNORECASE)


def to_number_cell(x) -> float:
    """Konwersja komórki do float (obsługuje 0,25 i 0.25)."""
    if pd.isna(x):
        return 0.0
    if isinstance(x, (int, float)):
        try:
            if math.isnan(float(x)):
                return 0.0
        except Exception:
            return 0.0
        return float(x)
    s = str(x).strip()
    if not s:
        return 0.0
    s = s.replace("\u00a0", "").replace(" ", "").replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return 0.0


def find_u_marker_columns(raw: pd.DataFrame, marker_row_idx0: int):
    """Zwraca listę (col_idx, u_marker) dla kolumn oznaczonych u1..uN w danym wierszu."""
    out = []
    for c in range(raw.shape[1]):
        v = raw.iat[marker_row_idx0, c]
        if pd.isna(v):
            continue
        s = str(v).strip()
        if U_RE.match(s):
            out.append((c, s.lower()))
    if not out:
        raise RuntimeError("Nie znaleziono markerów u1..uN w pierwszym wierszu.")
    # sortuj po numerze u
    out.sort(key=lambda t: int(t[1][1:]))
    return out


def detect_nn_header_row(raw: pd.DataFrame, u_cols):
    """
    Znajdź wiersz, w którym w kolumnach u* pojawiają się nagłówki NN-xxxxx.
    Skuteczniejsze niż szukanie po całym arkuszu.
    """
    best_row, best_count = None, -1
    for r in range(min(len(raw), 200)):  # nagłówki są w górze
        cnt = 0
        for c, _u in u_cols:
            v = raw.iat[r, c]
            if pd.isna(v):
                continue
            if NN_RE.match(str(v).strip()):
                cnt += 1
        if cnt > best_count:
            best_count = cnt
            best_row = r
    if best_row is None or best_count <= 0:
        raise RuntimeError("Nie udało się znaleźć wiersza z nagłówkami NN-xxxxx w kolumnach u*.")
    return best_row


def get_issue_map(raw: pd.DataFrame, nn_header_row_idx0: int, u_cols):
    """Mapuje u1..uN -> IssueKey z wiersza nagłówków."""
    m = {}
    for c, u in u_cols:
        v = raw.iat[nn_header_row_idx0, c]
        key = str(v).strip() if not pd.isna(v) else ""
        # if not NN_RE.match(key):
        #     raise RuntimeError(
        #         f"W kolumnie {u} nie ma NN-xxxxx w wierszu nagłówków "
        #         f"(row idx {nn_header_row_idx0}). Wartość: {v}"
        #     )
        m[u] = key
    return m


# =====================================================
# 1) WCZYTANIE
# =====================================================
raw = pd.read_excel(EXCEL_PATH, sheet_name=SHEET_NAME, header=None, engine="openpyxl")

marker_row_idx0 = MARKER_ROW_EXCEL - 1
u_cols = find_u_marker_columns(raw, marker_row_idx0)

nn_header_row_idx0 = detect_nn_header_row(raw, u_cols)
u_to_issue = get_issue_map(raw, nn_header_row_idx0, u_cols)

# =====================================================
# 2) WYCIĘCIE ZAKRESU OSÓB (wiersze) + KOLUMN U*
# =====================================================
start_idx0 = PEOPLE_START_ROW_EXCEL - 1
end_idx0_inclusive = PEOPLE_END_ROW_EXCEL - 1

rows_block = raw.iloc[start_idx0 : end_idx0_inclusive + 1, [NAME_COL_IDX] + [c for c, _ in u_cols]].copy()
rows_block.columns = ["Name"] + [u for _, u in u_cols]

rows_block["Name"] = rows_block["Name"].astype(str).str.strip()
rows_block = rows_block[rows_block["Name"].notna() & (rows_block["Name"] != "")]

# Konwersja godzin
for u in [u for _, u in u_cols]:
    rows_block[u] = rows_block[u].apply(to_number_cell)

# =====================================================
# 3) FAIL-FAST roli (opcjonalne)
# =====================================================
people_names = rows_block["Name"].unique().tolist()
missing_roles = sorted([n for n in people_names if n not in ROLE_BY_NAME])

if FAIL_FAST_ROLE_MAP and missing_roles:
    raise RuntimeError(
        "[FAIL FAST] Brakuje mapowania roli dla:\n- "
        + "\n- ".join(missing_roles)
        + "\n\nDopisz do ROLE_BY_NAME albo ustaw FAIL_FAST_ROLE_MAP=False."
    )

# =====================================================
# 4) LONG FORMAT: Name, Issue, Hours
# =====================================================
long_df = rows_block.melt(id_vars="Name", var_name="u", value_name="Hours")
long_df["Issue"] = long_df["u"].map(u_to_issue)
long_df["Role"] = long_df["Name"].map(ROLE_BY_NAME)
long_df = long_df.drop(columns=["u"])

# =====================================================
# 5) METRYKI
# =====================================================
issue_totals = long_df.groupby("Issue", as_index=False)["Hours"].sum().sort_values("Hours", ascending=False)

person_totals = long_df.groupby(["Name", "Role"], as_index=False)["Hours"].sum().sort_values("Hours", ascending=False)

context_switch = (
    long_df[long_df["Hours"] > 0]
    .groupby(["Name", "Role"], as_index=False)["Issue"]
    .nunique()
    .rename(columns={"Issue": "Issues_touched"})
    .sort_values("Issues_touched", ascending=False)
)

role_issue = long_df.groupby(["Issue", "Role"], as_index=False)["Hours"].sum()
role_tot = role_issue.groupby("Issue", as_index=False)["Hours"].sum().rename(columns={"Hours": "IssueHours"})
role_issue = role_issue.merge(role_tot, on="Issue", how="left")
role_issue["Share"] = role_issue.apply(lambda r: (r["Hours"] / r["IssueHours"]) if r["IssueHours"] else 0.0, axis=1)

tmp = long_df.groupby(["Issue", "Name"], as_index=False)["Hours"].sum()
tmp = tmp[tmp["Hours"] > 0]


def topk_share(g: pd.DataFrame, k: int) -> float:
    total = g["Hours"].sum()
    if total <= 0:
        return 0.0
    return float(g.sort_values("Hours", ascending=False).head(k)["Hours"].sum() / total)


bus_rows = []
for issue, g in tmp.groupby("Issue"):
    bus_rows.append(
        {
            "Issue": issue,
            "Top1_share": topk_share(g, 1),
            "Top3_share": topk_share(g, 3),
            "Contributors": int(g.shape[0]),
            "IssueHours": float(g["Hours"].sum()),
        }
    )
bus_factor = pd.DataFrame(bus_rows).sort_values("IssueHours", ascending=False)

variability = pd.DataFrame(
    [
        {
            "Issues_count": int(issue_totals.shape[0]),
            "Total_hours": float(issue_totals["Hours"].sum()),
            "Mean_hours_per_issue": float(issue_totals["Hours"].mean()) if not issue_totals.empty else 0.0,
            "Median_hours_per_issue": float(issue_totals["Hours"].median()) if not issue_totals.empty else 0.0,
            "Std_hours_per_issue": float(issue_totals["Hours"].std(ddof=0)) if issue_totals.shape[0] > 0 else 0.0,
            "P90_hours_per_issue": float(issue_totals["Hours"].quantile(0.90)) if issue_totals.shape[0] > 0 else 0.0,
        }
    ]
)

# =====================================================
# 6) ZAPIS CSV
# =====================================================
rows_block.to_csv(os.path.join(OUT_DIR, "extracted_wide_u_cols.csv"), index=False, encoding="utf-8")
long_df.to_csv(os.path.join(OUT_DIR, "tidy_long.csv"), index=False, encoding="utf-8")
issue_totals.to_csv(os.path.join(OUT_DIR, "metrics_issue_totals.csv"), index=False, encoding="utf-8")
person_totals.to_csv(os.path.join(OUT_DIR, "metrics_person_totals.csv"), index=False, encoding="utf-8")
context_switch.to_csv(os.path.join(OUT_DIR, "metrics_context_switching.csv"), index=False, encoding="utf-8")
role_issue.to_csv(os.path.join(OUT_DIR, "metrics_role_split.csv"), index=False, encoding="utf-8")
bus_factor.to_csv(os.path.join(OUT_DIR, "metrics_bus_factor.csv"), index=False, encoding="utf-8")
variability.to_csv(os.path.join(OUT_DIR, "metrics_variability.csv"), index=False, encoding="utf-8")

# =====================================================
# 7) WYKRESY (matplotlib)
# =====================================================
# 7.1 Top issues by hours
top_issues = issue_totals.head(TOP_ISSUES_BAR).sort_values("Hours", ascending=True)
plt.figure()
plt.barh(top_issues["Issue"], top_issues["Hours"])
plt.title(f"Top {TOP_ISSUES_BAR} issues by total hours")
plt.xlabel("Hours")
plt.ylabel("Issue")
plt.tight_layout()
plt.savefig(os.path.join(OUT_DIR, "chart_top_issues.png"), dpi=160)
plt.close()

# 7.2 Role split stacked bar (top 10 issues)
top_issue_keys = issue_totals.head(min(10, len(issue_totals)))["Issue"].tolist()
role_pivot = role_issue[role_issue["Issue"].isin(top_issue_keys)].pivot_table(
    index="Issue", columns="Role", values="Hours", aggfunc="sum", fill_value=0.0
)
role_pivot = role_pivot.reindex(top_issue_keys)

plt.figure()
bottom = None
for role in role_pivot.columns:
    vals = role_pivot[role].values
    if bottom is None:
        plt.bar(role_pivot.index, vals, label=role)
        bottom = vals
    else:
        plt.bar(role_pivot.index, vals, bottom=bottom, label=role)
        bottom = bottom + vals

plt.title("Role split (hours) for top issues")
plt.xlabel("Issue")
plt.ylabel("Hours")
plt.xticks(rotation=45, ha="right")
plt.legend()
plt.tight_layout()
plt.savefig(os.path.join(OUT_DIR, "chart_role_split_stacked.png"), dpi=160)
plt.close()

# 7.3 Load per person (top N)
top_people = person_totals.head(TOP_PEOPLE_BAR).sort_values("Hours", ascending=True)
plt.figure()
plt.barh(top_people["Name"], top_people["Hours"])
plt.title(f"Top {TOP_PEOPLE_BAR} people by total hours (load)")
plt.xlabel("Hours")
plt.ylabel("Person")
plt.tight_layout()
plt.savefig(os.path.join(OUT_DIR, "chart_load_per_person.png"), dpi=160)
plt.close()

# 7.4 Context switching (top N)
top_ctx = context_switch.head(TOP_PEOPLE_BAR).sort_values("Issues_touched", ascending=True)
plt.figure()
plt.barh(top_ctx["Name"], top_ctx["Issues_touched"])
plt.title(f"Top {TOP_PEOPLE_BAR} people by issues touched (context switching)")
plt.xlabel("Issues touched")
plt.ylabel("Person")
plt.tight_layout()
plt.savefig(os.path.join(OUT_DIR, "chart_context_switching.png"), dpi=160)
plt.close()

# 7.5 Heatmap person x issue (top subset)
heat_people = person_totals.head(HEATMAP_TOP_PEOPLE)["Name"].tolist()
heat_issues = issue_totals.head(HEATMAP_TOP_ISSUES)["Issue"].tolist()

heat = (
    long_df[long_df["Name"].isin(heat_people) & long_df["Issue"].isin(heat_issues)]
    .groupby(["Name", "Issue"], as_index=False)["Hours"]
    .sum()
    .pivot(index="Name", columns="Issue", values="Hours")
    .fillna(0.0)
)

heat = heat.loc[heat.sum(axis=1).sort_values(ascending=False).index]
heat = heat[heat_issues]

plt.figure()
plt.imshow(heat.values, aspect="auto")
plt.title("Heatmap: hours by person and issue (top subset)")
plt.xlabel("Issue")
plt.ylabel("Person")
plt.xticks(range(len(heat.columns)), heat.columns, rotation=45, ha="right")
plt.yticks(range(len(heat.index)), heat.index)
plt.tight_layout()
plt.savefig(os.path.join(OUT_DIR, "chart_heatmap.png"), dpi=160)
plt.close()

# 7.6 Boxplot: distribution of hours per issue
plt.figure()
plt.boxplot(issue_totals["Hours"].values, vert=True, labels=["Issues"])
plt.title("Distribution of total hours per issue (variability)")
plt.ylabel("Hours")
plt.tight_layout()
plt.savefig(os.path.join(OUT_DIR, "chart_boxplot_issue_hours.png"), dpi=160)
plt.close()

# =====================================================
# 8) DIAGNOSTYKA
# =====================================================
print("OK — wczytano po markerach u*, policzono metryki i zapisano wykresy.")
print(f"OUT_DIR: {OUT_DIR}")
print(f"Marker row (idx0): {marker_row_idx0}")
print(f"NN header row (idx0): {nn_header_row_idx0}")
print(f"Name col idx0: {NAME_COL_IDX}")
print(f"People rows Excel: {PEOPLE_START_ROW_EXCEL}..{PEOPLE_END_ROW_EXCEL}")
print("u->Issue map:", u_to_issue)
