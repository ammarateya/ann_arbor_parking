## Ann Arbor Citation Scraper

Python scraper that builds and maintains a database of Ann Arbor citations.

### Setup

1. Create and activate a virtualenv

```bash
python3 -m venv .venv && source .venv/bin/activate
```

2. Install dependencies

```bash
pip install -r requirements.txt
```

3. Configure environment

- Create a `.env` file with the following variables (or export them in your shell):
  - `DB_HOST`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_PORT`

### Database schema

Apply `schema.sql` to your Supabase Postgres (SQL Editor or psql):

```bash
psql "host=$DB_HOST dbname=$DB_NAME user=$DB_USER password=$DB_PASSWORD port=$DB_PORT sslmode=require" -f schema.sql
```

### Run

- Initial backfill (once):
  - Edit `main.py` and uncomment `initial_database_build()` under `if __name__ == "__main__":`
- Ongoing job every minute:

```bash
python main.py
```

### Notes

- Scraper respects portal verification token and parses grid rows.
- OCR helpers in `ocr_utils.py` for future image text extraction.
- Tune delays if you encounter throttling.
