import json
import sqlite3

c = sqlite3.connect("./data/studob.db")

for table in ["app_questions", "test_questions"]:
    rows = c.execute(f"SELECT id, options FROM {table} WHERE options IS NOT NULL").fetchall()
    fixed = 0
    for rid, opts in rows:
        if not opts or opts.strip() == "" or opts.strip() == "None":
            c.execute(f"UPDATE {table} SET options = NULL WHERE id = ?", (rid,))
            fixed += 1
            continue
        try:
            json.loads(opts)
        except (json.JSONDecodeError, TypeError):
            fixed_opts = opts.replace("'", '"')
            try:
                json.loads(fixed_opts)
                c.execute(f"UPDATE {table} SET options = ? WHERE id = ?", (fixed_opts, rid))
                fixed += 1
            except (json.JSONDecodeError, TypeError):
                c.execute(f"UPDATE {table} SET options = NULL WHERE id = ?", (rid,))
                fixed += 1
    c.commit()
    print(f"Fixed {fixed} rows in {table}")

c.close()
print("Done")
