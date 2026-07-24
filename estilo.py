"""
Identidade visual do Tempestivo.

DECISÕES E POR QUÊ
Numa controladoria a informação é UMA: quantos dias úteis restam. Então o
número é o elemento principal — grande, na margem esquerda, como a numeração
de um livro de registro. O resto (ato, cliente, processo) fica quieto ao lado.
O olho desce a coluna de números e para no menor.

Cor: papel neutro frio (não creme), tinta quase preta, verde institucional
profundo como âncora, e a urgência só aparece no número — vermelho para
vencido/hoje, âmbar para apertado, verde para folga. Cor não decora: é dado.

Tipo: serifa (Newsreader) exclusivamente nos numerais, com figuras tabulares
para as colunas alinharem; sans (Inter Tight) em todo o resto. A serifa dá o
ar documental do meio jurídico sem transformar a tela em jornal.
"""

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter+Tight:wght@400;500;600;700&family=Newsreader:opsz,wght@6..72,400;6..72,600&display=swap');

:root{
  --papel:#F6F5F2; --tinta:#16181A; --suave:#6B6E72; --regua:#E2E0DA;
  --verde:#14453A; --alarme:#A31D1D; --atencao:#B45309; --calmo:#14453A;
}

.stApp{ background:var(--papel); }
html, body, [class*="css"]{ font-family:'Inter Tight',system-ui,sans-serif; }

/* cabeçalho */
.cabeca{ display:flex; align-items:baseline; justify-content:space-between;
  border-bottom:2px solid var(--tinta); padding-bottom:.5rem; margin-bottom:.25rem; }
.marca{ font-family:'Newsreader',Georgia,serif; font-size:1.75rem; font-weight:600;
  letter-spacing:-.01em; color:var(--tinta); line-height:1; }
.marca small{ font-family:'Inter Tight',sans-serif; font-size:.72rem; font-weight:500;
  letter-spacing:.14em; text-transform:uppercase; color:var(--suave);
  display:block; margin-top:.35rem; }
.hoje{ font-size:.82rem; color:var(--suave); text-align:right; line-height:1.5; }
.hoje-topo{ font-size:.8rem; color:var(--tinta); line-height:1.45; padding-top:.5rem; }
.hoje-topo span{ color:var(--suave); font-size:.74rem; }
hr.regua-topo{ border:0; border-top:2px solid var(--tinta); margin:.1rem 0 .2rem; }

/* navegação do calendário: compacta, sem caixas enormes vazias */
[class*="st-key-navcal"] button{ min-height:0!important; padding:.2rem .5rem!important;
  font-size:.9rem!important; }

/* linha de situação */
.situacao{ display:flex; gap:1.6rem; flex-wrap:wrap; padding:.7rem 0 1rem;
  border-bottom:1px solid var(--regua); margin-bottom:1.3rem; }
.situacao b{ font-family:'Newsreader',serif; font-size:1.35rem; font-weight:600;
  font-variant-numeric:tabular-nums; margin-right:.3rem; }
.situacao span{ font-size:.82rem; color:var(--suave); }

/* registro de prazos */
.conta{ text-align:right; padding-right:1rem; border-right:1px solid var(--regua);
  min-height:64px; }
.conta .num{ font-family:'Newsreader',Georgia,serif; font-size:2.5rem; font-weight:600;
  font-variant-numeric:tabular-nums; line-height:1; display:block; }
.conta .un{ font-size:.66rem; text-transform:uppercase; letter-spacing:.1em;
  color:var(--suave); display:block; margin-top:.2rem; }
.corpo{ padding-top:.15rem; }
.corpo .ato{ font-size:1.02rem; font-weight:600; color:var(--tinta); line-height:1.25; }
.corpo .cliente{ font-size:.9rem; color:var(--tinta); opacity:.75; margin-top:.1rem; }
.corpo .meta{ font-size:.75rem; color:var(--suave); margin-top:.3rem;
  font-variant-numeric:tabular-nums; }
.divisa{ border:0; border-top:1px solid var(--regua); margin:.85rem 0; }

/* selo de estado */
.selo{ display:inline-block; font-size:.66rem; font-weight:600; letter-spacing:.07em;
  text-transform:uppercase; padding:.14rem .5rem; border-radius:2px;
  border:1px solid currentColor; margin-left:.4rem; vertical-align:.12em; }

/* seções */
.secao{ font-size:.72rem; font-weight:600; letter-spacing:.14em; text-transform:uppercase;
  color:var(--suave); margin:2rem 0 .8rem; padding-bottom:.35rem;
  border-bottom:1px solid var(--regua); }
