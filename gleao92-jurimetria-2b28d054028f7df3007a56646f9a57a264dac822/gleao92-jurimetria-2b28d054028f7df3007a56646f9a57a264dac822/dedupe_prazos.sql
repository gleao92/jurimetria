-- Tempestivo :: duplicidade de prazos
-- Rodar bloco a bloco, na ordem. Ler o resultado de cada um antes de seguir.

-- =====================================================================
-- 1. DIAGNOSTICO (somente leitura) -- ha duplicata?
-- =====================================================================

select count(*) as total_prazos,
       count(distinct publicacao_id) as publicacoes_distintas,
       count(*) - count(distinct publicacao_id) as excedente
  from prazos;

-- Se "excedente" for 0, NAO ha duplicata. Pare aqui.


-- =====================================================================
-- 2. QUAIS estao duplicados, e como diferem
-- =====================================================================

select publicacao_id,
       count(*)                       as vezes,
       string_agg(distinct ato, ' | ')    as atos,
       string_agg(distinct status, ' | ') as status,
       min(criado_em)                 as primeiro,
       max(criado_em)                 as ultimo
  from prazos
 group by publicacao_id
having count(*) > 1
 order by vezes desc, publicacao_id;


-- =====================================================================
-- 3. BACKUP antes de apagar qualquer coisa
-- =====================================================================

create table if not exists prazos_backup_dedupe as
select *, now() as backup_em from prazos;

select count(*) as linhas_no_backup from prazos_backup_dedupe;


-- =====================================================================
-- 4. LIMPEZA -- mantem UMA linha por publicacao
--
-- Criterio de escolha, nesta ordem:
--   a) prazo ja confirmado pelo advogado vence sempre (decisao humana)
--   b) entre os demais, fica o mais ANTIGO (preserva o historico original)
--
-- Rodar primeiro o SELECT para ver o que SERIA apagado.
-- =====================================================================

with ranqueado as (
  select id, publicacao_id, ato, status, criado_em,
         row_number() over (
           partition by publicacao_id
           order by case when status = 'pendente_revisao' then 1 else 0 end,
                    criado_em,
                    id
         ) as posicao
    from prazos
)
select * from ranqueado where posicao > 1 order by publicacao_id;

-- Conferiu? Entao apague:

with ranqueado as (
  select id,
         row_number() over (
           partition by publicacao_id
           order by case when status = 'pendente_revisao' then 1 else 0 end,
                    criado_em,
                    id
         ) as posicao
    from prazos
)
delete from prazos
 where id in (select id from ranqueado where posicao > 1);


-- =====================================================================
-- 5. VERIFICACAO
-- =====================================================================

select count(*) as total_prazos,
       count(distinct publicacao_id) as publicacoes_distintas
  from prazos;
-- Os dois numeros devem ser iguais agora.

select ato, count(*) from prazos group by ato order by 2 desc;


-- =====================================================================
-- 6. TRAVA no banco -- impede que volte a acontecer
--
-- Com este indice, uma segunda insercao para a mesma publicacao falha
-- no banco, independente do que o codigo Python decida. E a garantia
-- que nao depende de ninguem lembrar da regra.
--
-- So funciona DEPOIS que o passo 4 zerou as duplicatas.
-- =====================================================================

create unique index if not exists ux_prazos_publicacao
    on prazos (publicacao_id);


-- Se precisar desfazer tudo:
--   drop index if exists ux_prazos_publicacao;
--   delete from prazos;
--   insert into prazos select id, publicacao_id, processo, area, ato,
--          prazo_dias, data_fatal, prazo_interno, status, fonte,
--          confirmado_por, confirmado_em, cumprido_em, observacao,
--          criado_em, trecho from prazos_backup_dedupe;
