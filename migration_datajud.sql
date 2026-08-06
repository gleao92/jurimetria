-- Tempestivo :: integração DataJud
-- Migração ADITIVA. Nenhuma tabela existente é alterada.
-- Ajustar apenas o REFERENCES abaixo para o nome real da sua tabela de processos.

create table if not exists datajud_capas (
  processo_id        uuid primary key references processos(id) on delete cascade,
  numero             text not null,
  tribunal           text,
  grau               text,
  classe             text,
  assuntos           jsonb default '[]'::jsonb,
  orgao_julgador     text,
  data_ajuizamento   timestamptz,
  ultima_atualizacao timestamptz,
  sincronizado_em    timestamptz default now()
);

create table if not exists datajud_movimentos (
  id           uuid primary key default gen_random_uuid(),
  processo_id  uuid not null references processos(id) on delete cascade,
  chave        text not null,
  codigo       integer not null,
  nome         text not null,
  data_hora    timestamptz not null,
  relevancia   text not null default 'rotina'
               check (relevancia in ('rotina','relevante','atencao')),
  complementos jsonb default '[]'::jsonb,
  visto_em     timestamptz,
  criado_em    timestamptz default now(),
  unique (processo_id, chave)
);

-- O unique acima é o que torna a sincronização idempotente. Sem ele,
-- cada execução duplicaria o histórico inteiro do processo.

create index if not exists idx_datajud_mov_processo
  on datajud_movimentos (processo_id, data_hora desc);

create index if not exists idx_datajud_mov_atencao
  on datajud_movimentos (relevancia, data_hora desc)
  where relevancia = 'atencao';

create index if not exists idx_datajud_capas_sync
  on datajud_capas (sincronizado_em);
