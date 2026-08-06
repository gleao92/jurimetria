from captura_djen import _buscar_bruto
from datetime import date, timedelta
brutos = _buscar_bruto("61423", "GO", date.today() - timedelta(days=60))
com_tag = indisp = vazio = 0
for i in brutos:
    t = str(i.get("texto") or "")
    if not t.strip():
        vazio += 1
    elif "INDISPON" in t.upper():
        indisp += 1
    elif "<" in t and ">" in t:
        com_tag += 1
print(f"total={len(brutos)} com_html={com_tag} indisponivel={indisp} vazio={vazio}")
for i in brutos:
    t = str(i.get("texto") or "")
    if "<" in t and ">" in t:
        print("\n=== EXEMPLO COM HTML ===")
        print(repr(t)[:800])
        break
