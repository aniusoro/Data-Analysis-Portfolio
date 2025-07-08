import pandas as pd
import re

FILE = "/Users/anietieakpanusoh/Desktop/Research/recreationdata.xlsx"
SHEET = "20230808 Client Data"                                  # worksheet name


# 1.  Peek at header only, so we know exact column names
cols_all = pd.read_excel(FILE, SHEET, nrows=0).columns.tolist()

# -- columns that hold region / demo / weights
REGION_COL   = "regions -- Regions"
AGE_COL      = "q8 -- Age"                 # adjust if the age question label is different
GENDER_COL = "q7 -- Gender"
EDU_COL = "q9 -- Education"
INCOME_COL = "q14 -- What is the total amount of income before taxes that your household received during the past 12 months?"

WEIGHT_COL    = None

# 2.  Identify barrier columns      (still the q4c1_ prefix)
cols_all      = pd.read_excel(FILE, SHEET, nrows=0).columns
BARRIER_COLS  = [c for c in cols_all if c.startswith("q4c1_")]

# Put everything we want in one list
keep_cols = [REGION_COL, AGE_COL, GENDER_COL, EDU_COL, INCOME_COL] + BARRIER_COLS
if WEIGHT_COL:
    keep_cols.insert(0, WEIGHT_COL)

# 3.  Read only those columns  (this keeps memory down)
df = pd.read_excel(FILE, SHEET, usecols=keep_cols)



# Region → drop numeric code
df["region"] = (df[REGION_COL]
                .astype(str)
                .str.replace(r"^\(\d+\)\s*", "", regex=True)
                .str.strip())

# Age band
df["age_band"] = pd.cut(pd.to_numeric(df[AGE_COL], errors="coerce"),
                        bins=[0, 17, 24, 34, 44, 54, 64, 120],
                        labels=["<18", "18-24", "25-34", "35-44", "45-54", "55-64", "65+"])

# Gender tidy (example mapping)
gender_map = {
    "(1) Male":      "Male",
    "(2) Female":    "Female",
    "(3) Non-binary": "Non-binary",
    "(-7) Skipped":  "Skipped"
}
df["gender"] = df[GENDER_COL].map(gender_map).fillna("Other")

# Education tidy (trim prefix “(x) ”)
df["education"] = df[EDU_COL].astype(str).str.replace(r"^\(\d+\)\s*", "", regex=True)

# Income tidy and sort into buckets
df["income_raw"] = (
    df[INCOME_COL]
    .astype(str)
    .str.replace(r"^\(\-?\d+\)\s*", "", regex=True)   # drop "(3) "
    .str.strip()
)

income_map = {
    "Under $20,000":                 "Low (<$40k)",
    "$20,000 – $39,999":             "Low (<$40k)",
    "$20,000 - $39,999":             "Low (<$40k)",   # handle en-dash or hyphen
    "$40,000 – $59,999":             "Middle ($40k–$99k)",
    "$40,000 - $59,999":             "Middle ($40k–$99k)",
    "$60,000 – $79,999":             "Middle ($40k–$99k)",
    "$60,000 - $79,999":             "Middle ($40k–$99k)",
    "$80,000 – $99,999":             "Middle ($40k–$99k)",
    "$80,000 - $99,999":             "Middle ($40k–$99k)",
    "$100,000 – $124,999":           "High (≥$100k)",
    "$100,000 - $124,999":           "High (≥$100k)",
    "$125,000 – $149,999":           "High (≥$100k)",
    "$125,000 - $149,999":           "High (≥$100k)",
    "$150,000 or more":              "High (≥$100k)",
    "Skipped":                       "Skipped/NA",
}

df["income_bucket"] = df["income_raw"].map(income_map).fillna("Skipped/NA")

# 6.  Recode barrier items  (Selected=1, else 0)
# ------------------------------------------------------------------
for col in BARRIER_COLS:
    df[col] = df[col].map({"(1) Selected": 1,
                           "(0) Not selected": 0}).fillna(0).astype(int)


# printing the head of the dataframe
print(df.head())


# 1️⃣  % of respondents selecting each barrier  ───────────
#     A) by region
barrier_pct_region = (
    df.groupby("region")[BARRIER_COLS]
      .mean()            # 0/1 → share
      .mul(100)          # to percent
      .round(1)          # 1-dec place
)

#     B) by income bucket
barrier_pct_income = (
    df.groupby("income_bucket")[BARRIER_COLS]
      .mean()
      .mul(100)
      .round(1)
)

# 2️⃣  Average number of barriers per respondent ──────────
mean_barriers_by_region = (
    df.assign(n_barriers=df[BARRIER_COLS].sum(axis=1))
      .groupby("region")["n_barriers"]
      .mean()
      .round(2)
      .to_frame("avg_barriers")
)

# 3️⃣  Save to disk so Tableau / Power BI / Excel can ingest
barrier_pct_region.to_csv("barrier_pct_by_region.csv")
barrier_pct_income.to_csv("barrier_pct_by_income.csv")
mean_barriers_by_region.to_csv("avg_barriers_by_region.csv")

print("✔️ 3 summary files written:")
print("   • barrier_pct_by_region.csv")
print("   • barrier_pct_by_income.csv")
print("   • avg_barriers_by_region.csv")

# Checking to see if the csv created have been put in the correct working directory
import os
print("Current working dir:", os.getcwd())
