import {
  User,
  Processo,
  Prazo,
  Compromisso,
  Regra,
  Configuracao,
  LogEntry,
  FeriadoLocal,
  AreaProcesso,
  Publicacao,
} from '../types';
import { PROCESSOS_EXEMPLO, PUBLICACOES_EXEMPLO, COMPROMISSOS_EXEMPLO } from './sampleData';
import { REGRAS_PADRAO, classificarPublicacao } from './extrator';
import { calcularPrazo } from './prazosEngine';

const STORAGE_KEY = 'tempestivo_data_v1';

export interface AppState {
  currentUser: User | null;
  users: User[];
  processos: Processo[];
  prazos: Prazo[];
  compromissos: Compromisso[];
  regras: Regra[];
  feriadosLocais: FeriadoLocal[];
  configuracao: Configuracao;
  logs: LogEntry[];
}

const DEFAULT_CONFIG: Configuracao = {
  oab_numero: '61423',
  oab_uf: 'GO',
  fonte: 'djen',
  conectada: false,
  area_padrao: 'conservadora',
  mni_usuario: '',
  mni_senha: '',
  mni_wsdl: '',
};

export const INITIAL_USER: User = {
  id: 'u1',
  usuario: 'fulano',
  nome: 'Dr. Fulano de Tal',
  papel: 'advogado',
};

function generateInitialPrazos(processos: Processo[], publicacoes: Publicacao[], feriadosLocaisMap: Record<string, string>): Prazo[] {
  const procMap = new Map(processos.map((p) => [p.numero, p]));

  return publicacoes.map((pub, idx) => {
    const proc = procMap.get(pub.processo);
    const areaProc: AreaProcesso = proc ? proc.area : 'a_confirmar';

    const { ato, dias, contagemForcada } = classificarPublicacao(pub.teor, REGRAS_PADRAO);

    const dataDisp = new Date(pub.data_disponibilizacao + 'T00:00:00');
    const calc = calcularPrazo(
      dataDisp,
      dias,
      areaProc === 'a_confirmar' ? 'civel' : areaProc,
      3,
      contagemForcada,
      'disponibilizacao',
      feriadosLocaisMap
    );

    const status = idx === 1 ? 'confirmado' : 'pendente_revisao';

    return {
      id: `pzp_${idx + 1}`,
      publicacao_id: pub.id,
      processo: pub.processo,
      cliente: proc?.cliente || 'não identificado',
      tribunal: proc?.tribunal || pub.sistema || 'TJGO',
      orgao: pub.orgao,
      ato,
      area: areaProc,
      data_disponibilizacao: pub.data_disponibilizacao,
      publicacao: calc.publicacao.toISOString().split('T')[0],
      inicio_contagem: calc.inicio_contagem.toISOString().split('T')[0],
      data_fatal: calc.data_fatal.toISOString().split('T')[0],
      prazo_interno: calc.prazo_interno.toISOString().split('T')[0],
      dias_prazo: dias,
      status,
      confirmado_por: status === 'confirmado' ? 'Dr. Fulano de Tal' : undefined,
      confirmado_em: status === 'confirmado' ? new Date().toISOString() : undefined,
      teor: pub.teor,
      contagem_explicacao: calc.contagem,
    };
  });
}

export function getInitialState(): AppState {
  try {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved) {
      const parsed = JSON.parse(saved);
      if (parsed && Array.isArray(parsed.processos) && Array.isArray(parsed.prazos)) {
        return parsed;
      }
    }
  } catch (e) {
    console.error('Failed to load from storage:', e);
  }

  const initialFeriadosLocaisMap: Record<string, string> = {};
  const prazos = generateInitialPrazos(PROCESSOS_EXEMPLO, PUBLICACOES_EXEMPLO, initialFeriadosLocaisMap);

  const initialLogs: LogEntry[] = [
    {
      id: 'l1',
      quando: new Date().toISOString().replace('T', ' ').substring(0, 19),
      acao: 'sistema_iniciado',
      quem: 'Sistema',
      detalhe: 'Carteira de exemplo carregada com 6 processos e 7 publicações',
    },
  ];

  return {
    currentUser: INITIAL_USER,
    users: [
      INITIAL_USER,
      { id: 'u2', usuario: 'assistente', nome: 'Maria Silva (Apoio)', papel: 'apoio' },
    ],
    processos: PROCESSOS_EXEMPLO,
    prazos,
    compromissos: COMPROMISSOS_EXEMPLO,
    regras: REGRAS_PADRAO,
    feriadosLocais: [],
    configuracao: DEFAULT_CONFIG,
    logs: initialLogs,
  };
}

export function saveState(state: AppState) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  } catch (e) {
    console.error('Failed to save to storage:', e);
  }
}
