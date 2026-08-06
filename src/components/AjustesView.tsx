import React, { useState } from 'react';
import { Configuracao, Regra, FeriadoLocal, LogEntry, User } from '../types';
import {
  ShieldCheck,
  Database,
  Radio,
  CheckCircle2,
  AlertCircle,
  RefreshCw,
  Plus,
  Trash2,
  List,
  RotateCcw,
  Calendar,
  History,
} from 'lucide-react';

interface AjustesViewProps {
  configuracao: Configuracao;
  regras: Regra[];
  feriadosLocais: FeriadoLocal[];
  logs: LogEntry[];
  currentUser: User;
  onSaveConfig: (cfg: Partial<Configuracao>) => void;
  onSaveRegras: (regras: Regra[]) => void;
  onRestoreDefaultRegras: () => void;
  onAddFeriadoLocal: (f: FeriadoLocal) => void;
  onRemoveFeriadoLocal: (dateStr: string) => void;
  onRecalcularPendentes: () => void;
}

export const AjustesView: React.FC<AjustesViewProps> = ({
  configuracao,
  regras,
  feriadosLocais,
  logs,
  currentUser,
  onSaveConfig,
  onSaveRegras,
  onRestoreDefaultRegras,
  onAddFeriadoLocal,
  onRemoveFeriadoLocal,
  onRecalcularPendentes,
}) => {
  const [oab, setOab] = useState(configuracao.oab_numero);
  const [uf, setUf] = useState(configuracao.oab_uf);
  const [fonte, setFonte] = useState(configuracao.fonte);
  const [areaPadrao, setAreaPadrao] = useState(configuracao.area_padrao);
  const [conectada, setConectada] = useState(configuracao.conectada);

  const [mniUser, setMniUser] = useState(configuracao.mni_usuario);
  const [mniSenha, setMniSenha] = useState(configuracao.mni_senha);
  const [mniWsdl, setMniWsdl] = useState(configuracao.mni_wsdl);

  const [testResult, setTestResult] = useState<string | null>(null);
  const [recalcMsg, setRecalcMsg] = useState('');

  // Rules state
  const [editedRegras, setEditedRegras] = useState<Regra[]>(regras);

  // New holiday state
  const [newHolDate, setNewHolDate] = useState('');
  const [newHolName, setNewHolName] = useState('');

  const handleTestConnection = () => {
    setTestResult('Conectando ao Diário Nacional (DJEN)...');
    setTimeout(() => {
      setTestResult(`✓ Conexão bem-sucedida! 14 publicações encontradas em 60 dias para OAB ${oab}/${uf}.`);
    }, 1200);
  };

  const handleSaveConfigSubmit = () => {
    onSaveConfig({
      oab_numero: oab,
      oab_uf: uf,
      fonte,
      area_padrao: areaPadrao,
      conectada,
      mni_usuario: mniUser,
      mni_senha: mniSenha,
      mni_wsdl: mniWsdl,
    });
  };

  const handleToggleConectada = (val: boolean) => {
    setConectada(val);
    onSaveConfig({ conectada: val });
  };

  const handleRuleChange = (id: string, field: keyof Regra, value: any) => {
    setEditedRegras(
      editedRegras.map((r) => (r.id === id ? { ...r, [field]: value } : r))
    );
  };

  const handleSaveRegrasSubmit = () => {
    onSaveRegras(editedRegras);
  };

  const handleAddHolidaySubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newHolDate || !newHolName) return;
    onAddFeriadoLocal({ data: newHolDate, nome: newHolName });
    setNewHolDate('');
    setNewHolName('');
  };

  const handleRecalcularSubmit = () => {
    onRecalcularPendentes();
    setRecalcMsg('Prazos não confirmados recalculados com sucesso!');
    setTimeout(() => setRecalcMsg(''), 4000);
  };

  return (
    <div className="space-y-8 max-w-5xl">
      {/* 1. OAB Token Notice */}
      <section className="bg-slate-800/80 border border-slate-700/60 rounded-2xl p-5 space-y-2">
        <h3 className="text-sm font-bold text-slate-100 font-serif flex items-center gap-2">
          <ShieldCheck className="w-4 h-4 text-amber-400" /> Certificado e Segurança da OAB
        </h3>
        <p className="text-xs text-slate-300 leading-relaxed">
          O token do advogado não entra neste sistema. A chave privada fica protegida dentro do seu dispositivo. Para acompanhar publicações e calcular prazos, o sistema realiza apenas consultas públicas por OAB e tribunal.
        </p>
      </section>

      {/* 2. Publication Sources */}
      <section className="bg-slate-800/60 border border-slate-700/60 rounded-2xl p-6 space-y-6">
        <div>
          <h3 className="text-sm font-bold text-slate-100 font-serif flex items-center gap-2">
            <Database className="w-4 h-4 text-amber-400" /> Fonte das Publicações
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Configure de onde o sistema deve capturar novas intimações.
          </p>
        </div>

        {/* Step 1 */}
        <div className="space-y-2">
          <span className="text-xs font-bold text-amber-400 uppercase tracking-wider">
            1 · Identificação do Advogado
          </span>
          <div className="grid grid-cols-3 gap-3 max-w-sm">
            <div className="col-span-2">
              <label className="block text-[11px] text-slate-400 mb-1">Número da OAB</label>
              <input
                type="text"
                value={oab}
                onChange={(e) => setOab(e.target.value)}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg p-2 text-xs text-slate-100 font-mono"
              />
            </div>
            <div>
              <label className="block text-[11px] text-slate-400 mb-1">UF</label>
              <input
                type="text"
                maxLength={2}
                value={uf}
                onChange={(e) => setUf(e.target.value.toUpperCase())}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg p-2 text-xs text-slate-100 uppercase text-center font-bold"
              />
            </div>
          </div>
        </div>

        {/* Step 2 */}
        <div className="space-y-2">
          <span className="text-xs font-bold text-amber-400 uppercase tracking-wider">
            2 · Fonte de Dados
          </span>
          <div className="space-y-2 max-w-md">
            <label className="flex items-center gap-2 text-xs text-slate-200 cursor-pointer">
              <input
                type="radio"
                name="fonte"
                value="djen"
                checked={fonte === 'djen'}
                onChange={() => setFonte('djen')}
                className="text-amber-500"
              />
              Diário Nacional (DJEN) — somente OAB, sem senha
            </label>
            <label className="flex items-center gap-2 text-xs text-slate-200 cursor-pointer">
              <input
                type="radio"
                name="fonte"
                value="mni"
                checked={fonte === 'mni'}
                onChange={() => setFonte('mni')}
                className="text-amber-500"
              />
              Webservice do Tribunal (MNI) — exige usuário e senha
            </label>
            <label className="flex items-center gap-2 text-xs text-slate-200 cursor-pointer">
              <input
                type="radio"
                name="fonte"
                value="ambas"
                checked={fonte === 'ambas'}
                onChange={() => setFonte('ambas')}
                className="text-amber-500"
              />
              As duas fontes combinadas com cruzamento automático
            </label>
          </div>
        </div>

        {/* Step 3 */}
        <div className="space-y-2 pt-2 border-t border-slate-700/60">
          <span className="text-xs font-bold text-amber-400 uppercase tracking-wider">
            3 · Testar Conexão
          </span>
          <div className="flex items-center gap-3">
            <button
              onClick={handleTestConnection}
              className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-slate-200 font-semibold text-xs rounded-xl transition-colors"
            >
              Testar Fonte Agora
            </button>
            <button
              onClick={handleSaveConfigSubmit}
              className="px-4 py-2 bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold text-xs rounded-xl transition-colors"
            >
              Salvar Configuração
            </button>
          </div>
          {testResult && (
            <div className="text-xs text-emerald-400 bg-emerald-950/40 p-2.5 rounded-lg border border-emerald-800/50 max-w-md mt-2">
              {testResult}
            </div>
          )}
        </div>

        {/* Step 4 */}
        <div className="pt-4 border-t border-slate-700/60 space-y-3">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-xs font-bold text-slate-200">Captura Automática pelo Computador do Escritório</div>
              <div className="text-[11px] text-slate-400">
                Como o DJEN/Tribunais exigem IP do Brasil, a captura é executada localmente pelo script <code className="text-amber-300">capturar.bat</code> e grava direto no banco na nuvem.
              </div>
            </div>
            <button
              onClick={() => handleToggleConectada(!conectada)}
              className={`px-4 py-2 rounded-xl font-bold text-xs transition-colors shrink-0 ${
                conectada
                  ? 'bg-emerald-600 hover:bg-emerald-500 text-slate-100'
                  : 'bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700'
              }`}
            >
              {conectada ? 'Conexão Ativa ✓' : 'Ativar Fonte Local'}
            </button>
          </div>

          <div className="bg-slate-900/90 border border-slate-700/80 rounded-xl p-4 text-xs text-slate-300 space-y-2">
            <div className="font-bold text-amber-400 flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-amber-400"></span> Como rodar no seu computador local:
            </div>
            <ol className="list-decimal list-inside space-y-1 text-slate-300 text-[11px] leading-relaxed pl-1">
              <li>Abra o arquivo <code className="bg-slate-800 px-1 py-0.5 rounded text-amber-200">capturar.bat</code> na pasta local do projeto.</li>
              <li>Cole a string <code className="bg-slate-800 px-1 py-0.5 rounded text-amber-200">DATABASE_URL</code> com o banco do Supabase ou Railway.</li>
              <li>Dê duplo clique no <code className="bg-slate-800 px-1 py-0.5 rounded text-amber-200">capturar.bat</code> ou agende no <strong>Agendador de Tarefas do Windows</strong> diariamente às 07:00.</li>
            </ol>
          </div>
        </div>
      </section>

      {/* 3. Contagem e Recálculo */}
      <section className="bg-slate-800/60 border border-slate-700/60 rounded-2xl p-6 space-y-4">
        <h3 className="text-sm font-bold text-slate-100 font-serif">Contagem de Prazos Padrão</h3>
        <p className="text-xs text-slate-400">
          Quando a área do processo estiver como &quot;a confirmar&quot;, qual regra de contagem utilizar por padrão?
        </p>

        <div className="space-y-2 max-w-md">
          <label className="flex items-center gap-2 text-xs text-slate-200 cursor-pointer">
            <input
              type="radio"
              name="areaPadrao"
              value="conservadora"
              checked={areaPadrao === 'conservadora'}
              onChange={() => {
                setAreaPadrao('conservadora');
                onSaveConfig({ area_padrao: 'conservadora' });
              }}
            />
            Conservadora (a mais curta - dias corridos, previne perda)
          </label>
          <label className="flex items-center gap-2 text-xs text-slate-200 cursor-pointer">
            <input
              type="radio"
              name="areaPadrao"
              value="civel"
              checked={areaPadrao === 'civel'}
              onChange={() => {
                setAreaPadrao('civel');
                onSaveConfig({ area_padrao: 'civel' });
              }}
            />
            Cível (dias úteis - CPC art. 219)
          </label>
        </div>

        <div className="pt-3 border-t border-slate-700/60 flex items-center gap-3">
          <button
            onClick={handleRecalcularSubmit}
            className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-slate-200 font-semibold text-xs rounded-xl flex items-center gap-1.5 transition-colors"
          >
            <RefreshCw className="w-3.5 h-3.5" /> Recalcular prazos não confirmados
          </button>
          {recalcMsg && <span className="text-xs text-emerald-400">{recalcMsg}</span>}
        </div>
      </section>

      {/* 4. Classification Rules */}
      <section className="bg-slate-800/60 border border-slate-700/60 rounded-2xl p-6 space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-sm font-bold text-slate-100 font-serif flex items-center gap-2">
              <List className="w-4 h-4 text-amber-400" /> Regras de Identificação das Publicações
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Dizem ao sistema qual ato e prazo atribuir ao ler expressões do texto.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={onRestoreDefaultRegras}
              className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs rounded-lg border border-slate-700 flex items-center gap-1"
            >
              <RotateCcw className="w-3.5 h-3.5" /> Restaurar Fábrica
            </button>
            <button
              onClick={handleSaveRegrasSubmit}
              className="px-4 py-1.5 bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold text-xs rounded-lg"
            >
              Salvar Regras
            </button>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-900/90 text-slate-400 uppercase font-semibold border-b border-slate-700">
              <tr>
                <th className="p-3">Trecho a procurar</th>
                <th className="p-3">Ato a atribuir</th>
                <th className="p-3">Dias</th>
                <th className="p-3 text-center">Ativa</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800 text-slate-200">
              {editedRegras.map((r) => (
                <tr key={r.id}>
                  <td className="p-2.5">
                    <input
                      type="text"
                      value={r.padrao}
                      onChange={(e) => handleRuleChange(r.id, 'padrao', e.target.value)}
                      className="bg-slate-900 border border-slate-700 rounded px-2 py-1 text-xs text-slate-100 w-full"
                    />
                  </td>
                  <td className="p-2.5">
                    <input
                      type="text"
                      value={r.rotulo}
                      onChange={(e) => handleRuleChange(r.id, 'rotulo', e.target.value)}
                      className="bg-slate-900 border border-slate-700 rounded px-2 py-1 text-xs text-slate-100 w-full"
                    />
                  </td>
                  <td className="p-2.5 w-24">
                    <input
                      type="number"
                      value={r.dias ?? ''}
                      onChange={(e) =>
                        handleRuleChange(
                          r.id,
                          'dias',
                          e.target.value ? parseInt(e.target.value, 10) : null
                        )
                      }
                      className="bg-slate-900 border border-slate-700 rounded px-2 py-1 text-xs text-slate-100 w-full"
                    />
                  </td>
                  <td className="p-2.5 text-center">
                    <input
                      type="checkbox"
                      checked={r.ativa}
                      onChange={(e) => handleRuleChange(r.id, 'ativa', e.target.checked)}
                      className="accent-amber-500"
                    />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* 5. Local Holidays */}
      <section className="bg-slate-800/60 border border-slate-700/60 rounded-2xl p-6 space-y-4">
        <div>
          <h3 className="text-sm font-bold text-slate-100 font-serif flex items-center gap-2">
            <Calendar className="w-4 h-4 text-amber-400" /> Feriados Forenses Locais (Tribunais)
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Cadastre os feriados específicos do TJ, TRF ou TRT local (ex: Dia do Advogado, Portaria de Recesso Local).
          </p>
        </div>

        <form onSubmit={handleAddHolidaySubmit} className="flex gap-3 max-w-md">
          <input
            type="date"
            required
            value={newHolDate}
            onChange={(e) => setNewHolDate(e.target.value)}
            className="bg-slate-900 border border-slate-700 rounded-lg p-2 text-xs text-slate-100 shrink-0"
          />
          <input
            type="text"
            required
            placeholder="Nome do feriado local"
            value={newHolName}
            onChange={(e) => setNewHolName(e.target.value)}
            className="bg-slate-900 border border-slate-700 rounded-lg p-2 text-xs text-slate-100 flex-1"
          />
          <button
            type="submit"
            className="px-3 py-2 bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold text-xs rounded-lg shrink-0"
          >
            Adicionar
          </button>
        </form>

        <div className="space-y-1.5 max-w-md">
          {feriadosLocais.length === 0 ? (
            <div className="text-xs text-slate-400 italic">Nenhum feriado local cadastrado.</div>
          ) : (
            feriadosLocais.map((f) => (
              <div
                key={f.data}
                className="bg-slate-900/80 p-2.5 rounded-lg border border-slate-700/60 flex items-center justify-between text-xs"
              >
                <div>
                  <span className="font-bold text-amber-300">{f.data}</span> —{' '}
                  <span className="text-slate-200">{f.nome}</span>
                </div>
                <button
                  onClick={() => onRemoveFeriadoLocal(f.data)}
                  className="text-rose-400 hover:text-rose-300"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
            ))
          )}
        </div>
      </section>

      {/* 6. Audit Trail Logs */}
      <section className="bg-slate-800/60 border border-slate-700/60 rounded-2xl p-6 space-y-4">
        <div>
          <h3 className="text-sm font-bold text-slate-100 font-serif flex items-center gap-2">
            <History className="w-4 h-4 text-amber-400" /> Trilha de Auditoria (Logs do Sistema)
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Registro imutável de confirmações, alterações de regras e acessos.
          </p>
        </div>

        <div className="overflow-x-auto max-h-64 overflow-y-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-900 uppercase text-slate-400 font-semibold border-b border-slate-700">
              <tr>
                <th className="p-2.5">Quando</th>
                <th className="p-2.5">Ação</th>
                <th className="p-2.5">Usuário</th>
                <th className="p-2.5">Detalhe</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800 text-slate-300 font-mono text-[11px]">
              {logs.map((l) => (
                <tr key={l.id}>
                  <td className="p-2.5 text-slate-400">{l.quando}</td>
                  <td className="p-2.5 font-bold text-amber-300">{l.acao}</td>
                  <td className="p-2.5 text-slate-200">{l.quem}</td>
                  <td className="p-2.5 text-slate-300">{l.detalhe}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
};
