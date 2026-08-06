export type Role = 'advogado' | 'apoio';

export interface User {
  id: string;
  usuario: string;
  nome: string;
  papel: Role;
}

export type AreaProcesso = 'civel' | 'criminal' | 'a_confirmar';

export interface Processo {
  numero: string;
  cliente: string;
  area: AreaProcesso;
  sistema: string;
  tribunal: string;
  assunto: string;
}

export interface Publicacao {
  id: string;
  processo: string;
  sistema: string;
  orgao: string;
  data_disponibilizacao: string; // ISO format YYYY-MM-DD
  teor: string;
}

export type StatusPrazo = 'pendente_revisao' | 'confirmado' | 'cumprido';

export interface Prazo {
  id: string;
  publicacao_id?: string;
  processo: string;
  cliente: string;
  tribunal: string;
  orgao: string;
  ato: string;
  area: AreaProcesso;
  data_disponibilizacao: string; // YYYY-MM-DD
  publicacao: string; // YYYY-MM-DD
  inicio_contagem: string; // YYYY-MM-DD
  data_fatal: string; // YYYY-MM-DD
  prazo_interno: string; // YYYY-MM-DD
  dias_prazo: number;
  status: StatusPrazo;
  confirmado_por?: string;
  confirmado_em?: string;
  cumprido_por?: string;
  cumprido_em?: string;
  observacoes?: string;
  teor?: string;
  contagem_explicacao?: string;
}

export type TipoCompromisso = 'audiencia' | 'reuniao' | 'diligencia' | 'outro';

export interface Compromisso {
  id: string;
  titulo: string;
  tipo: TipoCompromisso;
  data: string; // YYYY-MM-DD
  hora?: string; // HH:mm
  local?: string;
  processo?: string;
  cliente?: string;
  observacoes?: string;
}

export interface Regra {
  id: string;
  padrao: string;
  rotulo: string;
  dias: number | null;
  ativa: boolean;
}

export interface FeriadoLocal {
  data: string; // YYYY-MM-DD
  nome: string;
}

export interface Configuracao {
  oab_numero: string;
  oab_uf: string;
  fonte: 'djen' | 'mni' | 'ambas';
  conectada: boolean;
  area_padrao: 'conservadora' | 'civel' | 'criminal';
  mni_usuario: string;
  mni_senha: string;
  mni_wsdl: string;
}

export interface LogEntry {
  id: string;
  quando: string; // YYYY-MM-DD HH:mm:ss
  acao: string;
  quem: string;
  detalhe: string;
}