.vazio{ font-family:'Newsreader',serif; font-size:1.1rem; color:var(--verde);
  padding:2rem 0; text-align:center; }
.vazio small{ display:block; font-family:'Inter Tight',sans-serif; font-size:.82rem;
  color:var(--suave); margin-top:.4rem; }

/* passos da configuração */
.passo{ font-family:'Newsreader',serif; font-size:.95rem; color:var(--verde);
  font-weight:600; letter-spacing:.02em; }

/* abas mais discretas */
.stTabs [data-baseweb="tab-list"]{ gap:1.6rem; border-bottom:1px solid var(--regua); }
.stTabs [data-baseweb="tab"]{ padding:.4rem 0; font-size:.88rem; font-weight:500; }

section[data-testid="stSidebar"]{ background:#EFEEE9; border-right:1px solid var(--regua); }
.stButton>button{ border-radius:3px; font-weight:500; font-size:.86rem; }
</style>
"""


def linha(cor: str, numero: str, unidade: str, ato: str,
          cliente: str, meta: str, selo: str = "") -> str:
    """Uma linha do registro: contagem na margem, conteúdo ao lado."""
    marca = (f'<span class="selo" style="color:{cor}">{selo}</span>' if selo else "")
    return f"""
<div style="display:flex; gap:1rem;">
  <div class="conta" style="color:{cor}; min-width:88px;">
    <span class="num">{numero}</span><span class="un">{unidade}</span>
  </div>
  <div class="corpo">
    <div class="ato">{ato}{marca}</div>
    <div class="cliente">{cliente}</div>
    <div class="meta">{meta}</div>
  </div>
</div>"""


CSS_AGENDA = """
<style>
.cal{ width:100%; border-collapse:separate; border-spacing:0;
      table-layout:fixed; margin-top:.4rem; }
.cal th{ font-size:.66rem; font-weight:600; letter-spacing:.12em;
  text-transform:uppercase; color:var(--suave); padding:0 0 .5rem;
  text-align:left; }
.cal td{ vertical-align:top; border:1px solid var(--regua); border-radius:3px;
  padding:.4rem .45rem; height:96px; background:#FFFEFC; }
.cal td.fora{ background:transparent; border-color:transparent; }
.cal td.hoje{ border:1.5px solid var(--tinta); }
.cal td.feriado{ background:#F1EFEA; }
.cal .dia{ font-family:'Newsreader',serif; font-size:1.05rem; font-weight:600;
  font-variant-numeric:tabular-nums; color:var(--tinta); line-height:1;
  display:flex; justify-content:space-between; align-items:baseline; }
.cal .dia em{ font-style:normal; font-family:'Inter Tight',sans-serif;
  font-size:.6rem; color:var(--suave); letter-spacing:.04em; }
.cal td.fora .dia{ opacity:.28; }

.chip{ display:block; font-size:.66rem; line-height:1.25; margin-top:.28rem;
  padding:.16rem .3rem; border-radius:2px; overflow:hidden;
  white-space:nowrap; text-overflow:ellipsis; }
.chip.fatal{ background:#F6DEDC; color:#7A1512; border-left:2.5px solid #A31D1D; }
.chip.fatal.folga{ background:#E3EDE7; color:#123A2F; border-left-color:#14453A; }
.chip.fatal.perto{ background:#F7EAD5; color:#6E3B04; border-left-color:#B45309; }
.chip.interno{ background:transparent; color:var(--suave);
  border-left:2.5px solid var(--regua); }
.chip.mais{ background:transparent; color:var(--suave); font-weight:600; }
/* célula do calendário nativo */
.cabdia{ font-size:.62rem; font-weight:600; letter-spacing:.12em;
  text-transform:uppercase; color:var(--suave); padding:0 0 .3rem .1rem; }
.cel{ border-top:1px solid var(--regua); padding:.3rem .1rem .1rem; }
.cel.fora .dia{ opacity:.25; }
.cel.hoje{ border-top:2px solid var(--tinta); }
.cel.feriado{ background:#F1EFEA; }
.cel .dia{ font-family:'Newsreader',serif; font-size:1rem; font-weight:600;
  font-variant-numeric:tabular-nums; display:flex; justify-content:space-between;
  align-items:baseline; }
.cel .dia em{ font-style:normal; font-family:'Inter Tight',sans-serif;
  font-size:.55rem; color:var(--suave); }

/* botões que viram etiquetas de prazo */
[class*="st-key-chip"] button{
  width:100%; min-height:0!important; height:auto!important;
  padding:.12rem .3rem!important; border:none!important;
  border-left:2.5px solid!important; border-radius:2px!important;
  justify-content:flex-start!important; text-align:left!important;
  margin-bottom:.16rem!important; box-shadow:none!important; }
[class*="st-key-chip"] button p{
  font-size:.6rem!important; line-height:1.2!important; font-weight:500!important;
  overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
[class*="st-key-chipfatalurg"] button{ background:#F6DEDC!important;
  color:#7A1512!important; border-left-color:#A31D1D!important; }
[class*="st-key-chipfatalperto"] button{ background:#F7EAD5!important;
  color:#6E3B04!important; border-left-color:#B45309!important; }
[class*="st-key-chipfatalfolga"] button{ background:#E3EDE7!important;
  color:#123A2F!important; border-left-color:#14453A!important; }
[class*="st-key-chipinterno"] button{ background:transparent!important;
  color:var(--suave)!important; border-left-color:var(--regua)!important; }
[class*="st-key-chipcompromissoaudiencia"] button,
[class*="st-key-chipcompromissopericia"] button{ background:#F3E3DA!important;
  color:#7C2D12!important; border-left-color:#7C2D12!important;
  font-weight:600!important; }
[class*="st-key-chipcompromissoreuniao"] button,
[class*="st-key-chipcompromissodiligencia"] button{ background:#E1EAF0!important;
  color:#1E4D6B!important; border-left-color:#1E4D6B!important; }
[class*="st-key-chipcompromissolembrete"] button{ background:#F1EFEA!important;
  color:#5A5D61!important; border-left-color:#B8B5AE!important; }
[class*="st-key-chip"] button:hover{ filter:brightness(.94); }
.detalhe{ border:1px solid var(--regua); border-left:4px solid var(--verde);
  border-radius:3px; padding:1rem 1.1rem; background:#FFFEFC; margin-top:1rem; }
.detalhe .t{ font-family:'Newsreader',serif; font-size:1.3rem; font-weight:600;
  color:var(--tinta); line-height:1.2; }
.detalhe .c{ font-size:.9rem; color:var(--tinta); opacity:.8; margin-top:.15rem; }
.detalhe dl{ display:grid; grid-template-columns:auto 1fr; gap:.3rem 1.1rem;
  margin:.9rem 0 0; font-size:.82rem; }
.detalhe dt{ color:var(--suave); text-transform:uppercase; font-size:.66rem;
  letter-spacing:.09em; padding-top:.15rem; }
.detalhe dd{ margin:0; font-variant-numeric:tabular-nums; }

/* cabeçalho e leitura no painel de revisão */
.cab-rev{ display:flex; justify-content:space-between; align-items:baseline;
  gap:1rem; border-bottom:1px solid var(--regua); padding-bottom:.4rem; }
.cab-rev .proc{ font-family:'Newsreader',serif; font-size:1.15rem; font-weight:600;
  font-variant-numeric:tabular-nums; color:var(--tinta); }
.cab-rev .org{ font-size:.74rem; color:var(--suave); text-align:right; }
.cli-rev{ font-size:.82rem; color:var(--suave); margin:.3rem 0 .8rem; }

.trecho{ background:#FBF6E8; border-left:3px solid #B45309; border-radius:2px;
  padding:.55rem .75rem; margin-bottom:.8rem; }
.trecho b{ display:block; font-size:.62rem; letter-spacing:.11em;
  text-transform:uppercase; color:#8A5A08; margin-bottom:.25rem; }
.trecho div{ font-size:.9rem; line-height:1.45; color:var(--tinta); }

.teor-completo{ font-size:.86rem; line-height:1.6; color:var(--tinta);
  max-height:340px; overflow-y:auto; padding:.6rem .8rem; background:#FFFEFC;
  border:1px solid var(--regua); border-radius:3px; text-align:justify; }

/* semana e dia */
.sem td{ height:180px; }
.diaLista{ border-left:3px solid var(--regua); padding:.15rem 0 .15rem .7rem;
  margin-bottom:.85rem; }
.diaLista .t{ font-size:.95rem; font-weight:600; color:var(--tinta); }
.diaLista .s{ font-size:.78rem; color:var(--suave); margin-top:.12rem; }

.legenda{ display:flex; gap:1.1rem; flex-wrap:wrap; font-size:.7rem;
  color:var(--suave); margin-top:.9rem; }
.legenda i{ display:inline-block; width:9px; height:9px; border-radius:2px;
  margin-right:.35rem; vertical-align:-1px; font-style:normal; }
</style>
"""
