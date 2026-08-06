import db
with db.conectar() as con:
    cur = con.execute("""
        SELECT table_name FROM information_schema.tables
        WHERE table_schema='public' ORDER BY table_name
    """)
    for r in cur.fetchall():
        print(dict(r))
