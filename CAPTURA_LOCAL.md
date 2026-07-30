# Captura diária no computador do escritório

## Por que a captura fica aqui e o painel na nuvem

O DJEN recusa consulta vinda de servidor fora do Brasil — foi o `403` que
apareceu no Railway. A mesma consulta funciona a partir de uma conexão
brasileira, então a captura roda neste computador e grava direto no banco da
nuvem. O painel na web lê esse mesmo banco e mostra tudo na hora.

Não é remendo: separar captura de exibição é arquitetura comum. O que a
captura precisa é de um IP confiável para o tribunal; o painel precisa estar
acessível de qualquer lugar. São exigências diferentes.

---

## Instalação (uma vez, ~10 minutos)

### 1. Ter os arquivos e as dependências

Na pasta do projeto, no PowerShell:

```powershell
pip install -r requirements.txt
```

### 2. Pegar a string do banco

No Railway → serviço **web** → aba **Variables** → copie o valor de
`DATABASE_URL`.

### 3. Colar no `capturar.bat`

Abra o `capturar.bat` no Bloco de Notas e substitua:

```
set DATABASE_URL=COLE_AQUI_A_STRING_DO_BANCO
```

pela string copiada. Salve.

> A senha fica em texto neste arquivo, neste computador. Para uma máquina de
> escritório é proporcional — quem tem acesso a ela já teria acesso ao
> sistema. Se preferir não deixar ali, apague essa linha e defina
> `DATABASE_URL` nas Variáveis de Ambiente do Windows.

### 4. Testar

Dê **dois cliques** no `capturar.bat`. Deve aparecer:

```
Tempestivo - buscando publicacoes...
  OAB ....... 61423/GO
  Janela .... últimos 15 dias
  Gravando em banco na nuvem (DATABASE_URL definida)

Consultando o DJEN...
  63 publicações recebidas.

Resultado:
  publicações novas ....... 12
  prazos criados .......... 9
```

Abra o painel na web: os prazos novos estão lá.

Se aparecer `403`, confirme que está rodando na conexão do escritório e não
por VPN estrangeira.

---

## Agendar para rodar sozinho

**Agendador de Tarefas do Windows** (procure no menu Iniciar):

1. **Criar Tarefa Básica** → nome: `Tempestivo - captura`
2. **Disparador**: Diariamente, às **07:00**
3. **Ação**: Iniciar um programa
   - Programa: o caminho completo do `capturar.bat`
     (ex.: `C:\tempestivo\capturar.bat`)
   - Iniciar em: a pasta do projeto (ex.: `C:\tempestivo`)
4. Concluir. Em **Propriedades**, marque
   *"Executar estando o usuário conectado ou não"* e
   *"Executar com privilégios mais altos"*.

### Se o computador estiver desligado no horário

Não há perda. A captura busca uma janela de **15 dias para trás** — a próxima
execução recupera tudo que ficou para trás. Rodar duas vezes também não
duplica nada: publicação já vista é ignorada pelo banco.

Ainda assim, em **Propriedades → Disparadores → Editar**, marque
*"Executar a tarefa assim que possível após um início agendado ter sido
perdido"*. Assim ela roda ao ligar o computador.

---

## Como saber que está funcionando

No painel, em **Ajustes → Registro de atividade**, cada captura deixa registro.
Se passarem dois dias sem nenhum, a tarefa parou — confira o Agendador.

Vale a combinação com o advogado: se o painel não mostrar publicação nova por
três dias úteis seguidos, alguma coisa está errada e é para avisar. Sistema de
prazo que falha em silêncio é pior que sistema nenhum.

---

## Quando isso deixa de ser necessário

No dia em que o sistema rodar num servidor **no Brasil** (uma VM em São Paulo,
por exemplo), a captura volta para dentro dele e este script deixa de fazer
falta. Enquanto o painel estiver em servidor estrangeiro, ele é o caminho.
