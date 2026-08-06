import { Regra } from '../types';

export const REGRAS_PADRAO: Regra[] = [
  { id: '1', padrao: 'resposta à acusação', rotulo: 'Resposta à Acusação', dias: 10, ativa: true },
  { id: '2', padrao: 'resposta a acusacao', rotulo: 'Resposta à Acusação', dias: 10, ativa: true },
  { id: '3', padrao: 'contestação', rotulo: 'Contestação', dias: 15, ativa: true },
  { id: '4', padrao: 'contestacao', rotulo: 'Contestação', dias: 15, ativa: true },
  { id: '5', padrao: 'apelação', rotulo: 'Apelação', dias: 15, ativa: true },
  { id: '6', padrao: 'apelacao', rotulo: 'Apelação', dias: 15, ativa: true },
  { id: '7', padrao: 'alegações finais', rotulo: 'Alegações Finais', dias: 5, ativa: true },
  { id: '8', padrao: 'alegacoes finais', rotulo: 'Alegações Finais', dias: 5, ativa: true },
  { id: '9', padrao: 'embargos de declaração', rotulo: 'Embargos de Declaração', dias: 5, ativa: true },
  { id: '10', padrao: 'embargos de declaracao', rotulo: 'Embargos de Declaração', dias: 5, ativa: true },
  { id: '11', padrao: 'agravo de instrumento', rotulo: 'Agravo de Instrumento', dias: 15, ativa: true },
  { id: '12', padrao: 'recurso inominado', rotulo: 'Recurso Inominado', dias: 10, ativa: true },
  { id: '13', padrao: 'impugnação', rotulo: 'Impugnação / Réplica', dias: 15, ativa: true },
  { id: '14', padrao: 'impugnacao', rotulo: 'Impugnação / Réplica', dias: 15, ativa: true },
  { id: '15', padrao: 'especificação de provas', rotulo: 'Especificação de Provas', dias: 5, ativa: true },
  { id: '16', padrao: 'especificacao de provas', rotulo: 'Especificação de Provas', dias: 5, ativa: true },
];

export function extrairPrazoTextual(teor: string): number | null {
  if (!teor) return null;
  const texto = teor.toLowerCase();

  // Pattern 1: prazo de X (...) dias or prazo de X dias
  const match1 = texto.match(/prazo\s+de\s+(\d+)\s*(?:\([^)]*\))?\s*dias?/i);
  if (match1) {
    return parseInt(match1[1], 10);
  }

  // Pattern 2: no prazo de X (...) dias
  const match2 = texto.match(/no\s+prazo\s+de\s+(\d+)\s*dias?/i);
  if (match2) {
    return parseInt(match2[1], 10);
  }

  // Pattern 3: X (extenso) dias
  const match3 = texto.match(/(\d+)\s*\([a-z\s]+\)\s*dias?/i);
  if (match3) {
    return parseInt(match3[1], 10);
  }

  return null;
}

export function classificarPublicacao(
  teor: string,
  regras: Regra[] = REGRAS_PADRAO
): { ato: string; dias: number; contagemForcada: '' | 'uteis' | 'corridos' } {
  if (!teor) {
    return { ato: 'A IDENTIFICAR', dias: 15, contagemForcada: '' };
  }

  const texto = teor.toLowerCase();

  // Check forced count in text
  let contagemForcada: '' | 'uteis' | 'corridos' = '';
  if (texto.includes('dias úteis') || texto.includes('dias uteis')) {
    contagemForcada = 'uteis';
  } else if (texto.includes('dias corridos')) {
    contagemForcada = 'corridos';
  }

  // Check explicit extracted deadline in text first
  const diasExtraidos = extrairPrazoTextual(teor);

  // Check matching rule
  const regrasAtivas = regras.filter((r) => r.ativa);
  for (const r of regrasAtivas) {
    if (texto.includes(r.padrao.toLowerCase())) {
      return {
        ato: r.rotulo,
        dias: diasExtraidos ?? r.dias ?? 15,
        contagemForcada,
      };
    }
  }

  if (diasExtraidos) {
    return {
      ato: 'Intimação / Providência',
      dias: diasExtraidos,
      contagemForcada,
    };
  }

  return {
    ato: 'A IDENTIFICAR',
    dias: 15,
    contagemForcada,
  };
}
