import React, { useState, useEffect } from 'react';
import {
  AppState,
  getInitialState,
  saveState,
  INITIAL_USER,
} from './lib/store';
import {
  Prazo,
  Compromisso,
  Processo,
  Configuracao,
  Regra,
  FeriadoLocal,
  User,
  AreaProcesso,
  LogEntry,
} from './types';
import { calcularPrazo } from './lib/prazosEngine';
import { classificarPublicacao, REGRAS_PADRAO } from './lib/extrator';
import { Sidebar } from './components/Sidebar';
import { Header } from './components/Header';
import { HojeView } from './components/HojeView';
import { AgendaView } from './components/AgendaView';
import { PrazosView } from './components/PrazosView';
import { ProcessosView } from './components/ProcessosView';
import { AjustesView } from './components/AjustesView';
import { AuthModal } from './components/AuthModal';
import {
  subscribeToCollection,
  savePrazoToFirestore,
  savePrazosBatchToFirestore,
  deletePrazoFromFirestore,
  saveCompromissoToFirestore,
  saveProcessosBatchToFirestore,
  saveRegrasBatchToFirestore,
  saveFeriadoToFirestore,
  deleteFeriadoFromFirestore,
  saveConfiguracaoToFirestore,
  saveLogToFirestore,
} from './lib/firestoreSync';

