"""
Identidade visual do Tempestivo.

A DECISÃO CENTRAL
Numa controladoria, a informação é UMA: quantos dias úteis restam. Por isso o
número é o herói — serifa, tabular, grande, numa coluna fixa à esquerda. Todo
o resto (ato, cliente, processo) fica quieto ao lado. O olho desce a coluna de
números e para no menor.

TEMA ESCURO, ACENTO ÂMBAR
Fundo grafite (slate-900), cards um tom mais claro (slate-800), texto quase
branco. O acento — âmbar — marca só o que pede atenção: contagem urgente,
item ativo do menu, botão primário. Vermelho (rosa/rose) fica reservado pra
vencido; verde (esmeralda) pra confirmado/concluído; azul pra neutro/a
revisar. Paleta e nomes de classe seguem o protótipo aprovado (Tailwind
slate/amber/emerald/rose/blue), pra qualquer ajuste futuro comparar direto
com as mesmas referências de cor.

A BARRA LATERAL
É onde mora a navegação e o status da captura. Mesmo fundo do conteúdo,
separada só por uma linha — não compete com os cards.

COR É DADO, NÃO DECORAÇÃO
Vermelho, âmbar, verde e azul aparecem no numeral da contagem, nas etiquetas
e nos indicadores de status. Nada mais é colorido por gosto.
"""

import html
import re


def _seguro(texto) -> str:
    """Prepara texto de fora (publicação capturada, digitado pelo advogado)
    para entrar num f-string HTML renderizado com unsafe_allow_html.

    Dois problemas achados no cartão de prazo em produção, ambos com a mesma
    causa: um valor dinâmico (ato, cliente, órgão) sem sanitização, colado
    direto no meio do HTML. Um `<` ou `"` vindo do teor de uma publicação real
    quebra a tag seguinte; uma quebra de linha embutida cria uma "linha em
    branco" no meio do bloco, e o Markdown do Streamlit passa a tratar o resto
    do cartão (a caixa de contagem) como texto/bloco de código — foi exatamente
    o `<div class="contagem...` aparecendo cru na tela. `html.escape` cobre o
    primeiro caso; colapsar quebras de linha em espaço cobre o segundo.
    """
    if texto is None:
        return ""
    plano = re.sub(r"\s+", " ", str(texto)).strip()
    return html.escape(plano)


def _uma_linha(bruto: str) -> str:
    """Achata o HTML do cartão/linha para uma única linha antes de devolver.

    A causa raiz real do bug em produção: quando `cliente` (ou qualquer outro
    campo opcional interpolado sozinho numa linha do template) vem vazio, a
    substituição deixa uma linha só com os espaços de indentação do template
    — e uma linha só com espaço/tab conta como "linha em branco" para o
    CommonMark. Isso fecha o bloco de HTML no meio do cartão; o que vem
    depois (a caixa `.contagem`, indentada com 4+ espaços) deixa de ser
    reconhecido como continuação do HTML e vira bloco de código indentado —
    exatamente o `<div class="contagem...` aparecendo cru na tela, com botão
    de copiar. `_seguro()` sozinho não resolve: ele limpa o CONTEÚDO dinâmico,
    mas essa linha em branco nasce da ESTRUTURA do template, não do dado.
    Sem nenhuma quebra de linha no HTML devolvido, não existe "linha em
    branco" possível.
    """
    return re.sub(r"\s+", " ", bruto).strip()


CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Playfair+Display:wght@600;700&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20,400,0,0&display=block');
@import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20,400,0,0&display=swap');

:root{
  --canvas:#0F172A;
  --surface:#1E293B;
  --ink:#F1F5F9;
  --muted:#94A3B8;
  --line:#334155;
  --barra:#0F172A;
  --barra-tx:#CBD5E1;
  --barra-linha:#1E293B;
  --accent:#F59E0B;
  --accent-tx:#0F172A;
  --urgente:#FB7185;
  --atencao:#FBBF24;
  --calmo:#34D399;
  --azul:#60A5FA;
  --raio:12px;
  --sombra:0 1px 2px rgba(0,0,0,.35), 0 4px 16px rgba(0,0,0,.35);
  /* apelidos usados pelo CSS da agenda */
  --tinta:#F1F5F9; --suave:#94A3B8; --regua:#334155; --papel:#0F172A;
  --verde:#34D399; --alarme:#FB7185;
}

