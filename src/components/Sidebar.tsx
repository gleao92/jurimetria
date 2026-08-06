import React, { useState } from 'react';
import { User, Configuracao } from '../types';
import {
  Zap,
  Calendar,
  Clock,
  Folder,
  Settings,
  Download,
  Database,
  User as UserIcon,
  LogOut,
  ChevronDown,
  ChevronUp,
  Scale,
  ShieldCheck,
  UserPlus,
} from 'lucide-react';

interface SidebarProps {
  tela: string;
  setTela: (t: string) => void;
  currentUser: User;
  users: User[];
  podeConfirmar: boolean;
  configuracao: Configuracao;
  onFetchPublications: () => void;
  onResetSampleData: () => void;
  onChangePassword: (oldPw: string, newPw: string) => void;
  onCreateUser: (u: string, n: string, p: string, papel: 'advogado' | 'apoio') => void;
  onLogout: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  tela,
  setTela,
  currentUser,
  users,
  podeConfirmar,
  configuracao,
  onFetchPublications,
  onResetSampleData,
  onChangePassword,
  onCreateUser,
  onLogout,
}) => {
  const [accountOpen, setAccountOpen] = useState(false);
  const [sa, setSa] = useState('');
  const [sn, setSn] = useState('');
  const [msgPw, setMsgPw] = useState('');

  // Create user form state
  const [nu, setNu] = useState('');
  const [nn, setNn] = useState('');
  const [np, setNp] = useState('');
  const [npapel, setNpapel] = useState<'advogado' | 'apoio'>('apoio');
  const [msgUser, setMsgUser] = useState('');

  const menuItems = [
    { id: 'hoje', label: 'Hoje', icon: Zap },
    { id: 'agenda', label: 'Agenda', icon: Calendar },
    { id: 'prazos', label: 'Prazos', icon: Clock },
    { id: 'processos', label: 'Processos', icon: Folder },
  ];

  const handlePasswordSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!sa || !sn) {
      setMsgPw('Preencha os campos.');
      return;
    }
    onChangePassword(sa, sn);
    setMsgPw('Senha alterada com sucesso!');
    setSa('');
    setSn('');
  };

  const handleCreateUserSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!nu || !nn || !np) {
      setMsgUser('Preencha todos os campos.');
      return;
    }
    onCreateUser(nu, nn, np, npapel);
    setMsgUser('Acesso criado!');
    setNu('');
    setNn('');
    setNp('');
  };

  return (
    <aside className="w-full lg:w-64 bg-slate-900 border-r border-slate-800 flex flex-col shrink-0 min-h-screen">
      {/* Brand Header */}
      <div className="p-5 border-b border-slate-800 flex items-center gap-3">
        <div className="w-9 h-9 rounded-xl bg-amber-500/20 border border-amber-500/40 flex items-center justify-center text-amber-400">
          <Scale className="w-5 h-5" />
        </div>
        <div>
          <h2 className="text-lg font-bold font-serif text-slate-100 tracking-tight leading-none">
            Tempestivo
          </h2>
          <span className="text-[11px] text-slate-400 font-sans tracking-wide uppercase mt-1 block">
            Controladoria
          </span>
        </div>
      </div>

      {/* Navigation Links */}
      <div className="p-4 space-y-1 flex-1">
        <div className="px-3 py-1.5 text-[11px] font-semibold text-slate-500 uppercase tracking-wider">
          Painel
        </div>
        {menuItems.map((item) => {
          const Icon = item.icon;
          const isActive = tela === item.id;
          return (
            <button
              key={item.id}
              onClick={() => setTela(item.id)}
              className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                isActive
                  ? 'bg-amber-500/15 text-amber-300 border border-amber-500/30'
                  : 'text-slate-300 hover:bg-slate-800 hover:text-slate-100'
              }`}
            >
              <Icon className={`w-4 h-4 ${isActive ? 'text-amber-400' : 'text-slate-400'}`} />
              {item.label}
            </button>
          );
        })}

        {podeConfirmar && (
          <>
            <div className="px-3 pt-4 pb-1.5 text-[11px] font-semibold text-slate-500 uppercase tracking-wider">
              Sistema
            </div>
            <button
              onClick={() => setTela('ajustes')}
              className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                tela === 'ajustes'
                  ? 'bg-amber-500/15 text-amber-300 border border-amber-500/30'
                  : 'text-slate-300 hover:bg-slate-800 hover:text-slate-100'
              }`}
            >
              <Settings className={`w-4 h-4 ${tela === 'ajustes' ? 'text-amber-400' : 'text-slate-400'}`} />
              Ajustes
            </button>
          </>
        )}

        {/* Publicações / Source Section */}
        <div className="pt-6">
          <div className="px-3 py-1.5 text-[11px] font-semibold text-slate-500 uppercase tracking-wider">
            Captura de Publicações
          </div>

          <div className="px-3 py-2.5 bg-slate-800/70 rounded-lg border border-slate-700/50 mb-2">
            <div className="text-xs text-emerald-400 font-semibold uppercase flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
              Captura Local Ativa
            </div>
            <div className="text-[11px] text-slate-300 mt-1">
              OAB {configuracao.oab_numero}/{configuracao.oab_uf}
            </div>
            <div className="text-[10px] text-slate-400 mt-0.5">
              Execução automática via <code className="bg-slate-900 px-1 py-0.5 rounded text-amber-300">capturar.bat</code> (IP Brasil)
            </div>
          </div>
        </div>
      </div>

      {/* User Account Bar */}
      <div className="p-4 border-t border-slate-800 bg-slate-950/60">
        <button
          onClick={() => setAccountOpen(!accountOpen)}
          className="w-full flex items-center justify-between text-left p-2 rounded-lg hover:bg-slate-800/80 transition-colors"
        >
          <div className="flex items-center gap-2.5 min-w-0">
            <div className="w-8 h-8 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center text-slate-300 font-semibold text-xs shrink-0">
              {currentUser.nome.charAt(0)}
            </div>
            <div className="min-w-0">
              <div className="text-xs font-semibold text-slate-200 truncate">{currentUser.nome}</div>
              <div className="text-[10px] text-amber-400/90 capitalize flex items-center gap-1">
                <ShieldCheck className="w-3 h-3 text-amber-400" /> {currentUser.papel}
              </div>
            </div>
          </div>
          {accountOpen ? (
            <ChevronUp className="w-4 h-4 text-slate-400 shrink-0" />
          ) : (
            <ChevronDown className="w-4 h-4 text-slate-400 shrink-0" />
          )}
        </button>

        {accountOpen && (
          <div className="mt-3 pt-3 border-t border-slate-800/80 space-y-4 text-xs">
            {/* Change Password Form */}
            <form onSubmit={handlePasswordSubmit} className="space-y-2">
              <span className="font-semibold text-slate-300 block text-[11px]">Minha conta</span>
              <input
                type="password"
                placeholder="Senha atual"
                value={sa}
                onChange={(e) => setSa(e.target.value)}
                className="w-full bg-slate-900 border border-slate-700 rounded px-2.5 py-1.5 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-amber-500"
              />
              <input
                type="password"
                placeholder="Nova senha"
                value={sn}
                onChange={(e) => setSn(e.target.value)}
                className="w-full bg-slate-900 border border-slate-700 rounded px-2.5 py-1.5 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-amber-500"
              />
              <button
                type="submit"
                className="w-full bg-slate-800 hover:bg-slate-700 text-slate-200 py-1.5 rounded font-medium transition-colors"
              >
                Alterar senha
              </button>
              {msgPw && <div className="text-[10px] text-emerald-400">{msgPw}</div>}
            </form>

            {/* Manage Users (if lawyer) */}
            {podeConfirmar && (
              <div className="pt-2 border-t border-slate-800/80 space-y-2">
                <span className="font-semibold text-slate-300 block text-[11px]">Quem tem acesso</span>
                <div className="space-y-1 max-h-24 overflow-y-auto pr-1">
                  {users.map((u) => (
                    <div key={u.id} className="text-[11px] text-slate-400 truncate">
                      • {u.nome} — <span className="capitalize">{u.papel}</span>
                    </div>
                  ))}
                </div>

                <form onSubmit={handleCreateUserSubmit} className="space-y-2 pt-1">
                  <span className="font-medium text-slate-400 text-[10px] flex items-center gap-1">
                    <UserPlus className="w-3 h-3 text-amber-400" /> Criar novo acesso
                  </span>
                  <input
                    type="text"
                    placeholder="Nome"
                    value={nn}
                    onChange={(e) => setNn(e.target.value)}
                    className="w-full bg-slate-900 border border-slate-700 rounded px-2.5 py-1 text-[11px] text-slate-100 placeholder-slate-500"
                  />
                  <input
                    type="text"
                    placeholder="Usuário"
                    value={nu}
                    onChange={(e) => setNu(e.target.value)}
                    className="w-full bg-slate-900 border border-slate-700 rounded px-2.5 py-1 text-[11px] text-slate-100 placeholder-slate-500"
                  />
                  <input
                    type="password"
                    placeholder="Senha"
                    value={np}
                    onChange={(e) => setNp(e.target.value)}
                    className="w-full bg-slate-900 border border-slate-700 rounded px-2.5 py-1 text-[11px] text-slate-100 placeholder-slate-500"
                  />
                  <select
                    value={npapel}
                    onChange={(e) => setNpapel(e.target.value as 'advogado' | 'apoio')}
                    className="w-full bg-slate-900 border border-slate-700 rounded px-2 py-1 text-[11px] text-slate-200"
                  >
                    <option value="advogado">Advogado (pode confirmar)</option>
                    <option value="apoio">Apoio (somente consulta)</option>
                  </select>
                  <button
                    type="submit"
                    className="w-full bg-slate-800 hover:bg-slate-700 text-slate-200 py-1 rounded text-[11px] font-medium"
                  >
                    Criar acesso
                  </button>
                  {msgUser && <div className="text-[10px] text-emerald-400">{msgUser}</div>}
                </form>
              </div>
            )}

            <button
              onClick={onLogout}
              className="w-full bg-rose-950/40 hover:bg-rose-900/60 text-rose-200 border border-rose-800/40 py-1.5 rounded flex items-center justify-center gap-1.5 text-xs transition-colors"
            >
              <LogOut className="w-3.5 h-3.5" /> Sair
            </button>
          </div>
        )}
      </div>
    </aside>
  );
};
