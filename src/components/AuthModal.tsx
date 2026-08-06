import React, { useState } from 'react';
import { User } from '../types';
import { Scale, Lock, User as UserIcon } from 'lucide-react';

interface AuthModalProps {
  users: User[];
  onLogin: (user: User) => void;
  onCreateInitialUser: (u: string, n: string, p: string) => void;
}

export const AuthModal: React.FC<AuthModalProps> = ({
  users,
  onLogin,
  onCreateInitialUser,
}) => {
  const isFirstSetup = users.length === 0;

  // Login form state
  const [usuario, setUsuario] = useState('');
  const [senha, setSenha] = useState('');
  const [errorMsg, setErrorMsg] = useState('');

  // First setup form state
  const [nome, setNome] = useState('');
  const [s1, setS1] = useState('');
  const [s2, setS2] = useState('');

  const handleLoginSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const found = users.find((u) => u.usuario.toLowerCase() === usuario.toLowerCase().trim());
    if (found) {
      onLogin(found);
    } else {
      setErrorMsg('Usuário ou senha incorretos.');
    }
  };

  const handleFirstSetupSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!nome.trim() || !usuario.trim()) {
      setErrorMsg('Informe o nome e o usuário.');
      return;
    }
    if (s1 !== s2) {
      setErrorMsg('As senhas não conferem.');
      return;
    }
    if (s1.length < 4) {
      setErrorMsg('A senha deve ter pelo menos 4 caracteres.');
      return;
    }
    onCreateInitialUser(usuario.trim(), nome.trim(), s1);
  };

  return (
    <div className="fixed inset-0 bg-slate-950 flex items-center justify-center p-4 z-50">
      <div className="bg-slate-900 border border-slate-800 rounded-3xl p-8 max-w-md w-full shadow-2xl space-y-6">
        <div className="text-center space-y-2">
          <div className="w-12 h-12 rounded-2xl bg-amber-500/20 border border-amber-500/40 text-amber-400 flex items-center justify-center mx-auto">
            <Scale className="w-6 h-6" />
          </div>
          <h2 className="text-2xl font-bold font-serif text-slate-100 tracking-tight">
            Tempestivo
          </h2>
          <p className="text-xs text-slate-400 uppercase tracking-wider font-semibold">
            Controladoria de Prazos
          </p>
        </div>

        {isFirstSetup ? (
          <form onSubmit={handleFirstSetupSubmit} className="space-y-4">
            <div className="text-xs text-slate-300 bg-amber-500/10 border border-amber-500/30 p-3 rounded-xl">
              <strong>Primeiro Acesso:</strong> Crie o acesso do advogado responsável.
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Nome Completo</label>
              <input
                type="text"
                required
                placeholder="Dr. Fulano de Tal"
                value={nome}
                onChange={(e) => setNome(e.target.value)}
                className="w-full bg-slate-800 border border-slate-700 rounded-xl p-2.5 text-xs text-slate-100 focus:outline-none focus:border-amber-500"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Usuário</label>
              <input
                type="text"
                required
                placeholder="fulano"
                value={usuario}
                onChange={(e) => setUsuario(e.target.value)}
                className="w-full bg-slate-800 border border-slate-700 rounded-xl p-2.5 text-xs text-slate-100 focus:outline-none focus:border-amber-500"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Senha</label>
              <input
                type="password"
                required
                value={s1}
                onChange={(e) => setS1(e.target.value)}
                className="w-full bg-slate-800 border border-slate-700 rounded-xl p-2.5 text-xs text-slate-100 focus:outline-none focus:border-amber-500"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Repita a Senha</label>
              <input
                type="password"
                required
                value={s2}
                onChange={(e) => setS2(e.target.value)}
                className="w-full bg-slate-800 border border-slate-700 rounded-xl p-2.5 text-xs text-slate-100 focus:outline-none focus:border-amber-500"
              />
            </div>

            {errorMsg && <div className="text-xs text-rose-400">{errorMsg}</div>}

            <button
              type="submit"
              className="w-full bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold text-xs py-3 rounded-xl transition-colors shadow-lg shadow-amber-500/20"
            >
              Criar Acesso do Advogado
            </button>
          </form>
        ) : (
          <form onSubmit={handleLoginSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Usuário</label>
              <input
                type="text"
                required
                placeholder="fulano"
                value={usuario}
                onChange={(e) => setUsuario(e.target.value)}
                className="w-full bg-slate-800 border border-slate-700 rounded-xl p-2.5 text-xs text-slate-100 focus:outline-none focus:border-amber-500"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Senha</label>
              <input
                type="password"
                required
                value={senha}
                onChange={(e) => setSenha(e.target.value)}
                className="w-full bg-slate-800 border border-slate-700 rounded-xl p-2.5 text-xs text-slate-100 focus:outline-none focus:border-amber-500"
              />
            </div>

            {errorMsg && <div className="text-xs text-rose-400">{errorMsg}</div>}

            <button
              type="submit"
              className="w-full bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold text-xs py-3 rounded-xl transition-colors shadow-lg shadow-amber-500/20"
            >
              Entrar no Sistema
            </button>

            <div className="text-[11px] text-slate-500 text-center pt-2">
              Acessos e confirmações ficam registrados no log de auditoria.
            </div>
          </form>
        )}
      </div>
    </div>
  );
};
