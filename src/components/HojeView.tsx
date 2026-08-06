import React, { useState } from 'react';
import { Prazo, Compromisso, User, AreaProcesso } from '../types';
import { calcularUrgencia } from '../lib/prazosEngine';
import { ReviewPanel } from './ReviewPanel';
import {
  Clock,
  CheckCircle2,
  AlertTriangle,
  Calendar,
  User as UserIcon,
  Check,
  ChevronRight,
  ShieldCheck,
} from 'lucide-react';

interface HojeViewProps {
  prazos: Prazo[];
  compromissos: Compromisso[];
  currentUser: User;
  podeConfirmar: boolean;
  onConfirmPrazo: (id: string, updatedData: Partial<Prazo>) => void;
  onMarcarCumprido: (id: string) => void;
  onDeletePrazo: (id: string) => void;
  feriadosLocaisMap?: Record<string, string>;
}

export const HojeView: React.FC<HojeViewProps> = ({
  prazos,
  compromissos,
  currentUser,
  podeConfirmar,
  onConfirmPrazo,
  onMarcarCumprido,
  onDeletePrazo,
  feriadosLocaisMap = {},
}) => {
  const [openReviewId, setOpenReviewId] = useState<string | null>(null);

  const hoje = new Date();

  const ativos = prazos.filter((p) => p.status !== 'cumprido');
  const revisar = ativos.filter((p) => p.status === 'pendente_revisao');
  const confirmados = ativos.filter((p) => p.status === 'confirmado');

  const urgentes = confirmados
    .filter((p) => {
      const u = calcularUrgencia(p, hoje);
      return u.dias <= 5;
    })
    .sort((a, b) => new Date(a.data_fatal).getTime() - new Date(b.data_fatal).getTime());

  // Upcoming appointments in 7 days
  const proxCompromissos = compromissos.filter((c) => {
    const compDate = new Date(c.data + 'T00:00:00');
    const hojeStart = new Date(hoje.getFullYear(), hoje.getMonth(), hoje.getDate());
    const diffDays = Math.ceil((compDate.getTime() - hojeStart.getTime()) / (1000 * 60 * 60 * 24));
    return diffDays >= 0 && diffDays <= 7;
  });

  return (
    <div className="space-y-8">
      {/* 1. FILA DE REVISÃO */}
      {revisar.length > 0 && (
        <section className="space-y-4">
          <div className="flex items-center justify-between pb-2 border-b border-slate-800">
            <div className="flex items-center gap-2">
              <h2 className="text-sm font-bold uppercase tracking-wider text-amber-400">
                Fila de revisão
              </h2>
              <span className="bg-amber-500/20 text-amber-300 border border-amber-500/30 text-xs px-2 py-0.5 rounded-full font-semibold">
                {revisar.length}
              </span>
            </div>
            <span className="text-xs text-slate-400 hidden sm:inline">
              classificação sugerida — confirme antes de confiar na data
            </span>
          </div>

          {!podeConfirmar && (
            <div className="text-xs text-amber-300/80 italic">
              * A confirmação de prazos é restrita ao perfil de Advogado.
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {revisar.map((p) => {
              const u = calcularUrgencia(p, hoje);
              const isOpen = openReviewId === p.id;

              return (
                <div key={p.id} className="col-span-1">
                  <div
                    className={`bg-slate-800/90 border rounded-xl p-4 transition-all ${
                      isOpen
                        ? 'border-amber-500 ring-1 ring-amber-500/30'
                        : 'border-slate-700/70 hover:border-slate-600'
                    }`}
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="text-xs font-semibold text-amber-300 bg-amber-500/10 px-2 py-0.5 rounded border border-amber-500/20 truncate">
                            {p.ato}
                          </span>
                          <span className="text-[11px] text-slate-400 truncate">
                            {p.orgao || p.tribunal}
                          </span>
                        </div>
                        <h4 className="text-sm font-bold text-slate-100 mt-2 truncate">
                          {p.processo}
                        </h4>
                        <div className="text-xs text-slate-300 mt-0.5 truncate">
                          Cliente: <span className="font-medium text-slate-200">{p.cliente}</span>
                        </div>
                      </div>

                      {/* Urgency Badge */}
                      <div className="text-right shrink-0">
                        <div className="text-lg font-bold text-amber-400 leading-none">
                          {u.num} <span className="text-xs font-normal">{u.un}</span>
                        </div>
                        <div className="text-[10px] text-slate-400 mt-1">Fatal: {p.data_fatal}</div>
                      </div>
                    </div>

                    <div className="mt-4 pt-3 border-t border-slate-700/50 flex items-center justify-between">
                      <div className="text-[11px] text-slate-400">
                        Interno: <span className="text-amber-300 font-medium">{p.prazo_interno}</span>
                      </div>
                      <button
                        onClick={() => setOpenReviewId(isOpen ? null : p.id)}
                        disabled={!podeConfirmar}
                        className="px-3 py-1.5 bg-amber-500 hover:bg-amber-400 disabled:opacity-50 text-slate-950 font-bold text-xs rounded-lg flex items-center gap-1 transition-colors"
                      >
                        <ShieldCheck className="w-3.5 h-3.5" /> Revisar
                      </button>
                    </div>
                  </div>

                  {/* Open Review Panel underneath */}
                  {isOpen && (
                    <ReviewPanel
                      prazo={p}
                      podeConfirmar={podeConfirmar}
                      onConfirm={(id, updatedData) => {
                        onConfirmPrazo(id, updatedData);
                        setOpenReviewId(null);
                      }}
                      onDelete={(id) => {
                        onDeletePrazo(id);
                        setOpenReviewId(null);
                      }}
                      onClose={() => setOpenReviewId(null)}
                      feriadosLocaisMap={feriadosLocaisMap}
                    />
                  )}
                </div>
              );
            })}
          </div>
        </section>
      )}

      {/* 2. CONFIRMADOS VENCENDO */}
      {urgentes.length > 0 && (
        <section className="space-y-4">
          <div className="flex items-center justify-between pb-2 border-b border-slate-800">
            <div className="flex items-center gap-2">
              <h2 className="text-sm font-bold uppercase tracking-wider text-emerald-400">
                Confirmados, vencendo em breve
              </h2>
              <span className="bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 text-xs px-2 py-0.5 rounded-full font-semibold">
                {urgentes.length}
              </span>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {urgentes.map((p) => {
              const u = calcularUrgencia(p, hoje);

              return (
                <div
                  key={p.id}
                  className="bg-slate-800/80 border border-slate-700/70 rounded-xl p-4 flex flex-col justify-between"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-semibold text-emerald-300 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20 truncate">
                          {p.ato}
                        </span>
                        <span className="text-[11px] text-slate-400 truncate">{p.tribunal}</span>
                      </div>
                      <h4 className="text-sm font-bold text-slate-100 mt-2 truncate">
                        {p.processo}
                      </h4>
                      <div className="text-xs text-slate-300 mt-0.5 truncate">
                        Cliente: <span className="font-medium text-slate-200">{p.cliente}</span>
                      </div>
                    </div>

                    <div className="text-right shrink-0">
                      <div className="text-lg font-bold text-amber-400 leading-none">
                        {u.num} <span className="text-xs font-normal">{u.un}</span>
                      </div>
                      <div className="text-[10px] text-slate-400 mt-1">Fatal: {p.data_fatal}</div>
                    </div>
                  </div>

                  <div className="mt-4 pt-3 border-t border-slate-700/50 flex items-center justify-between">
                    <div className="text-[11px] text-slate-400">
                      Confirmado por: <span className="text-slate-200">{p.confirmado_por || '—'}</span>
                    </div>
                    <button
                      onClick={() => onMarcarCumprido(p.id)}
                      className="px-3 py-1.5 bg-emerald-600/90 hover:bg-emerald-500 text-slate-100 font-semibold text-xs rounded-lg flex items-center gap-1 transition-colors"
                    >
                      <Check className="w-3.5 h-3.5" /> Marcar cumprido
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        </section>
      )}

      {/* 3. PRÓXIMOS COMPROMISSOS */}
      {proxCompromissos.length > 0 && (
        <section className="space-y-4">
          <div className="flex items-center justify-between pb-2 border-b border-slate-800">
            <div className="flex items-center gap-2">
              <h2 className="text-sm font-bold uppercase tracking-wider text-blue-400">
                Próximos compromissos
              </h2>
              <span className="bg-blue-500/20 text-blue-300 border border-blue-500/30 text-xs px-2 py-0.5 rounded-full font-semibold">
                {proxCompromissos.length}
              </span>
            </div>
          </div>

          <div className="space-y-2.5">
            {proxCompromissos.map((c) => {
              const compDate = new Date(c.data + 'T00:00:00');
              const hojeStart = new Date(hoje.getFullYear(), hoje.getMonth(), hoje.getDate());
              const diffDays = Math.ceil((compDate.getTime() - hojeStart.getTime()) / (1000 * 60 * 60 * 24));
              const quando = diffDays === 0 ? 'hoje' : diffDays === 1 ? 'amanhã' : `em ${diffDays} dias`;

              return (
                <div
                  key={c.id}
                  className="bg-slate-800/60 border border-slate-700/60 rounded-xl p-3.5 flex items-center justify-between gap-4"
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <div className="w-10 h-10 rounded-lg bg-blue-500/10 border border-blue-500/30 flex flex-col items-center justify-center shrink-0 text-blue-400">
                      <span className="text-xs font-bold leading-none">{compDate.getDate()}</span>
                      <span className="text-[9px] uppercase font-semibold">
                        {compDate.toLocaleString('pt-BR', { month: 'short' }).replace('.', '')}
                      </span>
                    </div>

                    <div className="min-w-0">
                      <div className="text-xs font-bold text-slate-200 truncate">{c.titulo}</div>
                      <div className="text-[11px] text-slate-400 truncate mt-0.5">
                        {c.cliente && <span>Cliente: {c.cliente} · </span>}
                        <span className="text-blue-300 font-medium">{quando}</span>
                        {c.hora && <span> · {c.hora}</span>}
                        {c.local && <span> · {c.local}</span>}
                      </div>
                    </div>
                  </div>

                  <span className="text-xs text-slate-400 bg-slate-900 px-2.5 py-1 rounded border border-slate-800 shrink-0 capitalize">
                    {c.tipo}
                  </span>
                </div>
              );
            })}
          </div>
        </section>
      )}

      {/* 4. EMPTY STATE */}
      {revisar.length === 0 && urgentes.length === 0 && proxCompromissos.length === 0 && (
        <div className="bg-slate-800/40 border border-slate-800 rounded-2xl p-12 text-center my-8">
          <div className="w-12 h-12 rounded-full bg-emerald-500/10 text-emerald-400 flex items-center justify-center mx-auto mb-3">
            <CheckCircle2 className="w-6 h-6" />
          </div>
          <h3 className="text-lg font-bold text-slate-200 font-serif">Nada exige ação hoje</h3>
          <p className="text-xs text-slate-400 max-w-md mx-auto mt-1">
            Prazos revisados, com folga, e nenhum compromisso nos próximos dias.
          </p>
        </div>
      )}
    </div>
  );
};
