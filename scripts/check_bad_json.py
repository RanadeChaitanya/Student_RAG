import json
import sqlite3

c = sqlite3.connect("./data/studob.db")

for table in ["app_questions", "test_questions"]:
    rows = c.execute(f"SELECT id, options FROM {table} WHERE options IS NOT NULL").fetchall()
    bad = 0
    fixed = 0
    nulled = 0
    for rid, opts in rows:
        if not opts or opts.strip() == "":
            continue
        try:
            json.loads(opts)
        except (json.JSONDecodeError, TypeError):
            bad += 1
            cleaned = opts.replace("'", '"')
            try:
                json.loads(cleaned)
                c.execute(f"UPDATE {table} SET options = ? WHERE id = ?", (cleaned, rid))
                fixed += 1
            except (json.JSONDecodeError, TypeError):
                c.execute(f"UPDATE {table} SET options = NULL WHERE id = ?", (rid,))
                nulled += 1
    c.commit()
    print(f"{table}: {bad} bad, {fixed} fixed, {nulled} nulled")

c.close()
print("Done")
