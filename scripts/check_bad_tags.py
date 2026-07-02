import json
import sqlite3

c = sqlite3.connect("./data/studob.db")

for table in ["app_questions", "test_questions"]:
    rows = c.execute(f"SELECT id, tags FROM {table} WHERE tags IS NOT NULL").fetchall()
    bad = 0
    for rid, tags in rows:
        if not tags or tags.strip() == "":
            continue
        try:
            json.loads(tags)
        except (json.JSONDecodeError, TypeError) as e:
            bad += 1
            if bad <= 3:
                print(f"BAD {table} id={rid}, tags={repr(tags)[:200]}, error={e}")
    print(f"{table}: {bad} bad tags out of {len(rows)}")

c.close()
print("Done")