export const App: React.FC = () => {
  const [state, setState] = useState<AppState>(getInitialState);
  const [tela, setTela] = useState<string>('hoje');

  // Sync state changes to LocalStorage
  useEffect(() => {
    saveState(state);
  }, [state]);

  // Subscribe to Firestore collections for real-time synchronization
  useEffect(() => {
    const unsubPrazos = subscribeToCollection<Prazo>('prazos', (items) => {
      if (items && items.length > 0) {
        setState((prev) => ({ ...prev, prazos: items }));
      }
    });

    const unsubProcessos = subscribeToCollection<Processo>('processos', (items) => {
      if (items && items.length > 0) {
        setState((prev) => ({ ...prev, processos: items }));
      }
    });

    const unsubCompromissos = subscribeToCollection<Compromisso>('compromissos', (items) => {
      if (items && items.length > 0) {
        setState((prev) => ({ ...prev, compromissos: items }));
      }
    });

    return () => {
      unsubPrazos();
      unsubProcessos();
      unsubCompromissos();
    };
  }, []);

  const {
    currentUser,
    users,
    processos,
    prazos,
    compromissos,
    regras,
    feriadosLocais,
    configuracao,
    logs,
  } = state;

  const podeConfirmar = currentUser?.papel === 'advogado';

  // Helper to append log
  const appendLog = (acao: string, detalhe: string) => {
    const newLog: LogEntry = {
      id: `l_${Date.now()}`,
      quando: new Date().toISOString().replace('T', ' ').substring(0, 19),
      acao,
      quem: currentUser?.nome || 'Sistema',
      detalhe,
    };
    saveLogToFirestore(newLog);
    return [newLog, ...logs];
  };

  // Helper for feriados local map
  const feriadosLocaisMap: Record<string, string> = {};
  feriadosLocais.forEach((f) => {
    feriadosLocaisMap[f.data] = f.nome;
  });

  // Action Handlers
  const handleConfirmPrazo = (id: string, updatedData: Partial<Prazo>) => {
    const targetPrazo = prazos.find((p) => p.id === id);
    if (targetPrazo) {
      const updated: Prazo = {
        ...targetPrazo,
        ...updatedData,
        confirmado_por: currentUser?.nome || 'Advogado',
        confirmado_em: new Date().toISOString(),
      };
      savePrazoToFirestore(updated);
    }

    const updatedPrazos = prazos.map((p) => {
      if (p.id === id) {
        return {
          ...p,
          ...updatedData,
          confirmado_por: currentUser?.nome || 'Advogado',
          confirmado_em: new Date().toISOString(),
        };
      }
      return p;
    });

    const newLogs = appendLog(
      'prazo_confirmado',
      `Prazo #${id} (${targetPrazo?.ato || 'ato'}) confirmado para ${targetPrazo?.processo}`
    );

    setState({ ...state, prazos: updatedPrazos, logs: newLogs });
  };

  const handleMarcarCumprido = (id: string) => {
    const targetPrazo = prazos.find((p) => p.id === id);
    if (targetPrazo) {
      const updated: Prazo = {
        ...targetPrazo,
        status: 'cumprido' as const,
        cumprido_por: currentUser?.nome || 'Advogado',
        cumprido_em: new Date().toISOString(),
      };
      savePrazoToFirestore(updated);
    }

    const updatedPrazos = prazos.map((p) => {
      if (p.id === id) {
        return {
          ...p,
          status: 'cumprido' as const,
          cumprido_por: currentUser?.nome || 'Advogado',
          cumprido_em: new Date().toISOString(),
        };
      }
      return p;
    });

    const newLogs = appendLog(
      'prazo_cumprido',
      `Prazo #${id} (${targetPrazo?.ato}) marcado como cumprido`
    );

    setState({ ...state, prazos: updatedPrazos, logs: newLogs });
  };

  const handleDeletePrazo = (id: string) => {
    deletePrazoFromFirestore(id);
    const updatedPrazos = prazos.filter((p) => p.id !== id);
    const newLogs = appendLog('prazo_excluido', `Prazo #${id} removido`);
    setState({ ...state, prazos: updatedPrazos, logs: newLogs });
  };

  const handleAddManualPrazo = (pData: Omit<Prazo, 'id'>) => {
    const newId = `pzp_m_${Date.now()}`;
    const dataDisp = new Date(pData.data_disponibilizacao + 'T00:00:00');

    const calc = calcularPrazo(
      dataDisp,
      pData.dias_prazo,
      pData.area === 'a_confirmar' ? 'civel' : pData.area,
      3,
      '',
      'disponibilizacao',
      feriadosLocaisMap
    );

    const newPrazo: Prazo = {
      ...pData,
      id: newId,
      publicacao: calc.publicacao.toISOString().split('T')[0],
      inicio_contagem: calc.inicio_contagem.toISOString().split('T')[0],
      data_fatal: calc.data_fatal.toISOString().split('T')[0],
      prazo_interno: calc.prazo_interno.toISOString().split('T')[0],
      contagem_explicacao: calc.contagem,
    };

    savePrazoToFirestore(newPrazo);
    const newLogs = appendLog('prazo_manual_criado', `Prazo manual criado para ${pData.processo}`);
    setState({ ...state, prazos: [newPrazo, ...prazos], logs: newLogs });
  };

  const handleAddCompromisso = (cData: Omit<Compromisso, 'id'>) => {
    const newComp: Compromisso = {
      ...cData,
      id: `comp_${Date.now()}`,
    };
    saveCompromissoToFirestore(newComp);
    const newLogs = appendLog('compromisso_criado', `Compromisso "${cData.titulo}" criado`);
    setState({ ...state, compromissos: [newComp, ...compromissos], logs: newLogs });
  };

  const handleUpdateProcessos = (updatedProcs: Processo[]) => {
    // Recalculate pending deadlines if process areas changed
    const procMap = new Map(updatedProcs.map((p) => [p.numero, p]));

    const updatedPrazos = prazos.map((p) => {
      if (p.status === 'pendente_revisao') {
        const proc = procMap.get(p.processo);
        if (proc && proc.area !== p.area) {
          const dataDisp = new Date(p.data_disponibilizacao + 'T00:00:00');
          const calc = calcularPrazo(
            dataDisp,
            p.dias_prazo,
            proc.area === 'a_confirmar' ? 'civel' : proc.area,
            3,
            '',
            'disponibilizacao',
            feriadosLocaisMap
          );

          return {
            ...p,
            area: proc.area,
            cliente: proc.cliente || p.cliente,
            publicacao: calc.publicacao.toISOString().split('T')[0],
            inicio_contagem: calc.inicio_contagem.toISOString().split('T')[0],
            data_fatal: calc.data_fatal.toISOString().split('T')[0],
            prazo_interno: calc.prazo_interno.toISOString().split('T')[0],
            contagem_explicacao: calc.contagem,
          };
        }
      }
      return p;
    });

    const newLogs = appendLog('processos_atualizados', `${updatedProcs.length} processos salvos`);
    saveProcessosBatchToFirestore(updatedProcs);
    savePrazosBatchToFirestore(updatedPrazos);
    setState({
      ...state,
      processos: updatedProcs,
      prazos: updatedPrazos,
      logs: newLogs,
    });
  };

  const handleImportProcessosText = (text: string, areaPadraoInput: AreaProcesso) => {
    const cnjRegex = /\b\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}\b/g;
    const matches = text.match(cnjRegex) || [];
    const uniqueNums = Array.from(new Set(matches));

    if (uniqueNums.length === 0) return;

    const existingNums = new Set(processos.map((p) => p.numero));
    const newProcs: Processo[] = [];

    uniqueNums.forEach((num) => {
      if (!existingNums.has(num)) {
        newProcs.push({
          numero: num,
          cliente: 'Novo Cliente',
          area: areaPadraoInput,
          sistema: 'PJe',
          tribunal: 'TJGO',
          assunto: 'Importado em lote',
        });
      }
    });

    const updatedProcessos = [...processos, ...newProcs];
    saveProcessosBatchToFirestore(newProcs);
    const newLogs = appendLog('processos_importados', `${newProcs.length} processos importados`);

    setState({ ...state, processos: updatedProcessos, logs: newLogs });
  };

  const handleRecalcularPendentes = () => {
    const procMap = new Map(processos.map((p) => [p.numero, p]));

    const updatedPrazos = prazos.map((p) => {
      if (p.status === 'pendente_revisao') {
        const proc = procMap.get(p.processo);
        const areaToUse = proc ? proc.area : p.area;

        const { ato, dias, contagemForcada } = classificarPublicacao(p.teor || '', regras);

        const dataDisp = new Date(p.data_disponibilizacao + 'T00:00:00');
        const calc = calcularPrazo(
          dataDisp,
          dias,
          areaToUse === 'a_confirmar' ? 'civel' : areaToUse,
          3,
          contagemForcada,
          'disponibilizacao',
          feriadosLocaisMap
        );

        return {
          ...p,
          ato,
          dias_prazo: dias,
          area: areaToUse,
          publicacao: calc.publicacao.toISOString().split('T')[0],
          inicio_contagem: calc.inicio_contagem.toISOString().split('T')[0],
          data_fatal: calc.data_fatal.toISOString().split('T')[0],
          prazo_interno: calc.prazo_interno.toISOString().split('T')[0],
          contagem_explicacao: calc.contagem,
        };
      }
      return p;
    });

    savePrazosBatchToFirestore(updatedPrazos.filter((p) => p.status === 'pendente_revisao'));
    const newLogs = appendLog('prazos_recalculados', 'Recálculo de prazos pendentes executado');
    setState({ ...state, prazos: updatedPrazos, logs: newLogs });
  };

  const handleFetchPublications = () => {
    const newLogs = appendLog('busca_djen', 'Busca de novas publicações realizada');
    setState({ ...state, logs: newLogs });
  };

  const handleResetSampleData = () => {
    localStorage.removeItem('tempestivo_data_v1');
    setState(getInitialState());
  };

  const handleSaveConfig = (newCfg: Partial<Configuracao>) => {
    const updatedCfg = { ...configuracao, ...newCfg };
    saveConfiguracaoToFirestore(updatedCfg);
    const newLogs = appendLog('configuracao_salva', 'Configurações de fonte salvas');
    setState({ ...state, configuracao: updatedCfg, logs: newLogs });
  };

  const handleSaveRegras = (newRegras: Regra[]) => {
    saveRegrasBatchToFirestore(newRegras);
    const newLogs = appendLog('regras_salvas', `${newRegras.length} regras atualizadas`);
    setState({ ...state, regras: newRegras, logs: newLogs });
  };

  const handleRestoreDefaultRegras = () => {
    saveRegrasBatchToFirestore(REGRAS_PADRAO);
    const newLogs = appendLog('regras_restauradas', 'Regras de fábrica restauradas');
    setState({ ...state, regras: REGRAS_PADRAO, logs: newLogs });
  };

  const handleAddFeriadoLocal = (f: FeriadoLocal) => {
    const updated = [...feriadosLocais, f];
    saveFeriadoToFirestore(f);
    const newLogs = appendLog('feriado_adicionado', `Feriado local ${f.nome} (${f.data}) cadastrado`);
    setState({ ...state, feriadosLocais: updated, logs: newLogs });
  };

  const handleRemoveFeriadoLocal = (dateStr: string) => {
    const updated = feriadosLocais.filter((f) => f.data !== dateStr);
    deleteFeriadoFromFirestore(dateStr);
    const newLogs = appendLog('feriado_removido', `Feriado local ${dateStr} removido`);
    setState({ ...state, feriadosLocais: updated, logs: newLogs });
  };

  const handleChangePassword = (oldPw: string, newPw: string) => {
    const newLogs = appendLog('senha_alterada', 'Senha alterada pelo usuário');
    setState({ ...state, logs: newLogs });
  };

  const handleCreateUser = (u: string, n: string, p: string, papel: 'advogado' | 'apoio') => {
    const newUser: User = {
      id: `u_${Date.now()}`,
      usuario: u,
      nome: n,
      papel,
    };
    const newLogs = appendLog('usuario_criado', `Acesso criado para ${n} (${papel})`);
    setState({ ...state, users: [...users, newUser], logs: newLogs });
  };

  const handleLogout = () => {
    setState({ ...state, currentUser: null });
  };

  const handleLogin = (user: User) => {
    const newLogs = appendLog('login', `Usuário ${user.nome} entrou`);
    setState({ ...state, currentUser: user, logs: newLogs });
  };

  const handleCreateInitialUser = (u: string, n: string, p: string) => {
    const initialAdv: User = {
      id: 'u_init',
      usuario: u,
      nome: n,
      papel: 'advogado',
    };
    const newLogs = appendLog('primeiro_acesso', `Primeiro acesso criado: ${n}`);
    setState({
      ...state,
      currentUser: initialAdv,
      users: [initialAdv],
      logs: newLogs,
    });
  };

  if (!currentUser) {
    return (
      <AuthModal
        users={users}
        onLogin={handleLogin}
        onCreateInitialUser={handleCreateInitialUser}
      />
    );
  }

  return (
    <div className="flex flex-col lg:flex-row min-h-screen bg-slate-900 text-slate-100 font-sans">
      {/* Left Sidebar */}
      <Sidebar
        tela={tela}
        setTela={setTela}
        currentUser={currentUser}
        users={users}
        podeConfirmar={podeConfirmar}
        configuracao={configuracao}
        onFetchPublications={handleFetchPublications}
        onResetSampleData={handleResetSampleData}
        onChangePassword={handleChangePassword}
        onCreateUser={handleCreateUser}
        onLogout={handleLogout}
      />

      {/* Main Workspace Area */}
      <main className="flex-1 p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto w-full">
        <Header tela={tela} prazos={prazos} fonteConectada={configuracao.conectada} />

        {tela === 'hoje' && (
          <HojeView
            prazos={prazos}
            compromissos={compromissos}
            currentUser={currentUser}
            podeConfirmar={podeConfirmar}
            onConfirmPrazo={handleConfirmPrazo}
            onMarcarCumprido={handleMarcarCumprido}
            onDeletePrazo={handleDeletePrazo}
            feriadosLocaisMap={feriadosLocaisMap}
          />
        )}

        {tela === 'agenda' && (
          <AgendaView
            prazos={prazos}
            compromissos={compromissos}
            onAddCompromisso={handleAddCompromisso}
          />
        )}

        {tela === 'prazos' && (
          <PrazosView
            prazos={prazos}
            compromissos={compromissos}
            podeConfirmar={podeConfirmar}
            onAddManualPrazo={handleAddManualPrazo}
            onConfirmPrazo={handleConfirmPrazo}
            onMarcarCumprido={handleMarcarCumprido}
          />
        )}

        {tela === 'processos' && (
          <ProcessosView
            processos={processos}
            podeConfirmar={podeConfirmar}
            onUpdateProcessos={handleUpdateProcessos}
            onImportProcessosText={handleImportProcessosText}
          />
        )}

        {tela === 'ajustes' && (
          <AjustesView
            configuracao={configuracao}
            regras={regras}
            feriadosLocais={feriadosLocais}
            logs={logs}
            currentUser={currentUser}
            onSaveConfig={handleSaveConfig}
            onSaveRegras={handleSaveRegras}
            onRestoreDefaultRegras={handleRestoreDefaultRegras}
            onAddFeriadoLocal={handleAddFeriadoLocal}
            onRemoveFeriadoLocal={handleRemoveFeriadoLocal}
            onRecalcularPendentes={handleRecalcularPendentes}
          />
        )}
      </main>
    </div>
  );
};

export default App;
