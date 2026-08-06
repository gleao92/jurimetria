import React, { useState } from 'react';
import { Prazo, Compromisso, StatusPrazo } from '../types';
import { calcularUrgencia } from '../lib/prazosEngine';
import { Download, Plus, Search, Filter, Calendar, FileSpreadsheet, ShieldCheck } from 'lucide-react';

interface PrazosViewProps {
  prazos: Prazo[];
  compromissos: Compromisso[];
  podeConfirmar: boolean;
  onAddManualPrazo: (p: Omit<Prazo, 'id'>) => void;
  onConfirmPrazo: (id: string, updatedData: Partial<Prazo>) => void;
  onMarcarCumprido: (id: string) => void;
}

export const PrazosView: React.FC<PrazosViewProps> = ({
  prazos,
  compromissos,
  podeConfirmar,
  onAddManualPrazo,
  onConfirmPrazo,
  onMarcarCumprido,
}) => {
  const [selectedStatus, setSelectedStatus] = useState<StatusPrazo[]>([
    'pendente_revisao',
    'confirmado',
  ]);
  const [searchTerm, setSearchTerm] = useState('');
  const [showAddModal, setShowAddModal] = useState(false);

  // Manual deadline form
  const [procNum, setProcNum] = useState('');
  const [clienteName, setClienteName] = useState('');
  const [atoName, setAtoName] = useState('');
  const [diasCount, setDiasCount] = useState(15);
  const [areaSelect, setAreaSelect] = useState<'civel' | 'criminal'>('civel');

  const hoje = new Date();

  // Filter prazos
  const filtered = prazos.filter((p) => {
    const matchStatus = selectedStatus.includes(p.status);
    const textToMatch = `${p.processo} ${p.cliente} ${p.ato} ${p.orgao}`.toLowerCase();
    const matchSearch = textToMatch.includes(searchTerm.toLowerCase());
    return matchStatus && matchSearch;
  });

  const toggleStatus = (st: StatusPrazo) => {
    if (selectedStatus.includes(st)) {
      setSelectedStatus(selectedStatus.filter((s) => s !== st));
    } else {
      setSelectedStatus([...selectedStatus, st]);
    }
  };

  // Generate .ics calendar string
  const handleDownloadICS = () => {
    const confirmados = prazos.filter((p) => p.status === 'confirmado');
    let icsContent = [
      'BEGIN:VCALENDAR',
      'VERSION:2.0',
      'PRODID:-//Tempestivo Controladoria//BR',
      'CALSCALE:GREGORIAN',
    ];

    confirmados.forEach((p) => {
      const dateFatalClean = p.data_fatal.replace(/-/g, '');
      icsContent.push(
        'BEGIN:VEVENT',
        `SUMMARY:FATAL: ${p.ato} - ${p.cliente}`,
        `DESCRIPTION:Processo: ${p.processo}\\nTribunal: ${p.orgao || p.tribunal}`,
        `DTSTART;VALUE=DATE:${dateFatalClean}`,
        `DTEND;VALUE=DATE:${dateFatalClean}`,
        'END:VEVENT'
      );
    });

    icsContent.push('END:VCALENDAR');

    const blob = new Blob([icsContent.join('\r\n')], { type: 'text/calendar;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `prazos_tempestivo_${hoje.toISOString().split('T')[0]}.ics`;
    link.click();
  };

  // Export CSV
  const handleDownloadCSV = () => {
    const headers = ['Ato', 'Cliente', 'Processo', 'Área', 'Data Interna', 'Data Fatal', 'Situação', 'Confirmado Por'];
    const rows = filtered.map((p) => [
      `"${p.ato}"`,
      `"${p.cliente}"`,
      `"${p.processo}"`,
      `"${p.area}"`,
      `"${p.prazo_interno}"`,
      `"${p.data_fatal}"`,
      `"${p.status}"`,
      `"${p.confirmado_por || ''}"`,
    ]);

    const csvContent = [headers.join(','), ...rows.map((r) => r.join(','))].join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `prazos_tempestivo_${hoje.toISOString().split('T')[0]}.csv`;
    link.click();
  };

  const handleManualFormSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!procNum || !atoName) return;

    const todayStr = hoje.toISOString().split('T')[0];

    onAddManualPrazo({
      processo: procNum,
      cliente: clienteName || 'não informado',
      tribunal: 'TJGO',
      orgao: 'Vara Cível',
      ato: atoName,
      area: areaSelect,
      data_disponibilizacao: todayStr,
      publicacao: todayStr,
      inicio_contagem: todayStr,
      data_fatal: todayStr,
      prazo_interno: todayStr,
      dias_prazo: diasCount,
      status: 'pendente_revisao',
    });

    setShowAddModal(false);
    setProcNum('');
    setClienteName('');
    setAtoName('');
  };

  return (
    <div className="space-y-6">
      {/* Top Filter and Search Bar */}
      <div className="bg-slate-800/80 p-4 rounded-2xl border border-slate-700/60 flex flex-col md:flex-row items-center justify-between gap-4">
        {/* Status filters */}
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-xs font-semibold text-slate-400 mr-1 flex items-center gap-1">
            <Filter className="w-3.5 h-3.5" /> Situação:
          </span>

          <button
            onClick={() => toggleStatus('pendente_revisao')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors ${
              selectedStatus.includes('pendente_revisao')
                ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40'
                : 'bg-slate-900 text-slate-400 border border-slate-800 hover:bg-slate-800'
            }`}
          >
            Pendente Revisão
          </button>

          <button
            onClick={() => toggleStatus('confirmado')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors ${
              selectedStatus.includes('confirmado')
                ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40'
                : 'bg-slate-900 text-slate-400 border border-slate-800 hover:bg-slate-800'
            }`}
          >
            Confirmados
          </button>

          <button
            onClick={() => toggleStatus('cumprido')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors ${
              selectedStatus.includes('cumprido')
                ? 'bg-blue-500/20 text-blue-300 border border-blue-500/40'
                : 'bg-slate-900 text-slate-400 border border-slate-800 hover:bg-slate-800'
            }`}
          >
            Cumpridos
          </button>
        </div>

        {/* Search input & Add button */}
        <div className="flex items-center gap-2 w-full md:w-auto">
          <div className="relative flex-1 md:w-64">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
            <input
              type="text"
              placeholder="Buscar processo, cliente ou ato..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full bg-slate-900 border border-slate-700 rounded-xl pl-9 pr-3 py-1.5 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-amber-500"
            />
          </div>

          <button
            onClick={() => setShowAddModal(true)}
            className="px-3.5 py-2 bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold text-xs rounded-xl flex items-center gap-1.5 shrink-0 transition-colors"
          >
            <Plus className="w-4 h-4" /> Novo Prazo
          </button>
        </div>
      </div>

      {/* Main Table */}
      <div className="bg-slate-800/60 border border-slate-700/60 rounded-2xl overflow-hidden shadow-xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-900/90 text-slate-400 uppercase tracking-wider font-semibold border-b border-slate-700/80">
              <tr>
                <th className="p-3.5">Restam</th>
                <th className="p-3.5">Ato</th>
                <th className="p-3.5">Cliente</th>
                <th className="p-3.5">Área</th>
                <th className="p-3.5">Processo</th>
                <th className="p-3.5">Interno</th>
                <th className="p-3.5">Fatal</th>
                <th className="p-3.5">Situação</th>
                <th className="p-3.5 text-right">Ação</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/80 text-slate-200">
              {filtered.length === 0 ? (
                <tr>
                  <td colSpan={9} className="text-center py-8 text-slate-400">
                    Nenhum prazo encontrado com os filtros selecionados.
                  </td>
                </tr>
              ) : (
                filtered.map((p) => {
                  const u = calcularUrgencia(p, hoje);

                  return (
                    <tr key={p.id} className="hover:bg-slate-800/40 transition-colors">
                      <td className="p-3.5 font-bold">
                        <span
                          className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] ${
                            u.cor === 'red'
                              ? 'bg-rose-950/80 text-rose-300 border border-rose-800/50'
                              : u.cor === 'orange'
                              ? 'bg-amber-950/80 text-amber-300 border border-amber-800/50'
                              : u.cor === 'emerald'
                              ? 'bg-emerald-950/80 text-emerald-300 border border-emerald-800/50'
                              : 'bg-slate-800 text-slate-400'
                          }`}
                        >
                          {u.num} {u.un}
                        </span>
                      </td>
                      <td className="p-3.5 font-semibold text-slate-100">{p.ato}</td>
                      <td className="p-3.5 text-slate-300">{p.cliente}</td>
                      <td className="p-3.5 capitalize text-slate-400">{p.area}</td>
                      <td className="p-3.5 font-mono text-[11px] text-slate-300">{p.processo}</td>
                      <td className="p-3.5 font-medium text-amber-300">{p.prazo_interno}</td>
                      <td className="p-3.5 font-bold text-rose-300">{p.data_fatal}</td>
                      <td className="p-3.5">
                        <span
                          className={`px-2 py-0.5 rounded-full text-[10px] font-semibold uppercase tracking-wider ${
                            p.status === 'confirmado'
                              ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                              : p.status === 'pendente_revisao'
                              ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                              : 'bg-slate-700 text-slate-300'
                          }`}
                        >
                          {p.status.replace('_', ' ')}
                        </span>
                      </td>
                      <td className="p-3.5 text-right">
                        {p.status === 'confirmado' && (
                          <button
                            onClick={() => onMarcarCumprido(p.id)}
                            className="px-2.5 py-1 bg-emerald-600/80 hover:bg-emerald-500 text-slate-100 text-[11px] font-medium rounded transition-colors"
                          >
                            Cumprir
                          </button>
                        )}
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Export Section */}
      <div className="bg-slate-800/40 border border-slate-800 rounded-2xl p-5 space-y-3">
        <h3 className="text-sm font-bold text-slate-200 font-serif flex items-center gap-2">
          <Calendar className="w-4 h-4 text-amber-400" /> Exportação de Prazos e Calendário
        </h3>
        <p className="text-xs text-slate-400">
          Prazos confirmados viram compromissos com alarme na sua agenda pessoal (Google Agenda, Outlook ou Apple iCal).
        </p>
        <div className="flex flex-wrap gap-3 pt-2">
          <button
            onClick={handleDownloadICS}
            className="px-4 py-2 bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold text-xs rounded-xl flex items-center gap-2 transition-colors shadow-md shadow-amber-500/10"
          >
            <Download className="w-4 h-4" /> Baixar agenda (.ics)
          </button>
          <button
            onClick={handleDownloadCSV}
            className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-slate-200 font-medium text-xs rounded-xl flex items-center gap-2 transition-colors"
          >
            <FileSpreadsheet className="w-4 h-4" /> Baixar planilha (.csv)
          </button>
        </div>
      </div>

      {/* Manual Deadline Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-slate-900 border border-slate-700 rounded-2xl p-6 max-w-md w-full space-y-4 shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-base font-bold text-slate-100 font-serif">Adicionar Prazo Manual</h3>
              <button
                onClick={() => setShowAddModal(false)}
                className="text-slate-400 hover:text-slate-200 text-sm"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleManualFormSubmit} className="space-y-3">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Número do Processo</label>
                <input
                  type="text"
                  required
                  placeholder="1002345-67.2026.8.09.0051"
                  value={procNum}
                  onChange={(e) => setProcNum(e.target.value)}
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg p-2 text-xs text-slate-100"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Cliente</label>
                <input
                  type="text"
                  placeholder="Nome do cliente"
                  value={clienteName}
                  onChange={(e) => setClienteName(e.target.value)}
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg p-2 text-xs text-slate-100"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Ato Processual</label>
                <input
                  type="text"
                  required
                  placeholder="Ex: Contestação, Réplica, Apelação"
                  value={atoName}
                  onChange={(e) => setAtoName(e.target.value)}
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg p-2 text-xs text-slate-100"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Prazo (Dias)</label>
                  <input
                    type="number"
                    min={1}
                    value={diasCount}
                    onChange={(e) => setDiasCount(parseInt(e.target.value, 10) || 1)}
                    className="w-full bg-slate-800 border border-slate-700 rounded-lg p-2 text-xs text-slate-100"
                  />
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Área</label>
                  <select
                    value={areaSelect}
                    onChange={(e) => setAreaSelect(e.target.value as any)}
                    className="w-full bg-slate-800 border border-slate-700 rounded-lg p-2 text-xs text-slate-100"
                  >
                    <option value="civel">Cível (dias úteis)</option>
                    <option value="criminal">Criminal (dias corridos)</option>
                  </select>
                </div>
              </div>

              <div className="flex justify-end gap-2 pt-3">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-xs"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold rounded-lg text-xs"
                >
                  Adicionar
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
