import os
import re
import glob
import pandas as pd

# Read the raw CSV exports committed to the repo, and write the combined
# workbook alongside them. Paths are relative to this script's directory so it
# works from a fresh clone.
#
# Platform-aware: set PLATFORM=instamart (or zepto) to read raw_csvs_<platform>/
# and write <platform>_rca_combined.xlsx. Default 'blinkit' keeps the original
# paths (raw_csvs/ -> blinkit_rca_combined.xlsx) so nothing changes for Blinkit.
PLATFORM = os.environ.get("PLATFORM", "blinkit").lower()
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "raw_csvs" if PLATFORM == "blinkit" else f"raw_csvs_{PLATFORM}")
OUTPUT = os.path.join(BASE_DIR, f"{PLATFORM}_rca_combined.xlsx")


def sub_category_from_filename(path):
    name = os.path.splitext(os.path.basename(path))[0]
    # strip leading "<hash>-" and any "<platform>rcadownload_" prefix
    name = re.sub(r"^[0-9a-fA-F]+-", "", name)
    name = re.sub(r"^[a-z]+rcadownload_", "", name)
    return name.replace("_", " ").strip()


files = sorted(glob.glob(os.path.join(UPLOAD_DIR, "*.csv")))
frames = []
summary = []
for f in files:
    fallback = sub_category_from_filename(f)
    df = pd.read_csv(f)
    # Prefer the source's own "Category" column (canonical label); fall back to
    # the filename only where Category is missing — minimizes filename dependency.
    if "Category" in df.columns:
        sub_col = df["Category"].astype(str).str.strip()
        sub_col = sub_col.mask(sub_col.isin(["", "nan", "None"]), fallback)
    else:
        sub_col = fallback
    df.insert(0, "Sub Category", sub_col)
    sub = df["Sub Category"].mode().iloc[0] if len(df) else fallback
    frames.append(df)
    summary.append((os.path.basename(f), sub, len(df)))

combined = pd.concat(frames, ignore_index=True)
combined.to_excel(OUTPUT, sheet_name="Combined", index=False)

print("Files combined:")
for fn, sub, n in summary:
    print(f"  {sub:<28} {n:>5} rows   ({fn})")
print(f"\nTotal rows: {len(combined)}")
print(f"Columns ({len(combined.columns)}): {list(combined.columns)}")
print(f"Output: {OUTPUT}")
