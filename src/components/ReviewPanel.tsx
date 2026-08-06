import React, { useState } from 'react';
import { Prazo, AreaProcesso } from '../types';
import { calcularPrazo } from '../lib/prazosEngine';
import { CheckCircle2, XCircle, AlertCircle, FileText, Calendar, Clock, ShieldCheck, Trash2 } from 'lucide-react';

interface ReviewPanelProps {
  prazo: Prazo;
  podeConfirmar: boolean;
  onConfirm: (id: string, updatedData: Partial<Prazo>) => void;
  onDelete: (id: string) => void;
  onClose: () => void;
  feriadosLocaisMap?: Record<string, string>;
}

export const ReviewPanel: React.FC<ReviewPanelProps> = ({
  prazo,
  podeConfirmar,
  onConfirm,
  onDelete,
  onClose,
  feriadosLocaisMap = {},
}) => {
  const [ato, setAto] = useState(prazo.ato);
  const [dias, setDias] = useState(prazo.dias_prazo);
  const [area, setArea] = useState<AreaProcesso>(prazo.area === 'a_confirmar' ? 'civel' : prazo.area);
  const [obs, setObs] = useState(prazo.observacoes || '');

  // Live recalculation based on parameters
  const dataDisp = new Date(prazo.data_disponibilizacao + 'T00:00:00');
  const calc = calcularPrazo(dataDisp, dias, area, 3, '', 'disponibilizacao', feriadosLocaisMap);

  const fatalStr = calc.data_fatal.toISOString().split('T')[0];
  const internoStr = calc.prazo_interno.toISOString().split('T')[0];
  const pubStr = calc.publicacao.toISOString().split('T')[0];
  const inicioStr = calc.inicio_contagem.toISOString().split('T')[0];

  const handleConfirmSubmit = () => {
    onConfirm(prazo.id, {
      ato,
      dias_prazo: dias,
      area,
      observacoes: obs,
      publicacao: pubStr,
      inicio_contagem: inicioStr,
      data_fatal: fatalStr,
      prazo_interno: internoStr,
      contagem_explicacao: calc.contagem,
      status: 'confirmado',
    });
  };

  return (
    <div className="bg-slate-800/90 border border-amber-500/40 rounded-xl p-5 shadow-xl mt-4 space-y-5">
      {/* Header */}
      <div className="flex items-start justify-between pb-3 border-b border-slate-700/80">
        <div>
          <span className="text-xs font-semibold uppercase tracking-wider text-amber-400 bg-amber-500/10 px-2.5 py-1 rounded-md border border-amber-500/30 inline-flex items-center gap-1.5">
            <ShieldCheck className="w-3.5 h-3.5" /> Revisão de Prazo
          </span>
          <h3 className="text-lg font-bold text-slate-100 mt-2 font-serif">
            {prazo.processo} — <span className="text-amber-300">{prazo.cliente}</span>
          </h3>
          <p className="text-xs text-slate-400">{prazo.orgao || prazo.tribunal}</p>
        </div>
        <button
          onClick={onClose}
          className="text-slate-400 hover:text-slate-200 p-1 rounded-lg hover:bg-slate-700 transition-colors"
        >
          <XCircle className="w-5 h-5" />
        </button>
      </div>

      {/* Publication Text */}
      {prazo.teor && (
        <div className="bg-slate-900/80 border border-slate-700/60 rounded-lg p-3.5">
          <div className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5 flex items-center gap-1.5">
            <FileText className="w-3.5 h-3.5 text-slate-400" /> Teor da Publicação (DJEN)
          </div>
          <p className="text-xs text-slate-300 leading-relaxed font-mono whitespace-pre-wrap max-h-40 overflow-y-auto pr-1">
            {prazo.teor}
          </p>
        </div>
      )}

      {/* Form Fields for Adjustments */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 bg-slate-900/40 p-4 rounded-xl border border-slate-700/40">
        <div>
          <label className="block text-xs font-medium text-slate-300 mb-1">Ato Processual</label>
          <input
            type="text"
            value={ato}
            onChange={(e) => setAto(e.target.value)}
            disabled={!podeConfirmar}
            className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-xs text-slate-100 focus:outline-none focus:border-amber-500"
          />
        </div>

        <div>
          <label className="block text-xs font-medium text-slate-300 mb-1">Prazo em Dias</label>
          <input
            type="number"
            min={1}
            max={180}
            value={dias}
            onChange={(e) => setDias(parseInt(e.target.value, 10) || 1)}
            disabled={!podeConfirmar}
            className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-xs text-slate-100 focus:outline-none focus:border-amber-500"
          />
        </div>

        <div>
          <label className="block text-xs font-medium text-slate-300 mb-1">Área de Contagem</label>
          <select
            value={area}
            onChange={(e) => setArea(e.target.value as AreaProcesso)}
            disabled={!podeConfirmar}
            className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-xs text-slate-100 focus:outline-none focus:border-amber-500"
          >
            <option value="civel">Cível (dias úteis - CPC art. 219)</option>
            <option value="criminal">Criminal (dias corridos - CPP art. 798)</option>
          </select>
        </div>
      </div>

      {/* Calculated Dates Summary */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div className="bg-slate-900/60 p-3 rounded-lg border border-slate-800">
          <span className="text-[11px] text-slate-400 block font-medium">Disponibilização</span>
          <span className="text-sm font-semibold text-slate-200 mt-0.5 block">{prazo.data_disponibilizacao}</span>
        </div>

        <div className="bg-slate-900/60 p-3 rounded-lg border border-slate-800">
          <span className="text-[11px] text-slate-400 block font-medium">Início Contagem</span>
          <span className="text-sm font-semibold text-slate-200 mt-0.5 block">{inicioStr}</span>
        </div>

        <div className="bg-slate-900/60 p-3 rounded-lg border border-amber-500/30 bg-amber-500/5">
          <span className="text-[11px] text-amber-300 block font-medium flex items-center gap-1">
            <Clock className="w-3 h-3" /> Prazo Interno (alvo)
          </span>
          <span className="text-sm font-bold text-amber-300 mt-0.5 block">{internoStr}</span>
          <span className="text-[10px] text-slate-400">3 dias úteis antes</span>
        </div>

        <div className="bg-slate-900/60 p-3 rounded-lg border border-rose-500/30 bg-rose-500/5">
          <span className="text-[11px] text-rose-300 block font-medium flex items-center gap-1">
            <Calendar className="w-3 h-3" /> Data Fatal (limite)
          </span>
          <span className="text-sm font-bold text-rose-300 mt-0.5 block">{fatalStr}</span>
          <span className="text-[10px] text-slate-400">{calc.contagem}</span>
        </div>
      </div>

      {/* Observações */}
      <div>
        <label className="block text-xs font-medium text-slate-300 mb-1">Observações do Advogado</label>
        <textarea
          rows={2}
          value={obs}
          onChange={(e) => setObs(e.target.value)}
          placeholder="Ex: Peça já rascunhada; aguardando documentos do cliente."
          disabled={!podeConfirmar}
          className="w-full bg-slate-900 border border-slate-700 rounded-lg p-2.5 text-xs text-slate-100 focus:outline-none focus:border-amber-500"
        />
      </div>

      {/* Action Buttons */}
      <div className="flex flex-wrap items-center justify-between gap-3 pt-2 border-t border-slate-700/60">
        <button
          onClick={() => onDelete(prazo.id)}
          disabled={!podeConfirmar}
          className="px-3 py-2 bg-rose-950/40 hover:bg-rose-900/60 text-rose-300 border border-rose-800/50 rounded-lg text-xs font-medium flex items-center gap-1.5 transition-colors"
        >
          <Trash2 className="w-3.5 h-3.5" /> Excluir prazo
        </button>

        <div className="flex items-center gap-2">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-slate-200 rounded-lg text-xs font-medium transition-colors"
          >
            Fechar
          </button>
          <button
            onClick={handleConfirmSubmit}
            disabled={!podeConfirmar}
            className="px-5 py-2 bg-amber-500 hover:bg-amber-400 disabled:opacity-50 text-slate-950 rounded-lg text-xs font-bold flex items-center gap-1.5 transition-colors shadow-lg shadow-amber-500/20"
          >
            <CheckCircle2 className="w-4 h-4" /> Confirmar Prazo
          </button>
        </div>
      </div>
    </div>
  );
};
