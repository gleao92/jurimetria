import React from 'react';
import { Prazo } from '../types';
import { calcularUrgencia, ehDiaUtil, nomeDoFeriado } from '../lib/prazosEngine';
import { ShieldAlert, AlertTriangle, CheckCircle, Clock } from 'lucide-react';

interface HeaderProps {
  tela: string;
  prazos: Prazo[];
  fonteConectada: boolean;
}

const TITULOS: Record<string, [string, string]> = {
  hoje: ['Hoje', 'O que precisa da sua atenção agora.'],
  agenda: ['Agenda', 'Prazos e compromissos no calendário.'],
  prazos: ['Prazos', 'Todos os prazos, com filtros e exportação.'],
  processos: ['Processos', 'Sua carteira e a área de contagem de cada um.'],
  ajustes: ['Ajustes', 'Fonte das publicações, regras e feriados.'],
};

const DIAS_PT = ['Segunda-feira', 'Terça-feira', 'Quarta-feira', 'Quinta-feira', 'Sexta-feira', 'Sábado', 'Domingo'];
const MESES_PT = [
  'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
  'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'
];

export const Header: React.FC<HeaderProps> = ({ tela, prazos, fonteConectada }) => {
  const hoje = new Date();
  const dayOfWeek = hoje.getDay() === 0 ? 6 : hoje.getDay() - 1;
  const diaNome = DIAS_PT[dayOfWeek];
  const diaNum = hoje.getDate();
  const mesNome = MESES_PT[hoje.getMonth()];
  const ano = hoje.getFullYear();

  const feriado = nomeDoFeriado(hoje);
  const statusDia = feriado
    ? feriado
    : ehDiaUtil(hoje)
    ? 'dia útil'
    : 'sem expediente';

  const [titulo, subtitulo] = TITULOS[tela] || ['Tempestivo', 'Controladoria de Prazos'];

  const ativos = prazos.filter((p) => p.status !== 'cumprido');
  const revisar = ativos.filter((p) => p.status === 'pendente_revisao');
  const confirmados = ativos.filter((p) => p.status === 'confirmado');

  const criticos = ativos.filter((p) => {
    const u = calcularUrgencia(p, hoje);
    return u.dias >= 0 && u.dias <= 2;
  });

  const vencidos = ativos.filter((p) => {
    const u = calcularUrgencia(p, hoje);
    return u.dias < 0;
  });

  return (
    <header className="mb-6">
      {/* Top Title Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-slate-800 gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold font-serif text-slate-50 tracking-tight">
            {titulo}
          </h1>
          <p className="text-sm text-slate-400 mt-0.5">{subtitulo}</p>
        </div>
        <div className="text-right sm:border-l sm:border-slate-800 sm:pl-6">
          <div className="text-sm font-semibold text-amber-300">
            {diaNome}, {diaNum} de {mesNome} de {ano}
          </div>
          <div className="text-xs text-slate-400 mt-0.5 uppercase tracking-wider font-medium">
            {statusDia}
          </div>
        </div>
      </div>

      {/* Metrics Bar (if not in settings) */}
      {tela !== 'ajustes' && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-4">
          <div className="bg-slate-800/80 border border-slate-700/60 rounded-xl p-3.5 flex flex-col justify-between">
            <span className="text-xs font-medium text-slate-400 flex items-center gap-1.5">
              <Clock className="w-3.5 h-3.5 text-blue-400" /> a revisar
            </span>
            <span className="text-2xl font-bold text-blue-400 mt-1">{revisar.length}</span>
          </div>

          <div className="bg-slate-800/80 border border-slate-700/60 rounded-xl p-3.5 flex flex-col justify-between">
            <span className="text-xs font-medium text-slate-400 flex items-center gap-1.5">
              <CheckCircle className="w-3.5 h-3.5 text-emerald-400" /> confirmados
            </span>
            <span className="text-2xl font-bold text-emerald-400 mt-1">{confirmados.length}</span>
          </div>

          <div className="bg-slate-800/80 border border-slate-700/60 rounded-xl p-3.5 flex flex-col justify-between">
            <span className="text-xs font-medium text-slate-400 flex items-center gap-1.5">
              <AlertTriangle className="w-3.5 h-3.5 text-amber-400" /> vencem em ≤ 2 dias
            </span>
            <span className="text-2xl font-bold text-amber-400 mt-1">{criticos.length}</span>
          </div>

          <div className="bg-slate-800/80 border border-slate-700/60 rounded-xl p-3.5 flex flex-col justify-between">
            <span className="text-xs font-medium text-slate-400 flex items-center gap-1.5">
              <ShieldAlert className="w-3.5 h-3.5 text-rose-400" /> vencidos
            </span>
            <span className="text-2xl font-bold text-rose-400 mt-1">{vencidos.length}</span>
          </div>
        </div>
      )}


    </header>
  );
};
