import db

with db.conectar() as con:
    print("total       ", dict(con.execute("SELECT COUNT(*) AS n FROM publicacoes").fetchone()))
    print("com_tag     ", dict(con.execute(
        "SELECT COUNT(*) AS n FROM publicacoes WHERE teor LIKE %s AND teor LIKE %s",
        ("%<%", "%>%")).fetchone()))
    print("indisponivel", dict(con.execute(
        "SELECT COUNT(*) AS n FROM publicacoes WHERE UPPER(teor) LIKE %s",
        ("%INDISPON%",)).fetchone()))
    print("prazos      ", dict(con.execute("SELECT COUNT(*) AS n FROM prazos").fetchone()))

    print("\n--- colunas de publicacoes ---")
    cur = con.execute(
        "SELECT column_name, data_type FROM information_schema.columns "
        "WHERE table_name=%s ORDER BY ordinal_position", ("publicacoes",))
    for r in cur.fetchall():
        print(dict(r))

    print("\n--- exemplo sujo ---")
    cur = con.execute("SELECT * FROM publicacoes WHERE teor LIKE %s LIMIT 1", ("%</div>%",))
    for r in cur.fetchall():
        print(repr(dict(r))[:1200])
