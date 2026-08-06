from captura_djen import amostra
import json
b = amostra("61423", "GO")["exemplo_bruto"]
for k, v in b.items():
    print("---", k, "|", type(v).__name__)
    print(repr(v)[:400])
