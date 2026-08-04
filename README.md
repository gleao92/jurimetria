# Tempestivo

*Controladoria de prazos processuais.*

Controle de prazos processuais para advogado (cível / criminal / rural).
Captura publicação → sugere o ato e o prazo → **advogado confirma** → acompanha
até o cumprimento, com trilha de auditoria.

## Rodar

```bash
pip install -r requirements.txt
python -m streamlit run app.py
```

Sem fonte real conectada, clique em **"Carregar carteira de exemplo"** na barra
lateral para ver o fluxo inteiro funcionando.

Antes de confiar no motor de prazos:

```bash
python test_prazos.py     # 31 testes; se algum falhar, NÃO use
```

## Arquivos

```
app.py             painel (revisão, alertas, carteira, auditoria)
prazos.py          motor de cálculo — CRÍTICO
feriados_local.py  feriados forenses do TJGO — VOCÊ PRECISA PREENCHER
classificacao.py   ato + prazo a partir do teor (onde a IA entra)
pipeline.py        publicação → classificação → prazo → banco
db.py              persistência SQLite + log de auditoria
captura.py         captura genérica (STUB)
captura_djen.py    captura via DJEN — testar com a OAB real
dados_exemplo.py   carteira fictícia
test_prazos.py     testes do motor
controladoria.db   banco (criado no 1º uso) — FAÇA BACKUP
```

## O que mudou nesta versão

- **Persistência (SQLite).** Antes o sistema esquecia tudo a cada refresh.
  Agora guarda publicações, prazos e status — e dá para marcar "cumprido".
- **Revisão humana obrigatória.** Todo prazo nasce `pendente_revisao`. A
  classificação é SUGESTÃO; nada vale sem o advogado confirmar (art. 34 do
  EOAB / Resolução CNJ 615/2025). Fica registrado quem confirmou e quando.
- **Feriados móveis automáticos.** Carnaval, Sexta-feira Santa e Corpus Christi
  calculados a partir da Páscoa, para qualquer ano. Antes faltavam — e faltar
  feriado erra prazo.
- **Bug corrigido:** `dias_uteis_entre` ignorava o recesso enquanto o motor o
  respeitava. Prazos atravessando dezembro/janeiro mostravam contagem errada.
- **Prazo interno.** Além da data fatal, uma data-alvo 3 dias úteis antes
  (configurável em `prazos.py`). Controladoria séria trabalha com margem.
- **Publicação sem ato reconhecido não some.** Vira item "A IDENTIFICAR" na
  fila de revisão. Publicação ignorada em silêncio = prazo perdido.
- **Auditoria.** Log de tudo. Se um prazo for questionado, a prova está lá.
- **31 testes** no motor de prazos.

## Falta para produção

1. **Conectar a captura real** (`captura_djen.py`). Rode-o com a OAB 61423/GO e
   veja o JSON de verdade — inclusive se o **Projudi (criminal)** aparece no
   DJEN. É a resposta que decide o resto da arquitetura.
2. **Preencher `feriados_local.py`** com a portaria de feriados forenses do
   TJGO. Enquanto vazio, alguns prazos saem mais cedo que o real — seguro,
   porém apertado. **Nunca preencha de memória:** feriado a mais empurra a data
   fatal para depois da real e faz perder prazo.
3. **Rodar em paralelo** com o controle atual do advogado por algumas semanas.
   Só migre quando a captura bater 100%. Prazo perdido por bug = art. 32 do
   EOAB. Este não é um app onde erro é aceitável.

## Decisões de arquitetura

**Local-first, e por um motivo concreto: o advogado usa certificado A3 (token).**

A chave privada de um A3 nunca sai do token. Não dá para copiá-la para um
servidor — não é limitação de software, é o projeto do dispositivo. Isso
descarta, para este cliente, qualquer arquitetura de nuvem que assine ou
protocole peça sozinha. Se um dia houver peticionamento, ele roda na máquina
dele, com o token plugado.

**Mas o A3 não limita a controladoria.** A captura de publicações vem do DJEN
por número de OAB, sem certificado. A parte que gera o valor — os prazos — é
independente do token.

Daí sai a divisão recomendada:

| Camada | Onde roda | Precisa de certificado? |
|---|---|---|
| Captura de publicações (DJEN) | pode ser nuvem/n8n | não |
| Cálculo de prazo + alertas | junto da captura | não |
| Painel de revisão e confirmação | máquina do advogado | não |
| Protocolo/assinatura (futuro, fora de escopo) | **só** máquina dele, token plugado | sim (A3) |

**Ponto de atenção do local-first:** rodando só na máquina dele, o sistema só
captura quando a máquina está ligada. Para o piloto (30 dias em paralelo com o
controle atual) isso é aceitável — agende a captura no Agendador de Tarefas do
Windows. Para produção, mova a captura para a nuvem (ela não precisa de
certificado) e deixe o painel local. Aí o banco sai do SQLite para
Postgres/Supabase, porque passam a existir dois pontos de acesso.

**Não guarde o certificado do advogado.** Vale mesmo se um dia ele migrar para
A1: o certificado é pessoal, quem o tem pode assinar em nome dele. Fica com ele.
