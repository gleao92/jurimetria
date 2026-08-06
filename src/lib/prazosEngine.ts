import { AreaProcesso } from '../types';

export const MARGEM_SEGURANCA_DIAS = 3;
export const CRIMINAL_CONTA_DA_PUBLICACAO = false;
export const CRIMINAL_SUSPENDE_NO_RECESSO = false;

export const FERIADOS_NACIONAIS_FIXOS: Record<string, string> = {
  '01-01': 'Confraternização Universal',
  '04-21': 'Tiradentes',
  '05-01': 'Dia do Trabalho',
  '09-07': 'Independência',
  '10-12': 'Nossa Senhora Aparecida',
  '11-02': 'Finados',
  '11-15': 'Proclamação da República',
  '11-20': 'Consciência Negra',
  '12-25': 'Natal',
};

// Meeus/Jones/Butcher Easter calculation algorithm
export function pascoa(ano: number): Date {
  const a = ano % 19;
  const b = Math.floor(ano / 100);
  const c = ano % 100;
  const d = Math.floor(b / 4);
  const e = b % 4;
  const f = Math.floor((b + 8) / 25);
  const g = Math.floor((b - f + 1) / 3);
  const h = (19 * a + b - d - g + 15) % 30;
  const i = Math.floor(c / 4);
  const k = c % 4;
  const l = (32 + 2 * e + 2 * i - h - k) % 7;
  const m = Math.floor((a + 11 * h + 22 * l) / 451);
  const mes = Math.floor((h + l - 7 * m + 114) / 31);
  const dia = ((h + l - 7 * m + 114) % 31) + 1;
  return new Date(ano, mes - 1, dia);
}

function addDays(d: Date, days: number): Date {
  const res = new Date(d);
  res.setDate(res.getDate() + days);
  return res;
}

