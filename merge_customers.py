
import argparse
import csv
import re
import sys
from datetime import date, datetime

FIELDS = ["name", "email", "phone", "signup_date"]

def norm_name(s):
    """Collapse runs of whitespace; leave the casing as typed."""
    return " ".join((s or "").split())


def norm_email(s):
    """Emails are compared case-insensitively and ignoring stray spaces."""
    return re.sub(r"\s+", "", s or "").lower()


def norm_phone(s, default_cc="1"):
    """Return the phone in +<country><number> form, or '' if there are no digits."""
    digits = re.sub(r"\D", "", s or "")
    if not digits: 
        return ""
    if len(digits) == 10: 
        digits = default_cc + digits
    return "+" + digits


def norm_date(s, day_first=True):
    """Parse a date string."""
    s = (s or "").strip()
    if not s:
        return None, "missing date"

    m = re.fullmatch(r"(\d{4})-(\d{1,2})-(\d{1,2})", s)
    if m:
        y, mo, d = map(int, m.groups())
        return _build(y, mo, d, s, "")

    m = re.fullmatch(r"(\d{1,2})[/.-](\d{1,2})[/.-](\d{4})", s)
    if m:
        a, b, y = map(int, m.groups())

        """a is day b is month"""
        if a > 12 and b <= 12:
            return _build(y, b, a, s, "")
        """b is day a is month"""
        if b > 12 and a <= 12:
            return _build(y, a, b, s, f"'{s}' read as month-first (second number > 12)")
        if a == b:
            return _build(y, a, b, s, "")

        order = "day-first" if day_first else "month-first"
        d, mo = (a, b) if day_first else (b, a)
        return _build(y, mo, d, s, f"'{s}' is ambiguous; assumed {order}")

    return None, f"unparseable date '{s}'"


def _build(y, mo, d, raw, note):
    try:
        return date(y, mo, d), note
    except ValueError:
        return None, f"invalid date '{raw}'"


def load(path, default_cc, day_first, issues):
    rows = []
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        missing = [c for c in FIELDS if c not in (reader.fieldnames or [])]
        if missing:
            sys.exit(f"{path}: missing column(s): {', '.join(missing)}")
        for line_no, raw in enumerate(reader, start=2):
            d, note = norm_date(raw["signup_date"], day_first)
            if note:
                issues.append(f"{path}:{line_no}: {note}")
            row = {
                "name": norm_name(raw["name"]),
                "email": norm_email(raw["email"]),
                "phone": norm_phone(raw["phone"], default_cc),
                "signup_date": d,
            }
            if not row["email"] and not row["phone"]:
                issues.append(f"{path}:{line_no}: no email or phone; kept as its own customer")
            rows.append(row)
    return rows

def group_rows(rows):
    groups = [] 

    for row in rows: 
        keys = {("email", row["email"]), ("phone", row["phone"])}
        keys = {k for k in keys if k[1]}
        merged_rows = [row] 
        merged_keys = set(keys)
        untouched = []

        for g in groups:
            if g["keys"] & keys:
                merged_rows = g["rows"] + merged_rows
                merged_keys != g["keys"]
            else:
                untouched.append(g)

        groups = untouched + [{"rows": merged_rows, "keys": merged_keys}]

    return [g["rows"] for g in groups]


def merge_group(group):
    """Collapse one group into a single row.""" 
    ordered = sorted(group, key=lambda r: (r["signup_date"] is None, r["signup_date"] or date.max))
    merged = dict(ordered[0])
    for other in ordered[1:]:
        for field in ("name", "email", "phone"):
            if not merged[field] and other[field]:
                merged[field] = other[field]
    return merged


def merge(rows):
    merged = [merge_group(g) for g in group_rows(rows)]
    merged.sort(key=lambda r: (r["signup_date"] is None, r["signup_date"] or date.max, r["name"].lower()))
    return merged


"""output"""
def write(rows, path):
    out = sys.stdout if path == "-" else open(path, "w", newline="", encoding="utf-8")
    try:
        writer = csv.DictWriter(out, fieldnames=FIELDS)
        writer.writeheader()
        for r in rows:
            writer.writerow({**r, "signup_date": r["signup_date"].isoformat() if r["signup_date"] else ""})
    finally:
        if out is not sys.stdout:
            out.close()


def main(argv=None):
    p = argparse.ArgumentParser(description="Merge and clean two customer CSV files.")
    p.add_argument("file_a")
    p.add_argument("file_b")
    p.add_argument("-o", "--output", default="merged.csv", help="output path, or - for stdout (default: merged.csv)")
    p.add_argument("--country-code", default="1", help="country code for local numbers starting with 0 (default: 1)")
    p.add_argument("--month-first", action="store_true", help="read ambiguous dates as MM/DD/YYYY instead of DD/MM/YYYY")
    args = p.parse_args(argv)

    issues = []
    rows = []
    for path in (args.file_a, args.file_b):
        rows += load(path, args.country_code, not args.month_first, issues)

    merged = merge(rows)
    write(merged, args.output)

    print(f"Read {len(rows)} rows, wrote {len(merged)} customers " f"({len(rows) - len(merged)} duplicates merged).", file=sys.stderr)
    if issues:
        print(f"\n{len(issues)} row(s) flagged:", file=sys.stderr)
        for msg in issues:
            print("  " + msg, file=sys.stderr)


if __name__ == "__main__":
    main()
