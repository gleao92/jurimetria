import db
with db.conectar() as con:
    cur = con.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    for r in cur.fetchall():
        print(dict(r))
