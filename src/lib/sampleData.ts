import { Processo, Publicacao, Compromisso } from '../types';

function getDaysAgoStr(days: number): string {
  const d = new Date();
  d.setDate(d.getDate() - days);
  return d.toISOString().split('T')[0];
}

function getDaysAheadStr(days: number): string {
  const d = new Date();
  d.setDate(d.getDate() + days);
  return d.toISOString().split('T')[0];
}

export const PROCESSOS_EXEMPLO: Processo[] = [
  {
    numero: '1002345-67.2026.8.09.0051',
    cliente: 'Fazenda Boa Vista Ltda.',
    area: 'civel',
    sistema: 'PJe',
    tribunal: 'TJGO',
    assunto: 'Ação de cobrança',
  },
  {
    numero: '5001234-12.2026.4.01.3500',
    cliente: 'João Pereira da Silva',
    area: 'civel',
    sistema: 'eproc',
    tribunal: 'TRF1',
    assunto: 'Usucapião rural',
  },
  {
    numero: '0007654-32.2026.8.09.0100',
    cliente: 'Marcos A. de Souza',
    area: 'criminal',
    sistema: 'PJe',
    tribunal: 'TJGO',
    assunto: 'Ação penal',
  },
  {
    numero: '1005678-90.2026.8.26.0053',
    cliente: 'Agropecuária Rio Verde S/A',
    area: 'civel',
    sistema: 'eSAJ',
    tribunal: 'TJSP',
    assunto: 'Servidão de passagem',
  },
  {
    numero: '0003210-45.2026.8.09.0175',
    cliente: 'Antônio C. Ferreira',
    area: 'criminal',
    sistema: 'eproc',
    tribunal: 'TJGO',
    assunto: 'Queixa-crime',
  },
  {
    numero: '1009876-54.2026.8.09.0051',
    cliente: 'Sítio Três Marias',
    area: 'civel',
    sistema: 'PJe',
    tribunal: 'TJGO',
    assunto: 'Reintegração de posse',
  },
];

export const PUBLICACOES_EXEMPLO: Publicacao[] = [
  {
    id: 'pub1',
    processo: '0007654-32.2026.8.09.0100',
    sistema: 'PJe',
    orgao: '2ª Vara Criminal de Goiânia',
    data_disponibilizacao: getDaysAgoStr(7),
    teor: 'PODER JUDICIÁRIO DO ESTADO DE GOIÁS 2ª Vara Criminal de Goiânia. Autos nº 0007654-32.2026.8.09.0100. Recebida a denúncia oferecida pelo Ministério Público, cite-se o acusado para apresentar RESPOSTA À ACUSAÇÃO, por escrito, no prazo de 10 (dez) dias, nos termos do art. 396 do Código de Processo Penal, podendo arguir preliminares e alegar tudo o que interesse à sua defesa.',
  },
  {
    id: 'pub2',
    processo: '1002345-67.2026.8.09.0051',
    sistema: 'PJe',
    orgao: 'Goiânia - 3ª UPJ Varas Cíveis: 6ª Vara Cível',
    data_disponibilizacao: getDaysAgoStr(1),
    teor: 'Trata-se de ação de cobrança. Cite-se a parte requerida para, querendo, apresentar contestação no prazo de 15 (quinze) dias úteis, sob pena de revelia e confissão quanto à matéria de fato, nos termos dos arts. 335 e 344 do CPC.',
  },
  {
    id: 'pub3',
    processo: '1005678-90.2026.8.26.0053',
    sistema: 'eSAJ',
    orgao: 'Vara da Fazenda Pública',
    data_disponibilizacao: getDaysAgoStr(6),
    teor: 'Vistos. Manifeste-se a parte autora, no prazo de 15 (quinze) dias, sobre a contestação e os documentos que a acompanham, especificando as provas que pretende produzir, justificando a pertinência de cada uma.',
  },
  {
    id: 'pub4',
    processo: '5001234-12.2026.4.01.3500',
    sistema: 'eproc',
    orgao: '15ª Vara Federal de Juizado Especial Cível',
    data_disponibilizacao: getDaysAgoStr(3),
    teor: 'ATO ORDINATÓRIO (art. 203, § 4º do CPC). Trata-se de ação em que a parte autora pretende a concessão de benefício por incapacidade temporária em face do INSS – Instituto Nacional do Seguro Social. Fica a parte autora intimada para juntar aos autos, no prazo de 15 (quinze) dias, sob pena de indeferimento da petição inicial, os documentos necessários à propositura da demanda.',
  },
  {
    id: 'pub5',
    processo: '0003210-45.2026.8.09.0175',
    sistema: 'eproc',
    orgao: 'Vara Criminal de Aparecida de Goiânia',
    data_disponibilizacao: getDaysAgoStr(2),
    teor: 'Encerrada a instrução processual, intimem-se as partes para apresentação de ALEGAÇÕES FINAIS por memoriais, no prazo sucessivo de 5 (cinco) dias, iniciando-se pela acusação.',
  },
  {
    id: 'pub6',
    processo: '1009876-54.2026.8.09.0051',
    sistema: 'PJe',
    orgao: 'Goiânia - 3ª UPJ Varas Cíveis: 6ª Vara Cível',
    data_disponibilizacao: getDaysAgoStr(1),
    teor: 'Sentença publicada em audiência. Julgo procedente o pedido inicial. Ficam as partes intimadas do teor da sentença, correndo o prazo de 15 (quinze) dias para eventual recurso de apelação, na forma do art. 1.003 do CPC.',
  },
  {
    id: 'pub7',
    processo: '1002345-67.2026.8.09.0051',
    sistema: 'PJe',
    orgao: 'Goiânia - 3ª UPJ Varas Cíveis: 6ª Vara Cível',
    data_disponibilizacao: getDaysAgoStr(4),
    teor: 'Certifico que os autos foram remetidos à contadoria judicial para elaboração dos cálculos. Nada mais.',
  },
];

export const COMPROMISSOS_EXEMPLO: Compromisso[] = [
  {
    id: 'comp1',
    titulo: 'Audiência de Instrução e Julgamento',
    tipo: 'audiencia',
    data: getDaysAheadStr(1),
    hora: '14:00',
    local: 'Fórum de Goiânia - Sala 204',
    processo: '0007654-32.2026.8.09.0100',
    cliente: 'Marcos A. de Souza',
    observacoes: 'Levar testemunhas confirmadas.',
  },
  {
    id: 'comp2',
    titulo: 'Reunião com o cliente',
    tipo: 'reuniao',
    data: getDaysAheadStr(3),
    hora: '10:30',
    local: 'Escritório / Presencial',
    processo: '1002345-67.2026.8.09.0051',
    cliente: 'Fazenda Boa Vista Ltda.',
    observacoes: 'Apresentação de estratégia de defesa em réplica.',
  },
];