.stApp{ background:var(--canvas); }
html, body, [class*="css"], .stMarkdown, p, div, span, label, input, textarea{
  font-family:'Plus Jakarta Sans',system-ui,-apple-system,sans-serif;
  color:var(--ink);
}
.block-container{ padding-top:2.2rem; padding-bottom:4rem; max-width:1180px; }

/* ─────────── barra lateral ─────────── */
section[data-testid="stSidebar"]{
  background:var(--barra); border-right:1px solid var(--barra-linha);
  width:266px!important;
}
section[data-testid="stSidebar"] > div{ padding-top:1.6rem; }
section[data-testid="stSidebar"] *{ color:var(--barra-tx); }
.marca-barra{
  display:flex; align-items:center; gap:.7rem; padding:0 .5rem .1rem;
}
.marca-barra .icone{
  width:36px; height:36px; border-radius:10px; flex-shrink:0;
  background:rgba(245,158,11,.16); border:1px solid rgba(245,158,11,.4);
  color:var(--accent); display:flex; align-items:center; justify-content:center;
}
.marca-barra .icone .ms{ font-size:1.15rem; margin:0; opacity:1; }
.marca-barra .nome{
  font-family:'Playfair Display',Georgia,serif; font-size:1.18rem; font-weight:700;
  color:var(--ink)!important; letter-spacing:-.01em; line-height:1;
}
.marca-barra small{
  display:block; font-family:'Plus Jakarta Sans',sans-serif; font-size:.6rem;
  font-weight:600; letter-spacing:.16em; text-transform:uppercase;
  color:var(--muted)!important; margin-top:.3rem;
}
.grupo-barra{
  font-size:.62rem; font-weight:700; letter-spacing:.13em; text-transform:uppercase;
  color:#64748B!important; padding:0 .5rem .45rem; margin-top:1.7rem;
}

