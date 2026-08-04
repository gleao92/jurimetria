"""
Identidade visual do Tempestivo.

A DECISÃO CENTRAL
Numa controladoria, a informação é UMA: quantos dias úteis restam. Por isso o
número é o herói — serifa, tabular, grande, numa coluna fixa à esquerda. Todo
o resto (ato, cliente, processo) fica quieto ao lado. O olho desce a coluna de
números e para no menor.

POR QUE SAÍMOS DO FUNDO BEGE
A versão anterior usava papel creme com serifa — combinação que hoje é o
visual padrão de quase todo layout gerado automaticamente, e parte da sensação
de "template" vinha dali. Trocamos por cinza frio com cards brancos: lê como
software, não como papel envelhecido. A serifa continua, mas só nos NUMERAIS,
onde tem função (figuras tabulares alinham em coluna) e não apenas estilo.

A BARRA ESCURA
É a única ousadia. Serve à função: a navegação recua, o conteúdo avança. Num
painel cujo trabalho é fazer o advogado enxergar o que está vencendo, tudo que
não é prazo deve pesar menos.

COR É DADO, NÃO DECORAÇÃO
Vermelho, âmbar e verde aparecem apenas no numeral da contagem e nas etiquetas
da agenda. Nada mais é colorido por gosto.
"""

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Instrument+Sans:wght@400;500;600;700&family=Newsreader:opsz,wght@6..72,400;6..72,500;6..72,600&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20,400,0,0&display=block');
@import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20,400,0,0&display=swap');

:root{
  --canvas:#F1F3F5;
  --surface:#FFFFFF;
  --ink:#14171A;
  --muted:#697077;
  --line:#E1E5EA;
  --barra:#FAFBFC;
  --barra-tx:#4A5560;
  --barra-linha:#E4E8EC;
  --accent:#0F4C3A;
  --urgente:#B42318;
  --atencao:#B54708;
  --raio:10px;
  --sombra:0 1px 2px rgba(16,35,28,.05), 0 4px 12px rgba(16,35,28,.06);
  /* apelidos usados pelo CSS da agenda */
  --tinta:#14171A; --suave:#697077; --regua:#E1E5EA; --papel:#F1F3F5;
  --verde:#0F4C3A; --alarme:#B42318;
}

.stApp{ background:var(--canvas); }
html, body, [class*="css"], .stMarkdown, p, div, span, label, input, textarea{
  font-family:'Instrument Sans',system-ui,-apple-system,sans-serif;
}
.block-container{ padding-top:2.2rem; padding-bottom:4rem; max-width:1180px; }

/* ─────────── barra lateral ─────────── */
section[data-testid="stSidebar"]{
  background:var(--barra); border-right:1px solid var(--barra-linha);
  width:252px!important;
}
section[data-testid="stSidebar"] > div{ padding-top:1.6rem; }
section[data-testid="stSidebar"] *{ color:var(--barra-tx); }
.marca-barra{
  font-family:'Newsreader',Georgia,serif; font-size:1.3rem; font-weight:600;
  color:var(--ink)!important; letter-spacing:-.01em; line-height:1;
  padding:0 .35rem .1rem;
}
.marca-barra small{
  display:block; font-family:'Instrument Sans',sans-serif; font-size:.6rem;
  font-weight:600; letter-spacing:.16em; text-transform:uppercase;
  color:var(--muted)!important; margin-top:.4rem;
}
.grupo-barra{
  font-size:.6rem; font-weight:600; letter-spacing:.15em; text-transform:uppercase;
  color:#8A939D!important; padding:0 .5rem .45rem; margin-top:1.7rem;
}

