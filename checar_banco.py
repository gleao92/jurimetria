import db

with db.conectar() as con:
    cur = con.execute("SELECT COUNT(*) AS n FROM publicacoes")
    print("total:", dict(cur.fetchone()))
    cur = con.execute(
        "SELECT COUNT(*) AS n FROM publicacoes WHERE teor LIKE '%<%' AND teor LIKE '%>%'")
    print("com tag:", dict(cur.fetchone()))
    cur = con.execute(
        "SELECT id, substr(teor,1,200) AS amostra FROM publicacoes "
        "WHERE teor LIKE '%</div>%' LIMIT 3")
    for r in cur.fetchall():
        print("---", dict(r))
