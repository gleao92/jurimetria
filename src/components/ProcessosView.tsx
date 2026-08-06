import React, { useState } from 'react';
import { Processo, AreaProcesso } from '../types';
import { FolderPlus, AlertTriangle, CheckCircle2, Save, FileText, Search } from 'lucide-react';

interface ProcessosViewProps {
  processos: Processo[];
  podeConfirmar: boolean;
  onUpdateProcessos: (procs: Processo[]) => void;
  onImportProcessosText: (text: string, areaPadrao: AreaProcesso) => void;
}

// Regex to find CNJ numbers (NNNNNNN-DD.YYYY.J.TR.OOOO)
function extractCNJNumbers(text: string): string[] {
  const cnjRegex = /\b\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}\b/g;
  const matches = text.match(cnjRegex) || [];
  return Array.from(new Set(matches));
}

export const ProcessosView: React.FC<ProcessosViewProps> = ({
  processos,
  podeConfirmar,
  onUpdateProcessos,
  onImportProcessosText,
}) => {
  const [editedProcessos, setEditedProcessos] = useState<Processo[]>(processos);
  const [importText, setImportText] = useState('');
  const [importArea, setImportArea] = useState<AreaProcesso>('civel');
  const [showImportBox, setShowImportBox] = useState(processos.length === 0);
  const [savedMsg, setSavedMsg] = useState('');

  const faltamArea = editedProcessos.filter((p) => p.area === 'a_confirmar');

  const handleAreaChange = (numero: string, area: AreaProcesso) => {
    setEditedProcessos(
      editedProcessos.map((p) => (p.numero === numero ? { ...p, area } : p))
    );
  };

  const handleClienteChange = (numero: string, cliente: string) => {
    setEditedProcessos(
      editedProcessos.map((p) => (p.numero === numero ? { ...p, cliente } : p))
    );
  };

  const handleBulkArea = (targetArea: AreaProcesso) => {
    setEditedProcessos(
      editedProcessos.map((p) =>
        p.area === 'a_confirmar' ? { ...p, area: targetArea } : p
      )
    );
  };

  const handleSaveChanges = () => {
    onUpdateProcessos(editedProcessos);
    setSavedMsg('Alterações salvas com sucesso! Prazos recalculados.');
    setTimeout(() => setSavedMsg(''), 4000);
  };

  const handleImportSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!importText.trim()) return;
    onImportProcessosText(importText, importArea);
    setImportText('');
    setShowImportBox(false);
  };

  const recognizedNumbers = extractCNJNumbers(importText);

  return (
    <div className="space-y-6">
      {/* Warning if unassigned areas exist */}
      {faltamArea.length > 0 && podeConfirmar && (
        <div className="bg-amber-950/60 border border-amber-800/80 rounded-2xl p-4 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div className="flex items-start gap-3">
            <AlertTriangle className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
            <div>
              <h4 className="text-xs font-bold text-amber-200 uppercase tracking-wider">
                {faltamArea.length} processos sem área definida
              </h4>
              <p className="text-xs text-amber-300/80 mt-0.5">
                Sem ela o sistema usa a contagem cível por padrão. Defina a área dos processos para que a contagem seja exata.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 shrink-0">
            <button
              onClick={() => handleBulkArea('civel')}
              className="px-3 py-1.5 bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold text-xs rounded-lg transition-colors"
            >
              Marcar todos como Cível
            </button>
            <button
              onClick={() => handleBulkArea('criminal')}
              className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 font-semibold text-xs rounded-lg border border-slate-700 transition-colors"
            >
              Marcar todos como Criminal
            </button>
          </div>
        </div>
      )}

      {/* Main Process Portfolio Table */}
      <div className="bg-slate-800/60 border border-slate-700/60 rounded-2xl overflow-hidden shadow-xl">
        <div className="p-4 border-b border-slate-700/80 flex items-center justify-between">
          <h3 className="text-sm font-bold text-slate-100 font-serif flex items-center gap-2">
            <FileText className="w-4 h-4 text-amber-400" /> Carteira de Processos ({editedProcessos.length})
          </h3>

          {podeConfirmar && (
            <button
              onClick={handleSaveChanges}
              className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-slate-100 font-bold text-xs rounded-xl flex items-center gap-1.5 transition-colors shadow-lg shadow-emerald-600/20"
            >
              <Save className="w-4 h-4" /> Salvar Alterações
            </button>
          )}
        </div>

        {savedMsg && (
          <div className="bg-emerald-950/60 border-b border-emerald-800/50 text-emerald-300 text-xs px-4 py-2 flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4" /> {savedMsg}
          </div>
        )}

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-900/90 text-slate-400 uppercase tracking-wider font-semibold border-b border-slate-700/80">
              <tr>
                <th className="p-3.5">Número do Processo</th>
                <th className="p-3.5">Cliente</th>
                <th className="p-3.5">Área de Contagem</th>
                <th className="p-3.5">Tribunal / Sistema</th>
                <th className="p-3.5">Assunto</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/80 text-slate-200">
              {editedProcessos.length === 0 ? (
                <tr>
                  <td colSpan={5} className="text-center py-8 text-slate-400">
                    Sua carteira está vazia. Cole a lista de processos abaixo para importar.
                  </td>
                </tr>
              ) : (
                editedProcessos.map((p) => (
                  <tr key={p.numero} className="hover:bg-slate-800/40 transition-colors">
                    <td className="p-3.5 font-mono font-bold text-slate-100">{p.numero}</td>
                    <td className="p-3.5">
                      <input
                        type="text"
                        value={p.cliente}
                        disabled={!podeConfirmar}
                        onChange={(e) => handleClienteChange(p.numero, e.target.value)}
                        className="bg-slate-900/80 border border-slate-700 rounded px-2 py-1 text-xs text-slate-100 w-full focus:outline-none focus:border-amber-500 disabled:bg-transparent disabled:border-none"
                      />
                    </td>
                    <td className="p-3.5">
                      <select
                        value={p.area}
                        disabled={!podeConfirmar}
                        onChange={(e) => handleAreaChange(p.numero, e.target.value as AreaProcesso)}
                        className={`bg-slate-900 border border-slate-700 rounded px-2 py-1 text-xs font-medium focus:outline-none focus:border-amber-500 disabled:bg-transparent ${
                          p.area === 'civel'
                            ? 'text-emerald-300'
                            : p.area === 'criminal'
                            ? 'text-rose-300'
                            : 'text-amber-400 font-bold'
                        }`}
                      >
                        <option value="a_confirmar">a confirmar</option>
                        <option value="civel">cível (dias úteis)</option>
                        <option value="criminal">criminal (dias corridos)</option>
                      </select>
                    </td>
                    <td className="p-3.5 text-slate-400">
                      {p.tribunal} · {p.sistema}
                    </td>
                    <td className="p-3.5 text-slate-300">{p.assunto || '—'}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Import Section */}
      {podeConfirmar && (
        <div className="bg-slate-800/40 border border-slate-800 rounded-2xl p-5 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-bold text-slate-200 font-serif flex items-center gap-2">
                <FolderPlus className="w-4 h-4 text-amber-400" /> Importar Processos em Lote
              </h3>
              <p className="text-xs text-slate-400 mt-0.5">
                Cole qualquer texto com números de processo (CNJ). O sistema extrai e cadastra na carteira automaticamente.
              </p>
            </div>
            <button
              onClick={() => setShowImportBox(!showImportBox)}
              className="text-xs text-amber-400 hover:underline font-medium"
            >
              {showImportBox ? 'Ocultar' : 'Expandir'}
            </button>
          </div>

          {showImportBox && (
            <form onSubmit={handleImportSubmit} className="space-y-3 pt-2">
              <textarea
                rows={4}
                value={importText}
                onChange={(e) => setImportText(e.target.value)}
                placeholder="Cole a lista de processos aqui... Ex: 1002345-67.2026.8.09.0051"
                className="w-full bg-slate-900 border border-slate-700 rounded-xl p-3 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-amber-500 font-mono"
              />

              <div className="flex flex-col sm:flex-row items-center justify-between gap-3">
                <div className="text-xs text-slate-400">
                  {importText.trim() ? (
                    <span className="text-amber-300 font-bold">
                      {recognizedNumbers.length} processos reconhecidos
                    </span>
                  ) : (
                    'Nenhum processo colado ainda.'
                  )}
                </div>

                <div className="flex items-center gap-3 w-full sm:w-auto">
                  <select
                    value={importArea}
                    onChange={(e) => setImportArea(e.target.value as AreaProcesso)}
                    className="bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-amber-500"
                  >
                    <option value="civel">Área Padrão: Cível</option>
                    <option value="criminal">Área Padrão: Criminal</option>
                    <option value="a_confirmar">Área Padrão: Definição Posterior</option>
                  </select>

                  <button
                    type="submit"
                    disabled={recognizedNumbers.length === 0}
                    className="px-5 py-2 bg-amber-500 hover:bg-amber-400 disabled:opacity-50 text-slate-950 font-bold text-xs rounded-xl transition-colors shadow-md shadow-amber-500/10 shrink-0"
                  >
                    Importar Processos
                  </button>
                </div>
              </div>
            </form>
          )}
        </div>
      )}
    </div>
  );
};
