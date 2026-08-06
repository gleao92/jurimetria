import {
  collection,
  doc,
  onSnapshot,
  setDoc,
  deleteDoc,
  writeBatch,
} from 'firebase/firestore';
import { db, handleFirestoreError, OperationType } from './firebase';
import {
  Processo,
  Prazo,
  Compromisso,
  Regra,
  FeriadoLocal,
  Configuracao,
  LogEntry,
} from '../types';

export function subscribeToCollection<T>(
  collectionName: string,
  onData: (items: T[]) => void
) {
  try {
    return onSnapshot(
      collection(db, collectionName),
      (snapshot) => {
        const items: T[] = snapshot.docs.map((d) => d.data() as T);
        onData(items);
      },
      (error) => {
        handleFirestoreError(error, OperationType.LIST, collectionName);
      }
    );
  } catch (error) {
    handleFirestoreError(error, OperationType.LIST, collectionName);
    return () => {};
  }
}

export async function saveProcessoToFirestore(processo: Processo) {
  const path = `processos/${processo.numero.replace(/[/.]/g, '_')}`;
  try {
    await setDoc(doc(db, 'processos', processo.numero.replace(/[/.]/g, '_')), processo);
  } catch (error) {
    handleFirestoreError(error, OperationType.WRITE, path);
  }
}

export async function saveProcessosBatchToFirestore(processos: Processo[]) {
  try {
    const batch = writeBatch(db);
    processos.forEach((p) => {
      const docRef = doc(db, 'processos', p.numero.replace(/[/.]/g, '_'));
      batch.set(docRef, p);
    });
    await batch.commit();
  } catch (error) {
    handleFirestoreError(error, OperationType.WRITE, 'processos');
  }
}

export async function savePrazoToFirestore(prazo: Prazo) {
  const path = `prazos/${prazo.id}`;
  try {
    await setDoc(doc(db, 'prazos', prazo.id), prazo);
  } catch (error) {
    handleFirestoreError(error, OperationType.WRITE, path);
  }
}

export async function savePrazosBatchToFirestore(prazos: Prazo[]) {
  try {
    const batch = writeBatch(db);
    prazos.forEach((p) => {
      const docRef = doc(db, 'prazos', p.id);
      batch.set(docRef, p);
    });
    await batch.commit();
  } catch (error) {
    handleFirestoreError(error, OperationType.WRITE, 'prazos');
  }
}

export async function deletePrazoFromFirestore(prazoId: string) {
  const path = `prazos/${prazoId}`;
  try {
    await deleteDoc(doc(db, 'prazos', prazoId));
  } catch (error) {
    handleFirestoreError(error, OperationType.DELETE, path);
  }
}

export async function saveCompromissoToFirestore(compromisso: Compromisso) {
  const path = `compromissos/${compromisso.id}`;
  try {
    await setDoc(doc(db, 'compromissos', compromisso.id), compromisso);
  } catch (error) {
    handleFirestoreError(error, OperationType.WRITE, path);
  }
}

export async function saveRegrasBatchToFirestore(regras: Regra[]) {
  try {
    const batch = writeBatch(db);
    regras.forEach((r) => {
      const docRef = doc(db, 'regras', r.id);
      batch.set(docRef, r);
    });
    await batch.commit();
  } catch (error) {
    handleFirestoreError(error, OperationType.WRITE, 'regras');
  }
}

export async function saveFeriadoToFirestore(feriado: FeriadoLocal) {
  const path = `feriados/${feriado.data}`;
  try {
    await setDoc(doc(db, 'feriados', feriado.data), feriado);
  } catch (error) {
    handleFirestoreError(error, OperationType.WRITE, path);
  }
}

export async function deleteFeriadoFromFirestore(dateStr: string) {
  const path = `feriados/${dateStr}`;
  try {
    await deleteDoc(doc(db, 'feriados', dateStr));
  } catch (error) {
    handleFirestoreError(error, OperationType.DELETE, path);
  }
}

export async function saveConfiguracaoToFirestore(config: Configuracao) {
  const path = 'configuracao/geral';
  try {
    await setDoc(doc(db, 'configuracao', 'geral'), config);
  } catch (error) {
    handleFirestoreError(error, OperationType.WRITE, path);
  }
}

export async function saveLogToFirestore(log: LogEntry) {
  const path = `logs/${log.id}`;
  try {
    await setDoc(doc(db, 'logs', log.id), log);
  } catch (error) {
    handleFirestoreError(error, OperationType.WRITE, path);
  }
}