[class*="st-key-menu"] button{
  width:100%; justify-content:flex-start!important; text-align:left!important;
  background:transparent!important; border:none!important; color:var(--barra-tx)!important;
  padding:.52rem .6rem!important; border-radius:7px!important; min-height:0!important;
  box-shadow:none!important; transition:background .13s ease;
}
[class*="st-key-menu"] button:hover{ background:#EDF0F3!important; }
[class*="st-key-menu"] button p{
  font-size:.895rem!important; font-weight:500!important; color:var(--barra-tx)!important;
}
[class*="st-key-menu"] button [data-testid="stIconMaterial"]{
  font-size:1.1rem!important; margin-right:.6rem!important; opacity:.7;
}
[class*="st-key-menuativo"] button{ background:#E6EDEA!important; }
[class*="st-key-menuativo"] button p{ font-weight:600!important; color:var(--accent)!important; }
[class*="st-key-menuativo"] button [data-testid="stIconMaterial"]{
  opacity:1; color:var(--accent)!important;
}

[class*="st-key-acao_"] button{
  width:100%; background:var(--accent)!important; border:none!important;
  border-radius:7px!important; padding:.55rem!important; min-height:0!important;
}
[class*="st-key-acao_"] button:hover{ background:#0C3D2E!important; }
[class*="st-key-acao_"] button p{
  font-weight:600!important; font-size:.84rem!important; color:#FFFFFF!important;
}

.rodape-barra{
  border-top:1px solid var(--barra-linha); margin-top:1.4rem; padding:.9rem .5rem 0;
}
.rodape-barra b{ color:var(--ink)!important; font-size:.85rem; font-weight:600; }
.rodape-barra span{
  display:block; font-size:.62rem; letter-spacing:.13em; text-transform:uppercase;
  color:var(--muted)!important; margin-top:.16rem;
}

/* ─────────── cabeçalho ─────────── */
.topo{ display:flex; align-items:flex-end; justify-content:space-between;
  gap:1.5rem; margin-bottom:1.5rem; }
.topo h1{
  font-family:'Newsreader',Georgia,serif; font-size:2.05rem; font-weight:600;
  color:var(--ink); letter-spacing:-.018em; line-height:1; margin:0;
}
.topo .sub{ font-size:.9rem; color:var(--muted); margin-top:.35rem; }
.topo .data{ font-size:.82rem; color:var(--muted); text-align:right; line-height:1.5; }
.topo .data b{ color:var(--ink); font-weight:600; }

/* ─────────── painel de situação ─────────── */
.situacao{ display:grid; grid-template-columns:repeat(4,1fr); gap:.85rem;
  margin-bottom:1.9rem; }
.situacao > div{
  background:var(--surface); border:1px solid var(--line); border-radius:var(--raio);
  padding:.9rem 1rem; box-shadow:var(--sombra);
}
.situacao b{
  display:block; font-family:'Newsreader',serif; font-size:1.85rem; font-weight:600;
  font-variant-numeric:tabular-nums; color:var(--ink); line-height:1;
}
.situacao span{ display:block; font-size:.7rem; color:var(--muted); margin-top:.4rem; }

/* ─────────── cartão de prazo ─────────── */
.cartao{
  background:var(--surface); border:1px solid var(--line); border-radius:var(--raio);
  padding:1rem 1.1rem .85rem; box-shadow:var(--sombra); height:100%;
  display:flex; flex-direction:column; transition:box-shadow .14s ease;
}
.cartao:hover{ box-shadow:0 2px 4px rgba(16,35,28,.07), 0 10px 24px rgba(16,35,28,.09); }
.cartao-topo{ display:flex; gap:.9rem; align-items:flex-start; }
.cartao-info{ flex:1; min-width:0; }

.etiquetas{ display:flex; gap:.35rem; flex-wrap:wrap; margin-bottom:.6rem; }
.etq{
  font-size:.58rem; font-weight:700; letter-spacing:.07em; text-transform:uppercase;
  padding:.2rem .45rem; border-radius:4px; white-space:nowrap;
}
.etq-civel{ background:#E8EEF5; color:#1E4D6B; }
.etq-criminal{ background:#F2E7E1; color:#7C2D12; }
.etq-confirmar{ background:#EFF1F3; color:#5B6167; }
.etq-declarado{ background:#E4EEE9; color:#0C3D2E; }
.etq-sugestao{ background:#FCF0DD; color:#7A3D06; }
.etq-revisar{ background:#FCF0DD; color:#7A3D06; }
.etq-confirmado{ background:#E4EEE9; color:#0C3D2E; }
.etq-cumprido{ background:#EFF1F3; color:#5B6167; }

.cartao .ato{
  font-size:1.06rem; font-weight:600; color:var(--ink); line-height:1.28;
  letter-spacing:-.008em;
}
.cartao .proc{
  font-size:.79rem; color:var(--muted); margin-top:.3rem;
  font-variant-numeric:tabular-nums;
}
.cartao .cliente{ font-size:.85rem; color:var(--ink); opacity:.78; margin-top:.1rem; }

/* a contagem: caixa preenchida, número em serifa */
.contagem{
  border-radius:8px; padding:.45rem .6rem .4rem; text-align:center; min-width:66px;
  flex-shrink:0;
}
.contagem .n{
  font-family:'Newsreader',Georgia,serif; font-size:1.65rem; font-weight:600;
  font-variant-numeric:tabular-nums; line-height:1; display:block; letter-spacing:-.02em;
}
.contagem .u{
  font-size:.53rem; font-weight:700; letter-spacing:.09em; text-transform:uppercase;
  display:block; margin-top:.24rem; opacity:.78;
}
.ct-urgente{ background:#FDE7E5; color:#8C1B12; }
.ct-atencao{ background:#FCF0DD; color:#7A3D06; }
.ct-calmo{ background:#E4EEE9; color:#0C3D2E; }
.ct-neutro{ background:#EFF1F3; color:#5B6167; }

.cartao-pe{
  display:flex; gap:1rem; flex-wrap:wrap; align-items:center;
  border-top:1px solid var(--line); margin-top:.85rem; padding-top:.6rem;
  font-size:.73rem; color:var(--muted);
}
.cartao-pe b{ color:var(--ink); font-weight:600; }
.ms{
  font-family:'Material Symbols Outlined'; font-size:14px; line-height:1;
  vertical-align:-3px; margin-right:.24rem; opacity:.65;
}

/* linha simples (compromissos) */
.linha{
  display:flex; gap:1.15rem; background:var(--surface); border:1px solid var(--line);
  border-radius:var(--raio); padding:1rem 1.15rem; box-shadow:var(--sombra);
}
.conta{
  text-align:right; padding-right:1.05rem; border-right:1px solid var(--line);
  min-width:70px; flex-shrink:0;
}
.conta .num{
  font-family:'Newsreader',Georgia,serif; font-size:2rem; font-weight:600;
  font-variant-numeric:tabular-nums; line-height:.95; display:block;
}
.conta .un{
  font-size:.58rem; text-transform:uppercase; letter-spacing:.11em; color:var(--muted);
  display:block; margin-top:.3rem; font-weight:600;
}
.corpo{ padding-top:.1rem; min-width:0; }
.corpo .ato{ font-size:1rem; font-weight:600; color:var(--ink); line-height:1.3; }
.corpo .cliente{ font-size:.86rem; color:var(--ink); opacity:.72; margin-top:.12rem; }
.corpo .meta{ font-size:.74rem; color:var(--muted); margin-top:.4rem;
  font-variant-numeric:tabular-nums; }
.divisa{ border:0; height:.7rem; }
.selo{
  display:inline-block; font-size:.58rem; font-weight:700; letter-spacing:.09em;
  text-transform:uppercase; padding:.16rem .44rem; border-radius:4px;
  border:1px solid currentColor; margin-left:.5rem; vertical-align:.14em;
}

.secao{
  font-size:.66rem; font-weight:700; letter-spacing:.15em; text-transform:uppercase;
  color:var(--muted); margin:2.1rem 0 .9rem;
}
.vazio{
  background:var(--surface); border:1px dashed var(--line); border-radius:var(--raio);
  padding:2.6rem 1.5rem; text-align:center;
}
.vazio-t{ font-family:'Newsreader',serif; font-size:1.22rem; font-weight:500; color:var(--ink); }
.vazio small{ display:block; font-size:.84rem; color:var(--muted); margin-top:.45rem; }

[data-testid="stVerticalBlockBorderWrapper"]{
  background:var(--surface); border-radius:var(--raio)!important;
  border-color:var(--line)!important; box-shadow:var(--sombra);
}
.stButton>button{ border-radius:7px; font-weight:500; font-size:.855rem;
  border-color:var(--line); }
.stButton>button[kind="primary"]{ background:var(--accent); border-color:var(--accent);
  font-weight:600; }
.stButton>button[kind="primary"]:hover{ background:#0C3D2E; border-color:#0C3D2E; }
[data-testid="stTextInput"] input, [data-testid="stNumberInput"] input,
[data-testid="stTextArea"] textarea{ border-radius:7px!important; font-size:.88rem!important; }
[data-testid="stDataFrame"], [data-testid="stDataEditor"]{
  border-radius:var(--raio); overflow:hidden; border:1px solid var(--line); }
div[data-testid="stExpander"]{
  border:1px solid var(--line)!important; border-radius:var(--raio)!important;
  background:var(--surface); }
[data-testid="stVerticalBlock"]{ gap:.62rem; }

@media (max-width:820px){
  .situacao{ grid-template-columns:repeat(2,1fr); }
  .topo{ flex-direction:column; align-items:flex-start; gap:.5rem; }
  .topo .data{ text-align:left; }
}

/* ─────────── ícones ─────────── */
.ms{
  font-family:'Material Symbols Outlined'; font-size:1em; line-height:1;
  vertical-align:-.14em; font-weight:400; margin-right:.28rem; opacity:.65;
}

/* ─────────── cartão de prazo ─────────── */
.cartao{
  background:var(--surface); border:1px solid var(--line); border-radius:var(--raio);
  padding:.95rem 1.05rem .55rem; box-shadow:var(--sombra); height:100%;
  display:flex; flex-direction:column; transition:box-shadow .14s ease;
}
.cartao:hover{ box-shadow:0 2px 4px rgba(16,35,28,.07), 0 8px 20px rgba(16,35,28,.08); }
.cartao-linha{ display:flex; gap:.9rem; align-items:flex-start; }
.cartao-corpo{ flex:1; min-width:0; }

.tags{ display:flex; gap:.36rem; flex-wrap:wrap; margin-bottom:.62rem; }
.tag{
  font-size:.6rem; font-weight:700; letter-spacing:.07em; text-transform:uppercase;
  padding:.2rem .46rem; border-radius:5px; white-space:nowrap;
}
.tag-civel{ background:#E4EEE9; color:#0C3D2E; }
.tag-criminal{ background:#F3E6DE; color:#7C2D12; }
.tag-confirmar{ background:#F1F3F5; color:#697077; }
.tag-suave{ background:#F1F3F5; color:#697077; font-weight:600; text-transform:none;
  letter-spacing:.01em; }
.tag-revisar{ background:#FCF0DD; color:#7A3D06; text-transform:none;
  letter-spacing:.01em; font-weight:600; }
.tag-ok{ background:#E4EEE9; color:#0C3D2E; text-transform:none;
  letter-spacing:.01em; font-weight:600; }

.cartao .ato{
  font-size:1.02rem; font-weight:600; color:var(--ink); line-height:1.28;
  letter-spacing:-.006em;
}
.cartao .proc{
  font-size:.79rem; color:var(--muted); margin-top:.24rem;
  font-variant-numeric:tabular-nums;
}
.cartao .cliente{ font-size:.85rem; color:var(--ink); opacity:.78; margin-top:.1rem; }

.contagem{
  text-align:center; border-radius:8px; padding:.5rem .62rem; min-width:66px;
  flex-shrink:0;
}
.contagem .n{
  font-family:'Newsreader',Georgia,serif; font-size:1.72rem; font-weight:600;
  font-variant-numeric:tabular-nums; line-height:1; display:block; letter-spacing:-.02em;
}
.contagem .u{
  font-size:.54rem; text-transform:uppercase; letter-spacing:.1em; font-weight:700;
  display:block; margin-top:.26rem; opacity:.82;
}
.ct-urgente{ background:#FDE7E5; color:#8C1B12; }
.ct-atencao{ background:#FCF0DD; color:#7A3D06; }
.ct-calmo{ background:#EDF0F2; color:#4A5560; }

.cartao-pe{
  display:flex; gap:1rem; flex-wrap:wrap; align-items:center;
  border-top:1px solid var(--line); margin-top:.8rem; padding-top:.55rem;
  font-size:.745rem; color:var(--muted);
}
.cartao-pe b{ color:var(--ink); font-weight:600; font-variant-numeric:tabular-nums; }

/* cabeçalho de seção com explicação ao lado */
.secao-rica{
  display:flex; align-items:baseline; gap:.55rem; flex-wrap:wrap;
  margin:2rem 0 .95rem;
}
.secao-rica .t{
  font-size:.95rem; font-weight:600; color:var(--ink); letter-spacing:-.005em;
}
.secao-rica .d{ font-size:.79rem; color:var(--muted); }

.topo .sub{ font-size:.87rem; color:var(--muted); margin-top:.32rem; }

/* ═══════════════════════════════════════════════════════════════════
   CORREÇÃO DE LARGURA DO CARTÃO

   Sintoma: o ato quebrava caractere a caractere, na vertical, e as
   etiquetas empilhavam uma por linha.

   Causa: `flex:1` equivale a `flex:1 1 0%` — o bloco de texto parte de
   largura ZERO e só cresce se o flex distribuir o espaço. Quando o
   container pai não tem largura resolvida (o markdown do Streamlit
   dentro de st.columns), ele fica em zero de fato, enquanto a caixa da
   contagem se mantém pelo `flex-shrink:0`. Daí a coluna de letras.

   Correção: `flex:1 1 auto` faz o bloco partir do tamanho do conteúdo,
   e as larguras explícitas garantem que o cartão ocupe a coluna inteira.

   Fica no FIM do arquivo de propósito: precisa vencer as duas
   definições anteriores de .cartao por ordem de cascata.
   ═══════════════════════════════════════════════════════════════════ */

.cartao{ width:100%; box-sizing:border-box; }
.cartao-topo, .cartao-linha{
  display:flex; gap:.9rem; align-items:flex-start; width:100%;
}
.cartao-info, .cartao-corpo{ flex:1 1 auto; min-width:0; }
.contagem{ flex:0 0 auto; }
.cartao .ato, .cartao .proc, .cartao .cliente{
  overflow-wrap:break-word; word-break:normal;
}
.etiquetas, .tags{ display:flex; flex-wrap:wrap; width:100%; }
.cartao-pe{ width:100%; }

/* o markdown do Streamlit também precisa ocupar a coluna toda */
[data-testid="stMarkdownContainer"]{ width:100%; }
</style>
"""


CSS_AGENDA = """
<style>
.cabdia{
  font-size:.6rem; font-weight:700; letter-spacing:.13em; text-transform:uppercase;
  color:var(--muted); padding:0 0 .45rem .15rem;
}
.cel{
  background:var(--surface); border:1px solid var(--line); border-radius:8px;
  padding:.42rem .45rem .3rem; min-height:52px; margin-bottom:.3rem;
}
.cel.fora{ background:transparent; border-color:transparent; }
.cel.fora .dia{ opacity:.26; }
.cel.hoje{ border:1.5px solid var(--accent); }
.cel.feriado{ background:#EDEFF1; }
.cel .dia{
  font-family:'Newsreader',serif; font-size:1rem; font-weight:600;
  font-variant-numeric:tabular-nums; display:flex; justify-content:space-between;
  align-items:baseline; color:var(--ink);
}
.cel .dia em{
  font-style:normal; font-family:'Instrument Sans',sans-serif; font-size:.55rem;
  color:var(--muted); font-weight:600; letter-spacing:.04em;
}

/* etiquetas de prazo/compromisso: botões nativos vestidos de chip */
[class*="st-key-chip"] button{
  width:100%; min-height:0!important; height:auto!important;
  padding:.16rem .38rem!important; border:none!important;
  border-left:2.5px solid!important; border-radius:4px!important;
  justify-content:flex-start!important; text-align:left!important;
  margin-bottom:.18rem!important; box-shadow:none!important;
}
[class*="st-key-chip"] button p{
  font-size:.6rem!important; line-height:1.24!important; font-weight:600!important;
  overflow:hidden; text-overflow:ellipsis; white-space:nowrap;
}
[class*="st-key-chipfatalurg"] button{ background:#FDE7E5!important;
  border-left-color:var(--urgente)!important; }
[class*="st-key-chipfatalurg"] button p{ color:#8C1B12!important; }
[class*="st-key-chipfatalperto"] button{ background:#FCF0DD!important;
  border-left-color:var(--atencao)!important; }
[class*="st-key-chipfatalperto"] button p{ color:#7A3D06!important; }
[class*="st-key-chipfatalfolga"] button{ background:#E4EEE9!important;
  border-left-color:var(--accent)!important; }
[class*="st-key-chipfatalfolga"] button p{ color:#0C3D2E!important; }
[class*="st-key-chipinterno"] button{ background:#F4F6F7!important;
  border-left-color:#C6CDD3!important; }
[class*="st-key-chipinterno"] button p{ color:var(--muted)!important; font-weight:500!important; }
[class*="st-key-chipcompromissoaudiencia"] button,
[class*="st-key-chipcompromissopericia"] button{ background:#F3E6DE!important;
  border-left-color:#7C2D12!important; }
[class*="st-key-chipcompromissoaudiencia"] button p,
[class*="st-key-chipcompromissopericia"] button p{ color:#7C2D12!important; }
[class*="st-key-chipcompromissoreuniao"] button,
[class*="st-key-chipcompromissodiligencia"] button{ background:#E3EBF2!important;
  border-left-color:#1E4D6B!important; }
[class*="st-key-chipcompromissoreuniao"] button p,
[class*="st-key-chipcompromissodiligencia"] button p{ color:#1E4D6B!important; }
[class*="st-key-chipcompromissolembrete"] button{ background:#F1F3F5!important;
  border-left-color:#C6CDD3!important; }
[class*="st-key-chip"] button:hover{ filter:brightness(.96); }

[class*="st-key-navcal"] button{
  min-height:0!important; padding:.24rem .5rem!important; font-size:.9rem!important;
}

.diaLista{
  border-left:3px solid var(--line); padding:.2rem 0 .2rem .75rem; margin-bottom:.8rem;
}
.diaLista .t{ font-size:.95rem; font-weight:600; color:var(--ink); }
.diaLista .s{ font-size:.77rem; color:var(--muted); margin-top:.12rem; }

.legenda{
  display:flex; gap:1rem; flex-wrap:wrap; font-size:.68rem; color:var(--muted);
  margin-top:1rem; padding-top:.8rem; border-top:1px solid var(--line);
}
.legenda i{
  display:inline-block; width:9px; height:9px; border-radius:2px; margin-right:.34rem;
  vertical-align:-1px; font-style:normal;
}

/* painel de detalhe e revisão */
.detalhe{
  border:1px solid var(--line); border-left:4px solid var(--accent);
  border-radius:var(--raio); padding:1.1rem 1.25rem; background:var(--surface);
  box-shadow:var(--sombra);
}
.detalhe .t{
  font-family:'Newsreader',serif; font-size:1.35rem; font-weight:600; color:var(--ink);
  line-height:1.2;
}
.detalhe .c{ font-size:.89rem; color:var(--ink); opacity:.72; margin-top:.16rem; }
.detalhe dl{
  display:grid; grid-template-columns:auto 1fr; gap:.34rem 1.15rem; margin:1rem 0 0;
  font-size:.82rem;
}
.detalhe dt{
  color:var(--muted); text-transform:uppercase; font-size:.62rem; letter-spacing:.1em;
  padding-top:.16rem; font-weight:600;
}
.detalhe dd{ margin:0; font-variant-numeric:tabular-nums; color:var(--ink); }

.cab-rev{
  display:flex; justify-content:space-between; align-items:baseline; gap:1rem;
  border-bottom:1px solid var(--line); padding-bottom:.45rem;
}
.cab-rev .proc{
  font-family:'Newsreader',serif; font-size:1.12rem; font-weight:600;
  font-variant-numeric:tabular-nums; color:var(--ink);
}
.cab-rev .org{ font-size:.73rem; color:var(--muted); text-align:right; }
.cli-rev{ font-size:.82rem; color:var(--muted); margin:.32rem 0 .85rem; }

.trecho{
  background:#FCF6E9; border-left:3px solid var(--atencao); border-radius:6px;
  padding:.6rem .8rem; margin-bottom:.85rem;
}
.trecho b{
  display:block; font-size:.6rem; letter-spacing:.12em; text-transform:uppercase;
  color:#7A3D06; margin-bottom:.26rem; font-weight:700;
}
.trecho div{ font-size:.9rem; line-height:1.5; color:var(--ink); }

.teor-completo{
  font-size:.86rem; line-height:1.65; color:var(--ink); max-height:340px;
  overflow-y:auto; padding:.7rem .9rem; background:var(--canvas);
  border:1px solid var(--line); border-radius:8px; text-align:justify;
}
</style>
"""


def linha(cor: str, numero: str, unidade: str, ato: str,
          cliente: str, meta: str, selo: str = "") -> str:
    """Uma linha do registro: contagem na margem, conteúdo ao lado."""
    marca = (f'<span class="selo" style="color:{cor}">{selo}</span>' if selo else "")
    return f"""
<div class="linha">
  <div class="conta" style="color:{cor}">
    <span class="num">{numero}</span><span class="un">{unidade}</span>
  </div>
  <div class="corpo">
    <div class="ato">{ato}{marca}</div>
    <div class="cliente">{cliente}</div>
    <div class="meta">{meta}</div>
  </div>
</div>"""


CLASSE_AREA = {"civel": ("tag-civel", "Cível"),
               "criminal": ("tag-criminal", "Criminal"),
               "a_confirmar": ("tag-confirmar", "Área a confirmar")}


def cartao_antigo(numero: str, unidade: str, nivel: str, ato: str, processo: str,
                  cliente: str, area: str = "", fonte: str = "", status: str = "",
                  orgao: str = "", fatal: str = "", interno: str = "") -> str:
    """Assinatura ANTIGA do cartão, mantida só por referência.

    Antes se chamava `cartao` e era sobrescrita pela definição de baixo —
    ou seja, já não era chamada por ninguém. Renomeada para o nome deixar
    de mentir; se algum módulo ainda depender dela, o erro aparece na hora
    em vez de silenciosamente pegar a outra função.
    """
    cls_area, rot_area = CLASSE_AREA.get(area, ("tag-confirmar", "Área a confirmar"))
    tags = [f'<span class="tag {cls_area}">{rot_area}</span>']
    if fonte.startswith("declarado"):
        tags.append('<span class="tag tag-suave">prazo na publicação</span>')
    elif fonte.startswith("presumido"):
        tags.append('<span class="tag tag-suave">prazo presumido</span>')
    if status == "pendente_revisao":
        tags.append('<span class="tag tag-revisar">A revisar</span>')
    elif status == "confirmado":
        tags.append('<span class="tag tag-ok">Confirmado</span>')

    pe = []
    if orgao:
        pe.append(f'<span><span class="ms">account_balance</span>{orgao}</span>')
    if fatal:
        pe.append(f'<span><span class="ms">schedule</span>Fatal: <b>{fatal}</b></span>')
    if interno:
        pe.append(f'<span><span class="ms">event</span>Preparar: {interno}</span>')

    return f"""
<div class="cartao">
  <div class="tags">{''.join(tags)}</div>
  <div class="cartao-linha">
    <div class="cartao-corpo">
      <div class="ato">{ato}</div>
      <div class="proc">{processo}</div>
      <div class="cliente">{cliente}</div>
    </div>
    <div class="contagem {nivel}">
      <span class="n">{numero}</span><span class="u">{unidade}</span>
    </div>
  </div>
  <div class="cartao-pe">{''.join(pe)}</div>
</div>"""


def vazio(titulo: str, detalhe: str = "") -> str:
    sub = f"<small>{detalhe}</small>" if detalhe else ""
    return f'<div class="vazio"><div class="vazio-t">{titulo}</div>{sub}</div>'


# ── cartão de prazo ────────────────────────────────────────────────────
_CLASSE_AREA = {"civel": ("etq-civel", "cível"),
                "criminal": ("etq-criminal", "criminal"),
                "a_confirmar": ("etq-confirmar", "área a confirmar")}

_CLASSE_STATUS = {"pendente_revisao": ("etq-revisar", "a revisar"),
                  "confirmado": ("etq-confirmado", "confirmado"),
                  "cumprido": ("etq-cumprido", "cumprido"),
                  "arquivado": ("etq-cumprido", "arquivado")}


def _etiqueta(classe: str, texto: str) -> str:
    return f'<span class="etq {classe}">{texto}</span>'


def etiquetas_do_prazo(p: dict) -> str:
    """Área, origem do prazo e situação — nesta ordem.

    Não é enfeite: a área diz como a contagem foi feita, a origem diz se o
    prazo veio escrito na publicação ou foi deduzido, e a situação diz se o
    advogado já olhou. São as três perguntas que ele faz antes de confiar
    numa data.
    """
    saida = []
    cls, txt = _CLASSE_AREA.get(p.get("area") or "a_confirmar",
                                _CLASSE_AREA["a_confirmar"])
    saida.append(_etiqueta(cls, txt))

    fonte = (p.get("fonte") or "")
    if fonte.startswith("declarado"):
        saida.append(_etiqueta("etq-declarado", "prazo declarado"))
    elif fonte.startswith("presumido"):
        saida.append(_etiqueta("etq-sugestao", "sugestão"))

    cls, txt = _CLASSE_STATUS.get(p.get("status") or "", ("etq-cumprido", ""))
    if txt:
        saida.append(_etiqueta(cls, txt))
    return f'<div class="etiquetas">{"".join(saida)}</div>'


def cartao(p: dict, numero: str, unidade: str, tom: str,
           processo: str = "", orgao: str = "", fatal: str = "",
           interno: str = "") -> str:
    """Cartão de um prazo: etiquetas, ato, contagem à direita, rodapé.

    `tom` é uma de: urgente | atencao | calmo | neutro — define a cor da
    caixa da contagem. A cor traduz a urgência; nada mais no cartão é
    colorido por gosto.
    """
    pe = []
    if orgao:
        pe.append(f'<span><span class="ms">account_balance</span>{orgao}</span>')
    if fatal:
        pe.append(f'<span><span class="ms">schedule</span>Fatal: <b>{fatal}</b></span>')
    if interno:
        pe.append(f'<span>Preparar até {interno}</span>')
    rodape = f'<div class="cartao-pe">{"".join(pe)}</div>' if pe else ""

    cliente = p.get("cliente") or ""
    linha_cliente = f'<div class="cliente">{cliente}</div>' if cliente else ""

    return f"""
<div class="cartao">
  <div class="cartao-topo">
    <div class="cartao-info">
      {etiquetas_do_prazo(p)}
      <div class="ato">{p.get("ato") or "Prazo"}</div>
      <div class="proc">{processo}</div>
      {linha_cliente}
    </div>
    <div class="contagem ct-{tom}">
      <span class="n">{numero}</span><span class="u">{unidade}</span>
    </div>
  </div>
  {rodape}
</div>"""


def tom_por_dias(n) -> str:
    """Traduz dias úteis restantes no tom da caixa de contagem."""
    if n is None:
        return "neutro"
    if n <= 2:
        return "urgente"
    if n <= 5:
        return "atencao"
    return "calmo"
