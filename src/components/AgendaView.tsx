import React, { useState } from 'react';
import { Prazo, Compromisso } from '../types';
import { ChevronLeft, ChevronRight, Plus, Calendar as CalendarIcon, Clock, AlertTriangle } from 'lucide-react';

interface AgendaViewProps {
  prazos: Prazo[];
  compromissos: Compromisso[];
  onAddCompromisso: (c: Omit<Compromisso, 'id'>) => void;
}

export const AgendaView: React.FC<AgendaViewProps> = ({
  prazos,
  compromissos,
  onAddCompromisso,
}) => {
  const [currentDate, setCurrentDate] = useState(new Date());
  const [selectedDayStr, setSelectedDayStr] = useState<string | null>(null);
  const [showAddModal, setShowAddModal] = useState(false);

  // New appointment form state
  const [titulo, setTitulo] = useState('');
  const [tipo, setTipo] = useState<'audiencia' | 'reuniao' | 'diligencia' | 'outro'>('audiencia');
  const [data, setData] = useState(new Date().toISOString().split('T')[0]);
  const [hora, setHora] = useState('14:00');
  const [local, setLocal] = useState('');
  const [cliente, setCliente] = useState('');
  const [processo, setProcesso] = useState('');

  const year = currentDate.getFullYear();
  const month = currentDate.getMonth();

  const firstDayOfMonth = new Date(year, month, 1);
  const lastDayOfMonth = new Date(year, month + 1, 0);

  const startDayOfWeek = firstDayOfMonth.getDay() === 0 ? 6 : firstDayOfMonth.getDay() - 1; // Mon = 0
  const daysInMonth = lastDayOfMonth.getDate();

  const monthName = currentDate.toLocaleString('pt-BR', { month: 'long', year: 'numeric' });

  // Map deadlines and appointments by YYYY-MM-DD
  const eventsByDate: Record<string, { type: 'fatal' | 'interno' | 'compromisso'; title: string; subtitle: string; raw: any }[]> = {};

  prazos.forEach((p) => {
    if (p.status === 'cumprido') return;

    // Fatal date
    if (p.data_fatal) {
      if (!eventsByDate[p.data_fatal]) eventsByDate[p.data_fatal] = [];
      eventsByDate[p.data_fatal].push({
        type: 'fatal',
        title: `FATAL: ${p.ato}`,
        subtitle: `${p.processo} (${p.cliente})`,
        raw: p,
      });
    }

    // Internal date
    if (p.prazo_interno) {
      if (!eventsByDate[p.prazo_interno]) eventsByDate[p.prazo_interno] = [];
      eventsByDate[p.prazo_interno].push({
        type: 'interno',
        title: `ALVO: ${p.ato}`,
        subtitle: `${p.processo} (${p.cliente})`,
        raw: p,
      });
    }
  });

  compromissos.forEach((c) => {
    if (c.data) {
      if (!eventsByDate[c.data]) eventsByDate[c.data] = [];
      eventsByDate[c.data].push({
        type: 'compromisso',
        title: `${c.tipo.toUpperCase()}: ${c.titulo}`,
        subtitle: c.cliente ? `Cliente: ${c.cliente}` : c.local || '',
        raw: c,
      });
    }
  });

  const handlePrevMonth = () => setCurrentDate(new Date(year, month - 1, 1));
  const handleNextMonth = () => setCurrentDate(new Date(year, month + 1, 1));
  const handleToday = () => setCurrentDate(new Date());

  const handleFormSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!titulo || !data) return;
    onAddCompromisso({
      titulo,
      tipo,
      data,
      hora,
      local,
      cliente,
      processo,
    });
    setShowAddModal(false);
    setTitulo('');
    setLocal('');
    setCliente('');
    setProcesso('');
  };

  const daysGrid = [];
  for (let i = 0; i < startDayOfWeek; i++) {
    daysGrid.push(null);
  }
  for (let day = 1; day <= daysInMonth; day++) {
    daysGrid.push(day);
  }

  const selectedEvents = selectedDayStr ? eventsByDate[selectedDayStr] || [] : [];

  return (
    <div className="space-y-6">
      {/* Calendar Bar Controls */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-4 bg-slate-800/80 p-4 rounded-2xl border border-slate-700/60">
        <div className="flex items-center gap-3">
          <button
            onClick={handleToday}
            className="px-3 py-1.5 bg-slate-700 hover:bg-slate-600 text-slate-200 text-xs font-semibold rounded-lg transition-colors"
          >
            Hoje
          </button>
          <div className="flex items-center gap-1">
            <button
              onClick={handlePrevMonth}
              className="p-1.5 bg-slate-900 hover:bg-slate-700 text-slate-300 rounded-lg transition-colors"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <button
              onClick={handleNextMonth}
              className="p-1.5 bg-slate-900 hover:bg-slate-700 text-slate-300 rounded-lg transition-colors"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
          <h2 className="text-lg font-bold font-serif text-slate-100 capitalize">
            {monthName}
          </h2>
        </div>

        <button
          onClick={() => setShowAddModal(true)}
          className="px-4 py-2 bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold text-xs rounded-xl flex items-center gap-1.5 transition-colors shadow-md shadow-amber-500/10"
        >
          <Plus className="w-4 h-4" /> Novo Compromisso
        </button>
      </div>

      {/* Calendar Grid */}
      <div className="bg-slate-800/60 border border-slate-700/60 rounded-2xl p-4 overflow-hidden">
        <div className="grid grid-cols-7 gap-1 text-center mb-2">
          {['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb', 'Dom'].map((d) => (
            <div key={d} className="text-xs font-semibold text-slate-400 uppercase py-1">
              {d}
            </div>
          ))}
        </div>

        <div className="grid grid-cols-7 gap-1 sm:gap-2">
          {daysGrid.map((day, idx) => {
            if (day === null) {
              return <div key={`empty-${idx}`} className="h-20 sm:h-28 bg-slate-900/20 rounded-lg"></div>;
            }

            const dayDate = new Date(year, month, day);
            const dateStr = `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
            const isToday =
              new Date().toISOString().split('T')[0] === dateStr;

            const events = eventsByDate[dateStr] || [];
            const isSelected = selectedDayStr === dateStr;

            return (
              <div
                key={dateStr}
                onClick={() => setSelectedDayStr(dateStr)}
                className={`h-20 sm:h-28 p-1.5 rounded-xl border flex flex-col justify-between cursor-pointer transition-all ${
                  isToday
                    ? 'bg-amber-500/10 border-amber-500/50'
                    : isSelected
                    ? 'bg-slate-700/90 border-slate-500'
                    : 'bg-slate-900/60 border-slate-800 hover:border-slate-700'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span
                    className={`text-xs font-bold w-5 h-5 rounded-full flex items-center justify-center ${
                      isToday ? 'bg-amber-500 text-slate-950' : 'text-slate-300'
                    }`}
                  >
                    {day}
                  </span>
                  {events.length > 0 && (
                    <span className="text-[10px] font-semibold text-slate-400 bg-slate-800 px-1.5 py-0.5 rounded-full">
                      {events.length}
                    </span>
                  )}
                </div>

                <div className="space-y-1 overflow-y-auto max-h-16 pr-0.5">
                  {events.map((ev, evIdx) => (
                    <div
                      key={evIdx}
                      className={`text-[9px] font-medium px-1.5 py-0.5 rounded truncate ${
                        ev.type === 'fatal'
                          ? 'bg-rose-950/80 text-rose-300 border border-rose-800/40'
                          : ev.type === 'interno'
                          ? 'bg-amber-950/80 text-amber-300 border border-amber-800/40'
                          : 'bg-blue-950/80 text-blue-300 border border-blue-800/40'
                      }`}
                    >
                      {ev.title}
                    </div>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Selected Day Details Panel */}
      {selectedDayStr && (
        <div className="bg-slate-800/90 border border-slate-700 rounded-2xl p-5 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-700 pb-3">
            <h3 className="text-sm font-bold text-slate-100 flex items-center gap-2">
              <CalendarIcon className="w-4 h-4 text-amber-400" /> Eventos para {selectedDayStr}
            </h3>
            <button
              onClick={() => setSelectedDayStr(null)}
              className="text-xs text-slate-400 hover:text-slate-200"
            >
              Fechar
            </button>
          </div>

          {selectedEvents.length === 0 ? (
            <div className="text-xs text-slate-400 py-3">Nenhum evento agendado para este dia.</div>
          ) : (
            <div className="space-y-2">
              {selectedEvents.map((ev, idx) => (
                <div
                  key={idx}
                  className="bg-slate-900/80 border border-slate-700/80 p-3 rounded-xl flex items-start gap-3"
                >
                  <div
                    className={`p-2 rounded-lg shrink-0 ${
                      ev.type === 'fatal'
                        ? 'bg-rose-500/10 text-rose-400'
                        : ev.type === 'interno'
                        ? 'bg-amber-500/10 text-amber-400'
                        : 'bg-blue-500/10 text-blue-400'
                    }`}
                  >
                    {ev.type === 'fatal' ? (
                      <AlertTriangle className="w-4 h-4" />
                    ) : (
                      <Clock className="w-4 h-4" />
                    )}
                  </div>
                  <div>
                    <div className="text-xs font-bold text-slate-200">{ev.title}</div>
                    <div className="text-[11px] text-slate-400 mt-0.5">{ev.subtitle}</div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Add Appointment Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-slate-900 border border-slate-700 rounded-2xl p-6 max-w-md w-full space-y-4 shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-base font-bold text-slate-100 font-serif">Novo Compromisso</h3>
              <button
                onClick={() => setShowAddModal(false)}
                className="text-slate-400 hover:text-slate-200 text-sm"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleFormSubmit} className="space-y-3">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Título</label>
                <input
                  type="text"
                  required
                  value={titulo}
                  onChange={(e) => setTitulo(e.target.value)}
                  placeholder="Ex: Audiência de Conciliação"
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg p-2 text-xs text-slate-100"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Tipo</label>
                  <select
                    value={tipo}
                    onChange={(e) => setTipo(e.target.value as any)}
                    className="w-full bg-slate-800 border border-slate-700 rounded-lg p-2 text-xs text-slate-100"
                  >
                    <option value="audiencia">Audiência</option>
                    <option value="reuniao">Reunião</option>
                    <option value="diligencia">Diligência</option>
                    <option value="outro">Outro</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Data</label>
                  <input
                    type="date"
                    required
                    value={data}
                    onChange={(e) => setData(e.target.value)}
                    className="w-full bg-slate-800 border border-slate-700 rounded-lg p-2 text-xs text-slate-100"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Hora</label>
                  <input
                    type="time"
                    value={hora}
                    onChange={(e) => setHora(e.target.value)}
                    className="w-full bg-slate-800 border border-slate-700 rounded-lg p-2 text-xs text-slate-100"
                  />
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Local</label>
                  <input
                    type="text"
                    value={local}
                    onChange={(e) => setLocal(e.target.value)}
                    placeholder="Ex: Fórum de Goiânia"
                    className="w-full bg-slate-800 border border-slate-700 rounded-lg p-2 text-xs text-slate-100"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Cliente</label>
                <input
                  type="text"
                  value={cliente}
                  onChange={(e) => setCliente(e.target.value)}
                  placeholder="Nome do cliente"
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg p-2 text-xs text-slate-100"
                />
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
                  Salvar
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
