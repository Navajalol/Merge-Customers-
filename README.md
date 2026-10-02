# Customer list merge

Merges two messy customer CSVs into one clean list: no duplicate customers,
normalized emails and phone numbers, dates in `YYYY-MM-DD`, and the earlier
signup date kept when a customer is in both files.

Python 3.8+, standard library only.

## Run it

```bash
python merge_customers.py data/team_a.csv data/team_b.csv -o merged.csv
```

The merged CSV goes to `merged.csv`. A summary and any flagged rows are printed
to stderr, so nothing is changed silently.

Options:

| Flag | Default | Meaning |
|---|---|---|
| `-o PATH` | `merged.csv` | Output file (`-` for stdout) |
| `--country-code N` | `92` | Country code applied to local numbers starting with `0` |
| `--month-first` | off | Read ambiguous dates as `MM/DD/YYYY` |

## Tests

```bash
pip install pytest
pytest
```

## Decisions and assumptions

### When are two rows the same customer?

Two rows are the same customer if they share a **normalized email or a
normalized phone number**.

- Names are not used for matching. They are noisy (`Sara Ahmed` vs `Sara A.`)
  and different people share names.
- Matching is transitive, using union-find: if A and B share an email and B and
  C share a phone, all three are one customer.
- Blank emails or phones never match each other.
- A row with neither email nor phone cannot be matched, so it is kept as its
  own customer and flagged.

Trade-off: two people sharing one phone (a household or office line) would be
merged. For a customer list, a false merge on phone seemed less likely than
missing a real duplicate whose email changed.

### Which values survive a merge?

The row with the earliest signup date is the base. Any blank field is filled
from the other rows. If two rows disagree on a non-blank field (a different
name spelling or a second email), the earliest row's value is kept.

### Normalization

- **Email:** whitespace removed, lower-cased.
- **Phone:** all non-digits stripped, then written as `+<country><number>`.
  A leading `00` is treated as an international prefix; a single leading `0`
  is replaced by the default country code (`92`, since the sample numbers are
  Pakistani). So `+92 300 1234567`, `03001234567` and `00923001234567` all
  become `+923001234567`.
- **Name:** extra whitespace collapsed; casing left alone.

### Ambiguous dates such as `03/04/2024`

Slash dates are read as **day-first (`DD/MM/YYYY`)**, so `03/04/2024` becomes
`2024-04-03`. Reasons: the brief shows `01/03/2024` alongside `2024-03-01`, and
day-first is the convention where these phone numbers come from.

- First number over 12 (`25/12/2023`): can only be day-first. Not flagged.
- Second number over 12 (`04/25/2024`): can only be month-first. Parsed that
  way and flagged, because it suggests that source may use another convention.
- Both 12 or under and different: day-first assumed and **flagged**.
- Unparseable or impossible (`2024-13-45`): the row is kept with a blank date
  and flagged. A customer is never dropped because of a bad date.

When merging, a blank date always loses to a real one.

## Sample data

`data/team_a.csv` and `data/team_b.csv` have 8 rows each and cover: email case
and whitespace duplicates, the same phone in several formats, a customer
matched only by phone, a blank email, a blank phone, an ambiguous date, a
month-first date, an invalid date, and customers unique to each file. They
merge into 11 customers.