[class*="st-key-menu"] button{
  width:100%; justify-content:flex-start!important; text-align:left!important;
  background:transparent!important; border:1px solid transparent!important;
  color:var(--barra-tx)!important;
  padding:.52rem .6rem!important; border-radius:8px!important; min-height:0!important;
  box-shadow:none!important; transition:background .13s ease;
}
[class*="st-key-menu"] button:hover{ background:var(--surface)!important; }
[class*="st-key-menu"] button p{
  font-size:.895rem!important; font-weight:500!important; color:var(--barra-tx)!important;
}
[class*="st-key-menu"] button [data-testid="stIconMaterial"]{
  font-size:1.1rem!important; margin-right:.6rem!important; opacity:.75; color:#94A3B8;
}
[class*="st-key-menuativo"] button{
  background:rgba(245,158,11,.15)!important; border-color:rgba(245,158,11,.3)!important;
}
[class*="st-key-menuativo"] button p{ font-weight:600!important; color:#FCD34D!important; }
[class*="st-key-menuativo"] button [data-testid="stIconMaterial"]{
  opacity:1; color:var(--accent)!important;
}

[class*="st-key-acao_"] button{
  width:100%; background:var(--accent)!important; border:none!important;
  border-radius:8px!important; padding:.55rem!important; min-height:0!important;
}
[class*="st-key-acao_"] button:hover{ background:#D97706!important; }
[class*="st-key-acao_"] button p{
  font-weight:700!important; font-size:.84rem!important; color:var(--accent-tx)!important;
}

.rodape-barra{
  border-top:1px solid var(--barra-linha); margin-top:1.4rem; padding:.9rem .5rem 0;
}
.rodape-barra b{ color:var(--ink)!important; font-size:.85rem; font-weight:600; }
.rodape-barra span{
  display:block; font-size:.62rem; letter-spacing:.13em; text-transform:uppercase;
  color:var(--muted)!important; margin-top:.16rem;
}

/* status da captura, na barra lateral */
.captura-status{
  padding:.62rem .7rem; background:var(--surface); border:1px solid var(--barra-linha);
  border-radius:10px; margin:0 0 .3rem;
}
.captura-status .rot{
  font-size:.68rem; font-weight:700; text-transform:uppercase; letter-spacing:.04em;
  display:flex; align-items:center; gap:.4rem;
}
.captura-status .ponto{
  width:8px; height:8px; border-radius:50%; display:inline-block; flex-shrink:0;
}
.captura-status.ativa .rot{ color:#6EE7B7; }
.captura-status.ativa .ponto{ background:#10B981; box-shadow:0 0 0 3px rgba(16,185,129,.25); }
.captura-status.parada .rot{ color:var(--muted); }
.captura-status.parada .ponto{ background:#64748B; }
.captura-status .det{ font-size:.7rem; color:var(--barra-tx); margin-top:.3rem; }
.captura-status .sub{ font-size:.63rem; color:var(--muted); margin-top:.15rem; }
.captura-status code{
  background:var(--barra); padding:.05rem .3rem; border-radius:4px; color:#FCD34D;
}

/* ─────────── cabeçalho ─────────── */
.topo{ display:flex; align-items:flex-end; justify-content:space-between;
  gap:1.5rem; margin-bottom:1.5rem; padding-bottom:1.1rem;
  border-bottom:1px solid var(--line); }
.topo h1{
  font-family:'Playfair Display',Georgia,serif; font-size:2.05rem; font-weight:700;
  color:var(--ink); letter-spacing:-.018em; line-height:1; margin:0;
}
.topo .sub{ font-size:.9rem; color:var(--muted); margin-top:.35rem; }
.topo .data{ font-size:.82rem; color:var(--muted); text-align:right; line-height:1.5; }
.topo .data b{ color:#FCD34D; font-weight:600; }

/* ─────────── painel de situação ─────────── */
.situacao{ display:grid; grid-template-columns:repeat(4,1fr); gap:.85rem;
  margin-bottom:1.9rem; }
.situacao > div{
  background:var(--surface); border:1px solid var(--line); border-radius:var(--raio);
  padding:.85rem 1rem; box-shadow:var(--sombra);
  display:flex; flex-direction:column; justify-content:space-between; min-height:5.4rem;
}
.situacao .rot{
  font-size:.72rem; font-weight:600; color:var(--muted); display:flex;
  align-items:center; gap:.35rem;
}
.situacao .rot .ms{ font-size:.95rem; opacity:1; margin:0; }
.situacao b{
  display:block; font-family:'Plus Jakarta Sans',sans-serif; font-size:1.7rem;
  font-weight:800; font-variant-numeric:tabular-nums; color:var(--ink); line-height:1;
  margin-top:.5rem;
}
.tile-azul .rot .ms, .tile-azul b{ color:var(--azul); }
.tile-esmeralda .rot .ms, .tile-esmeralda b{ color:var(--calmo); }
.tile-ambar .rot .ms, .tile-ambar b{ color:var(--atencao); }
.tile-rosa .rot .ms, .tile-rosa b{ color:var(--urgente); }

/* ─────────── cartão de prazo ─────────── */
.cartao{
  background:rgba(30,41,59,.9); border:1px solid var(--line); border-radius:var(--raio);
  padding:1rem 1.1rem .85rem; box-shadow:var(--sombra); height:100%;
  display:flex; flex-direction:column; transition:border-color .14s ease;
}
.cartao:hover{ border-color:#475569; }
.cartao-topo{ display:flex; gap:.9rem; align-items:flex-start; }
.cartao-info{ flex:1; min-width:0; }

.etiquetas{ display:flex; gap:.35rem; flex-wrap:wrap; margin-bottom:.6rem; align-items:center; }
.etq{
  font-size:.6rem; font-weight:700; letter-spacing:.03em;
  padding:.2rem .5rem; border-radius:5px; white-space:nowrap; border:1px solid transparent;
}
.etq-ato{ background:rgba(245,158,11,.1); color:#FCD34D; border-color:rgba(245,158,11,.2); }
.etq-org{ font-size:.68rem; font-weight:500; color:var(--muted); text-transform:none;
  letter-spacing:0; padding:0; }
.etq-civel{ background:rgba(16,185,129,.12); color:#6EE7B7; }
.etq-criminal{ background:rgba(251,146,60,.14); color:#FDBA74; }
.etq-confirmar{ background:rgba(148,163,184,.14); color:#CBD5E1; }
.etq-declarado{ background:rgba(16,185,129,.12); color:#6EE7B7; }
.etq-sugestao{ background:rgba(245,158,11,.12); color:#FCD34D; }
.etq-revisar{ background:rgba(245,158,11,.12); color:#FCD34D; }
.etq-confirmado{ background:rgba(16,185,129,.12); color:#6EE7B7; }
.etq-cumprido{ background:rgba(148,163,184,.14); color:#CBD5E1; }

.cartao .ato{
  font-size:.95rem; font-weight:700; color:var(--ink); line-height:1.28;
  letter-spacing:-.006em; margin-top:.45rem;
}
.cartao .proc{
  font-size:.79rem; color:var(--muted); margin-top:.3rem;
  font-variant-numeric:tabular-nums;
}
.cartao .cliente{ font-size:.83rem; color:var(--barra-tx); margin-top:.15rem; }
.cartao .cliente b{ color:var(--ink); font-weight:600; }

/* a contagem: número grande colorido, sem caixa preenchida */
.contagem{
  text-align:right; min-width:66px; flex-shrink:0;
}
.contagem .n{
  font-family:'Plus Jakarta Sans',sans-serif; font-size:1.35rem; font-weight:800;
  font-variant-numeric:tabular-nums; line-height:1; letter-spacing:-.01em;
}
.contagem .u{
  font-size:.72rem; font-weight:500; margin-left:.15rem;
}
.contagem .fatal{
  display:block; font-size:.66rem; color:var(--muted); margin-top:.35rem;
}
.ct-urgente .n, .ct-urgente .u{ color:var(--urgente); }
.ct-atencao .n, .ct-atencao .u{ color:var(--atencao); }
.ct-calmo .n, .ct-calmo .u{ color:var(--calmo); }
.ct-neutro .n, .ct-neutro .u{ color:var(--muted); }

.cartao-pe{
  display:flex; gap:1rem; flex-wrap:wrap; align-items:center; justify-content:space-between;
  border-top:1px solid var(--line); margin-top:.85rem; padding-top:.6rem;
  font-size:.73rem; color:var(--muted);
}
.cartao-pe b{ color:#FCD34D; font-weight:600; }
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
  font-family:'Plus Jakarta Sans',sans-serif; font-size:1.7rem; font-weight:800;
  font-variant-numeric:tabular-nums; line-height:.95; display:block; color:var(--azul);
}
.conta .un{
  font-size:.58rem; text-transform:uppercase; letter-spacing:.11em; color:var(--muted);
  display:block; margin-top:.3rem; font-weight:600;
}
.corpo{ padding-top:.1rem; min-width:0; }
.corpo .ato{ font-size:1rem; font-weight:600; color:var(--ink); line-height:1.3; }
.corpo .cliente{ font-size:.86rem; color:var(--barra-tx); margin-top:.12rem; }
.corpo .meta{ font-size:.74rem; color:var(--muted); margin-top:.4rem;
  font-variant-numeric:tabular-nums; }
.divisa{ border:0; height:.7rem; }
.selo{
  display:inline-block; font-size:.58rem; font-weight:700; letter-spacing:.09em;
  text-transform:uppercase; padding:.16rem .44rem; border-radius:4px;
  border:1px solid currentColor; margin-left:.5rem; vertical-align:.14em;
}

.secao{
  font-size:.72rem; font-weight:700; letter-spacing:.1em; text-transform:uppercase;
  color:#FCD34D; margin:2.1rem 0 .9rem; padding-bottom:.55rem;
  border-bottom:1px solid var(--line);
}
.vazio{
  background:rgba(30,41,59,.5); border:1px solid var(--line); border-radius:16px;
  padding:2.8rem 1.5rem; text-align:center;
}
.vazio-t{ font-family:'Playfair Display',serif; font-size:1.22rem; font-weight:600; color:var(--ink); }
.vazio small{ display:block; font-size:.84rem; color:var(--muted); margin-top:.45rem; }

[data-testid="stVerticalBlockBorderWrapper"]{
  background:var(--surface); border-radius:var(--raio)!important;
  border-color:var(--line)!important; box-shadow:var(--sombra);
}
.stButton>button{ border-radius:8px; font-weight:600; font-size:.855rem;
  border-color:var(--line); background:var(--surface); color:var(--ink); }
.stButton>button:hover{ border-color:#475569; background:#28374B; }
.stButton>button[kind="primary"]{ background:var(--accent); border-color:var(--accent);
  font-weight:700; color:var(--accent-tx); }
.stButton>button[kind="primary"]:hover{ background:#D97706; border-color:#D97706; }
[data-testid="stTextInput"] input, [data-testid="stNumberInput"] input,
[data-testid="stTextArea"] textarea{
  border-radius:7px!important; font-size:.88rem!important;
  background:var(--surface)!important; color:var(--ink)!important;
  border-color:var(--line)!important;
}
[data-testid="stDataFrame"], [data-testid="stDataEditor"]{
  border-radius:var(--raio); overflow:hidden; border:1px solid var(--line); }
div[data-testid="stExpander"]{
  border:1px solid var(--line)!important; border-radius:var(--raio)!important;
  background:var(--surface); }
[data-testid="stVerticalBlock"]{ gap:.62rem; }

/* multiselect: os "chips" vêm com o vermelho padrão do BaseWeb — sem relação
   com o tema; sobrescreve pra âmbar, consistente com o resto das etiquetas */
[data-testid="stMultiSelectTagsContainer"] [data-tag]{
  background:rgba(245,158,11,.16)!important; color:#FCD34D!important;
  border:1px solid rgba(245,158,11,.35)!important; border-radius:6px!important;
}
[data-testid="stMultiSelectTagsContainer"] [data-tag] svg{ fill:#FCD34D!important; }
[data-baseweb="select"] > div, [data-baseweb="base-input"]{
  background:var(--surface)!important; border-color:var(--line)!important;
}
[data-baseweb="popover"] li{ background:var(--surface); color:var(--ink); }
[data-baseweb="popover"] li:hover{ background:#28374B; }

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

/* (segunda definição de .cartao/.contagem/.cartao-pe — vence a primeira por
   cascata; mantida em sincronia com o tema escuro acima) */
.cartao-linha{ display:flex; gap:.9rem; align-items:flex-start; }
.cartao-corpo{ flex:1; min-width:0; }

.tags{ display:flex; gap:.36rem; flex-wrap:wrap; margin-bottom:.62rem; }
.tag{
  font-size:.6rem; font-weight:700; letter-spacing:.07em; text-transform:uppercase;
  padding:.2rem .46rem; border-radius:5px; white-space:nowrap;
}
.tag-civel{ background:rgba(16,185,129,.12); color:#6EE7B7; }
.tag-criminal{ background:rgba(251,146,60,.14); color:#FDBA74; }
.tag-confirmar{ background:rgba(148,163,184,.14); color:#CBD5E1; }
.tag-suave{ background:rgba(148,163,184,.14); color:#CBD5E1; font-weight:600; text-transform:none;
  letter-spacing:.01em; }
.tag-revisar{ background:rgba(245,158,11,.12); color:#FCD34D; text-transform:none;
  letter-spacing:.01em; font-weight:600; }
.tag-ok{ background:rgba(16,185,129,.12); color:#6EE7B7; text-transform:none;
  letter-spacing:.01em; font-weight:600; }

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
.cel.feriado{ background:rgba(51,65,85,.4); }
.cel .dia{
  font-family:'Playfair Display',serif; font-size:1rem; font-weight:600;
  font-variant-numeric:tabular-nums; display:flex; justify-content:space-between;
  align-items:baseline; color:var(--ink);
}
.cel .dia em{
  font-style:normal; font-family:'Plus Jakarta Sans',sans-serif; font-size:.55rem;
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
[class*="st-key-chipfatalurg"] button{ background:rgba(251,113,133,.14)!important;
  border-left-color:var(--urgente)!important; }
[class*="st-key-chipfatalurg"] button p{ color:#FDA4AF!important; }
[class*="st-key-chipfatalperto"] button{ background:rgba(251,191,36,.14)!important;
  border-left-color:var(--atencao)!important; }
[class*="st-key-chipfatalperto"] button p{ color:#FCD34D!important; }
[class*="st-key-chipfatalfolga"] button{ background:rgba(52,211,153,.14)!important;
  border-left-color:var(--calmo)!important; }
[class*="st-key-chipfatalfolga"] button p{ color:#6EE7B7!important; }
[class*="st-key-chipinterno"] button{ background:rgba(148,163,184,.12)!important;
  border-left-color:#64748B!important; }
[class*="st-key-chipinterno"] button p{ color:var(--muted)!important; font-weight:500!important; }
[class*="st-key-chipcompromissoaudiencia"] button,
[class*="st-key-chipcompromissopericia"] button{ background:rgba(251,146,60,.14)!important;
  border-left-color:#FB923C!important; }
[class*="st-key-chipcompromissoaudiencia"] button p,
[class*="st-key-chipcompromissopericia"] button p{ color:#FDBA74!important; }
[class*="st-key-chipcompromissoreuniao"] button,
[class*="st-key-chipcompromissodiligencia"] button{ background:rgba(96,165,250,.14)!important;
  border-left-color:var(--azul)!important; }
[class*="st-key-chipcompromissoreuniao"] button p,
[class*="st-key-chipcompromissodiligencia"] button p{ color:#93C5FD!important; }
[class*="st-key-chipcompromissolembrete"] button{ background:rgba(148,163,184,.12)!important;
  border-left-color:#64748B!important; }
[class*="st-key-chip"] button:hover{ filter:brightness(1.15); }

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
  font-family:'Playfair Display',serif; font-size:1.35rem; font-weight:600; color:var(--ink);
  line-height:1.2;
}
.detalhe .c{ font-size:.89rem; color:var(--barra-tx); margin-top:.16rem; }
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
  font-family:'Playfair Display',serif; font-size:1.12rem; font-weight:600;
  font-variant-numeric:tabular-nums; color:var(--ink);
}
.cab-rev .org{ font-size:.73rem; color:var(--muted); text-align:right; }
.cli-rev{ font-size:.82rem; color:var(--muted); margin:.32rem 0 .85rem; }

.trecho{
  background:rgba(245,158,11,.08); border-left:3px solid var(--atencao); border-radius:6px;
  padding:.6rem .8rem; margin-bottom:.85rem;
}
.trecho b{
  display:block; font-size:.6rem; letter-spacing:.12em; text-transform:uppercase;
  color:#FCD34D; margin-bottom:.26rem; font-weight:700;
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
    marca = (f'<span class="selo" style="color:{cor}">{_seguro(selo)}</span>' if selo else "")
    return _uma_linha(f"""
<div class="linha">
  <div class="conta" style="color:{cor}">
    <span class="num">{_seguro(numero)}</span><span class="un">{_seguro(unidade)}</span>
  </div>
  <div class="corpo">
    <div class="ato">{_seguro(ato)}{marca}</div>
    <div class="cliente">{_seguro(cliente)}</div>
    <div class="meta">{_seguro(meta)}</div>
  </div>
</div>""")


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
        pe.append(f'<span><span class="ms">account_balance</span>{_seguro(orgao)}</span>')
    if fatal:
        pe.append(f'<span><span class="ms">schedule</span>Fatal: <b>{_seguro(fatal)}</b></span>')
    if interno:
        pe.append(f'<span>Preparar até {_seguro(interno)}</span>')
    rodape = f'<div class="cartao-pe">{"".join(pe)}</div>' if pe else ""

    cliente = p.get("cliente") or ""
    linha_cliente = f'<div class="cliente">{_seguro(cliente)}</div>' if cliente else ""

    return _uma_linha(f"""
<div class="cartao">
  <div class="cartao-topo">
    <div class="cartao-info">
      {etiquetas_do_prazo(p)}
      <div class="ato">{_seguro(p.get("ato") or "Prazo")}</div>
      <div class="proc">{_seguro(processo)}</div>
      {linha_cliente}
    </div>
    <div class="contagem ct-{tom}">
      <span class="n">{_seguro(numero)}</span><span class="u">{_seguro(unidade)}</span>
    </div>
  </div>
  {rodape}
</div>""")


def tom_por_dias(n) -> str:
    """Traduz dias úteis restantes no tom da caixa de contagem."""
    if n is None:
        return "neutro"
    if n <= 2:
        return "urgente"
    if n <= 5:
        return "atencao"
    return "calmo"
