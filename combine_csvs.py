import os
import re
import glob
import pandas as pd

UPLOAD_DIR = "/root/.claude/uploads/99928b2c-8330-4099-b8aa-0a3fe4fd1910"
OUTPUT = "/home/user/chapter-gobblecube-dashboard/blinkit_rca_combined.xlsx"


def sub_category_from_filename(path):
    name = os.path.splitext(os.path.basename(path))[0]
    # strip leading "<hash>-" and the "blinkitrcadownload_" prefix
    name = re.sub(r"^[0-9a-fA-F]+-", "", name)
    name = re.sub(r"^blinkitrcadownload_", "", name)
    return name.replace("_", " ").strip()


files = sorted(glob.glob(os.path.join(UPLOAD_DIR, "*.csv")))
frames = []
summary = []
for f in files:
    sub = sub_category_from_filename(f)
    df = pd.read_csv(f)
    df.insert(0, "Sub Category", sub)
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