function formatDateKey(d: Date): string {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${y}-${m}-${day}`;
}

export function feriadosMoveis(ano: number, incluirQuartaCinzas: boolean = false): Record<string, string> {
  const p = pascoa(ano);
  const fer: Record<string, string> = {
    [formatDateKey(addDays(p, -48))]: 'Carnaval (segunda)',
    [formatDateKey(addDays(p, -47))]: 'Carnaval (terça)',
    [formatDateKey(addDays(p, -2))]: 'Sexta-feira Santa',
    [formatDateKey(addDays(p, 60))]: 'Corpus Christi',
  };
  if (incluirQuartaCinzas) {
    fer[formatDateKey(addDays(p, -46))] = 'Quarta-feira de Cinzas';
  }
  return fer;
}

export function feriadosDoAno(ano: number, feriadosLocais: Record<string, string> = {}): Record<string, string> {
  const fer: Record<string, string> = {};

  // Fixed holidays
  Object.entries(FERIADOS_NACIONAIS_FIXOS).forEach(([mmdd, nome]) => {
    fer[`${ano}-${mmdd}`] = nome;
  });

  // Movable holidays
  Object.assign(fer, feriadosMoveis(ano));

  // Local holidays for that year
  Object.entries(feriadosLocais).forEach(([dateStr, nome]) => {
    if (dateStr.startsWith(`${ano}-`)) {
      fer[dateStr] = nome;
    }
  });

  return fer;
}

export function nomeDoFeriado(d: Date, feriadosLocais: Record<string, string> = {}): string | undefined {
  const key = formatDateKey(d);
  return feriadosDoAno(d.getFullYear(), feriadosLocais)[key];
}

export function ehDiaUtil(d: Date, feriadosLocais: Record<string, string> = {}): boolean {
  const dayOfWeek = d.getDay(); // 0 is Sunday, 6 is Saturday
  if (dayOfWeek === 0 || dayOfWeek === 6) return false;
  const key = formatDateKey(d);
  return !feriadosDoAno(d.getFullYear(), feriadosLocais)[key];
}

export function emRecessoForense(d: Date): boolean {
  const month = d.getMonth() + 1;
  const day = d.getDate();
  return (month === 12 && day >= 20) || (month === 1 && day <= 20);
}

function bloqueado(d: Date, suspendeRecesso: boolean, feriadosLocais: Record<string, string> = {}): boolean {
  return !ehDiaUtil(d, feriadosLocais) || (suspendeRecesso && emRecessoForense(d));
}

export function proximoDiaUtil(d: Date, suspendeRecesso: boolean = true, feriadosLocais: Record<string, string> = {}): Date {
  let curr = addDays(d, 1);
  while (bloqueado(curr, suspendeRecesso, feriadosLocais)) {
    curr = addDays(curr, 1);
  }
  return curr;
}

export function diasUteisEntre(inicio: Date, fim: Date, suspendeRecesso: boolean = true, feriadosLocais: Record<string, string> = {}): number {
  if (fim <= inicio) return 0;
  let count = 0;
  let curr = new Date(inicio);
  while (curr < fim) {
    curr = addDays(curr, 1);
    if (!bloqueado(curr, suspendeRecesso, feriadosLocais)) {
      count++;
    }
  }
  return count;
}

export function recuarDiasUteis(d: Date, n: number, suspendeRecesso: boolean = true, feriadosLocais: Record<string, string> = {}): Date {
  let curr = new Date(d);
  for (let i = 0; i < n; i++) {
    curr = addDays(curr, -1);
    while (bloqueado(curr, suspendeRecesso, feriadosLocais)) {
      curr = addDays(curr, -1);
    }
  }
  return curr;
}

export interface ResultadoCalculo {
  area: AreaProcesso;
  disponibilizacao: Date;
  publicacao: Date;
  inicio_contagem: Date;
  data_fatal: Date;
  prazo_interno: Date;
  contagem: string;
}

export function calcularPrazo(
  dataBase: Date,
  prazoDias: number,
  areaInput: AreaProcesso = 'civel',
  margem: number = MARGEM_SEGURANCA_DIAS,
  contagemForcada: '' | 'uteis' | 'corridos' = '',
  tipoData: 'disponibilizacao' | 'publicacao' = 'disponibilizacao',
  feriadosLocais: Record<string, string> = {}
): ResultadoCalculo {
  let area: AreaProcesso = areaInput === 'a_confirmar' ? 'civel' : areaInput;

  if (contagemForcada === 'uteis') {
    area = 'civel';
  } else if (contagemForcada === 'corridos') {
    area = 'criminal';
  }

  const jaPublicada = tipoData === 'publicacao';
  let publicacao: Date;
  let inicio: Date;
  let fatal: Date;
  let contagem: string;
  let susp: boolean;

  if (area === 'criminal') {
    susp = CRIMINAL_SUSPENDE_NO_RECESSO;
    if (jaPublicada || !CRIMINAL_CONTA_DA_PUBLICACAO) {
      publicacao = new Date(dataBase);
    } else {
      publicacao = proximoDiaUtil(dataBase, susp, feriadosLocais);
    }
    inicio = addDays(publicacao, 1);
    fatal = addDays(inicio, prazoDias - 1);
    while (bloqueado(fatal, susp, feriadosLocais)) {
      fatal = addDays(fatal, 1);
    }
    contagem = 'dias corridos (CPP art. 798)';
  } else {
    susp = true;
    publicacao = jaPublicada ? new Date(dataBase) : proximoDiaUtil(dataBase, susp, feriadosLocais);
    inicio = proximoDiaUtil(publicacao, susp, feriadosLocais);
    fatal = new Date(inicio);
    let contados = 1;
    while (contados < prazoDias) {
      fatal = proximoDiaUtil(fatal, susp, feriadosLocais);
      contados++;
    }
    contagem = 'dias úteis (CPC art. 219)';
  }

  const prazoInterno = recuarDiasUteis(fatal, margem, susp, feriadosLocais);

  return {
    area,
    disponibilizacao: new Date(dataBase),
    publicacao,
    inicio_contagem: inicio,
    data_fatal: fatal,
    prazo_interno: prazoInterno,
    contagem,
  };
}

export function calcularUrgencia(prazo: { data_fatal: string; status: string }, hoje: Date = new Date()) {
  const fatalDate = new Date(prazo.data_fatal + 'T00:00:00');
  const hojeDate = new Date(hoje.getFullYear(), hoje.getMonth(), hoje.getDate());
  
  const diffDays = Math.ceil((fatalDate.getTime() - hojeDate.getTime()) / (1000 * 60 * 60 * 24));
  
  if (prazo.status === 'cumprido') {
    return { num: '✓', un: 'cumprido', cor: 'slate', selo: 'cumprido', dias: 999 };
  }

  if (diffDays < 0) {
    return { num: Math.abs(diffDays).toString(), un: Math.abs(diffDays) === 1 ? 'dia vencido' : 'dias vencidos', cor: 'red', selo: 'vencido', dias: diffDays };
  } else if (diffDays === 0) {
    return { num: '0', un: 'hoje!', cor: 'red', selo: 'vence hoje', dias: 0 };
  } else if (diffDays === 1) {
    return { num: '1', un: 'dia útil', cor: 'orange', selo: 'vence amanhã', dias: 1 };
  } else {
    return { num: diffDays.toString(), un: 'dias', cor: diffDays <= 3 ? 'amber' : 'emerald', selo: `em ${diffDays} dias`, dias: diffDays };
  }
}
