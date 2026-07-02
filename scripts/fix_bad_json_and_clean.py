import json
import sqlite3

c = sqlite3.connect("./data/studob.db")
cur = c.cursor()

# Fix bad tags (Python repr -> JSON) in app_questions
fixed_app = 0
rows = cur.execute("SELECT id, tags FROM app_questions WHERE tags IS NOT NULL").fetchall()
for rid, tags in rows:
    if not tags or tags.strip() == "":
        continue
    try:
        json.loads(tags)
    except (json.JSONDecodeError, TypeError):
        cleaned = tags.replace("'", '"')
        try:
            json.loads(cleaned)
            cur.execute("UPDATE app_questions SET tags = ? WHERE id = ?", (cleaned, rid))
            fixed_app += 1
        except (json.JSONDecodeError, TypeError):
            cur.execute("UPDATE app_questions SET tags = NULL WHERE id = ?", (rid,))
            fixed_app += 1
c.commit()
print(f"Fixed {fixed_app} app_questions tags")

# Fix bad tags in test_questions
fixed_test = 0
rows = cur.execute("SELECT id, tags FROM test_questions WHERE tags IS NOT NULL").fetchall()
for rid, tags in rows:
    if not tags or tags.strip() == "":
        continue
    try:
        json.loads(tags)
    except (json.JSONDecodeError, TypeError):
        cleaned = tags.replace("'", '"')
        try:
            json.loads(cleaned)
            cur.execute("UPDATE test_questions SET tags = ? WHERE id = ?", (cleaned, rid))
            fixed_test += 1
        except (json.JSONDecodeError, TypeError):
            cur.execute("UPDATE test_questions SET tags = NULL WHERE id = ?", (rid,))
            fixed_test += 1
c.commit()
print(f"Fixed {fixed_test} test_questions tags")

# Delete jee_archive app questions
cur.execute("DELETE FROM app_questions WHERE source = 'jee_archive'")
print(f"Deleted {cur.rowcount} jee_archive app_questions")

# Delete test questions from 2023-2025
cur.execute("DELETE FROM test_questions WHERE year IN (2023, 2024, 2025)")
print(f"Deleted {cur.rowcount} test_questions from 2023-2025")

c.commit()

print(f"After cleanup: app={cur.execute('SELECT COUNT(*) FROM app_questions').fetchone()[0]}, test={cur.execute('SELECT COUNT(*) FROM test_questions').fetchone()[0]}")

c.close()
print("Done - ready for re-seed")
