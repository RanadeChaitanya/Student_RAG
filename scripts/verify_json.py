import json
import sqlite3

c = sqlite3.connect("./data/studob.db")

for table in ["app_questions", "test_questions"]:
    print(f"\n=== {table} ===")
    print(f"Total: {c.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0]}")

    bad_opts = 0
    bad_tags = 0
    rows = c.execute(f"SELECT id, options, tags FROM {table}").fetchall()
    for rid, opts, tags in rows:
        if opts and opts.strip():
            try:
                json.loads(opts)
            except:
                bad_opts += 1
                if bad_opts <= 2:
                    print(f"  Bad opts id={rid}: {repr(opts)[:80]}")
        if tags and tags.strip():
            try:
                json.loads(tags)
            except:
                bad_tags += 1
                if bad_tags <= 2:
                    print(f"  Bad tags id={rid}: {repr(tags)[:80]}")

    print(f"  Bad options: {bad_opts}, Bad tags: {bad_tags}")

c.close()
print("\nVerification complete")
