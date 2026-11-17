# 🌤 Clima Windy → n8n → WAHA → WhatsApp

Robô de monitoramento meteorológico: captura o **mapa e a previsão do Windy**
com Playwright, gera um relatório em texto e manda **imagem + texto no seu
privado ou num grupo do WhatsApp** via WAHA, tudo orquestrado pelo **n8n**.

Localização do mapa, destino (seu número ou um grupo) e sessão do WAHA são
configurados em **`.env`** (arquivo local, não versionado) e no workflow — o
repositório **não contém dados pessoais**.

## Arquitetura

```
┌────────────────────────┐  POST :8000/relatorio   ┌──────────────────────┐
│  n8n (Docker :5678)    │ ──────────────────────► │  api.py (Python)      │
│  • Agendado (hora)     │ ◄────────────────────── │  Playwright + Windy   │
│  • Executar na mão     │  {resumo, texto,        │  (máquina local,      │
└───────────┬────────────┘    imagem_base64}      │   porta 8000)         │
            │                                     └──────────────────────┘
            │  POST :3000/api/sendImage  +  /api/sendText
            ▼
┌────────────────────────┐        WhatsApp        ┌──────────────────────┐
│  WAHA (Docker :3000)   │ ─────────────────────► │  SEU NÚMERO ou GRUPO  │
│  sessão WORKING        │                        │                       │
└────────────────────────┘                        └──────────────────────┘
```

## Arquivos

| Arquivo | O que é |
|---|---|
| `scraper.py` | Scraper do Windy. Expõe `gerar_relatorio()`; `python scraper.py` continua funcionando (salva em `prints_windy/`) |
| `api.py` | Servidor HTTP local (porta 8000) que o n8n chama. Devolve JSON com `resumo`, `texto` e `imagem_base64` |
| `config.py` | Carrega o `.env` (sem dependências externas). Expõe `obter()` / `obter_int()` e as validações `obter_coordenadas()` / `obter_destinatario()` (falham cedo com mensagem clara se o `.env` estiver errado) |
| `iniciar.bat` | Sobe a API com 1 clique (Windows). Se não existir `.env`, cria a partir do modelo |
| `n8n_workflow.json` | Export do workflow principal pra referência / reimport no n8n (**vem com placeholders**) |
| `n8n_error_workflow.json` | Workflow de **alerta de falha** (Error Trigger → WhatsApp). Vincule como *Error Workflow* do principal |
| `tests/` | Testes pytest do `scraper.py` e do `config.py` (sem internet/navegador) |
| `teste_envio.py` | Teste de ponta a ponta via Python (gera relatório e manda no WhatsApp) |
| `.env.example` | Modelo de configuração — copie para `.env` e edite com seus dados |
| `.env` | **Seus dados** (número, sessão, coordenadas). Local, ignorado pelo git |
| `requirements.txt` | Dependências (`pip install -r requirements.txt`) — travadas pra bater com a imagem Docker |
| `requirements-dev.txt` | Dependências de desenvolvimento (pytest + ruff) |
| `ruff.toml` | Regras do linter fixadas (local e CI usam as mesmas) |
| `pyproject.toml` | Config do pytest (`pythonpath = ["."]`) — faz o `pytest` achar os módulos do projeto |
| `.github/workflows/ci.yml` | CI: roda `ruff check` + `pytest` a cada push/PR |
| `Dockerfile` | Imagem da API (Python + Chromium prontos, sem instalar nada na máquina) |
| `docker-compose.yml` | Sobe a API em container com healthcheck e auto-restart |
| `.dockerignore` | Garante que `.env` e arquivos internos **nunca** entrem na imagem |

> `prints_windy/` é criado automaticamente (prints, relatórios e QRs) e não
> é versionado.

---

## Setup (uma vez só)

### 1. Dependências Python

```bash
pip install -r requirements.txt
python -m playwright install chromium
```

### 2. Configurar o `.env`

```bat
copy .env.example .env
```

Edite o `.env` com **seus** dados:

| Variável | O que é |
|---|---|
| `WHATSAPP_CHAT_ID` | Destino: seu número (`55 + DDD + número + @c.us`) **ou** um grupo (`120363...@g.us`) |
| `WAHA_SESSION` | Nome da sessão criada no WAHA |
| `CLIMA_LAT` / `CLIMA_LON` / `CLIMA_LOCAL` | Centro do mapa e rótulo do relatório |

> O `.gitignore` garante que o `.env` **nunca** seja enviado ao GitHub.

### 3. Subir a API

**Opção A — Docker (recomendado: não exige Python na máquina):**

```bash
docker compose up -d --build
docker compose ps        # Status: healthy = no ar
docker compose logs -f   # acompanhar atividade
```

**Opção B — Python local:**

```bat
iniciar.bat
```

Ou manualmente: `python api.py` → confirme em <http://localhost:8000/relatorio>
(a primeira chamada leva ~15s — é o scraper rodando, é normal).

> ⚠️ Use **uma opção por vez** — as duas usam a porta 8000. Para trocar de
> modo: `docker compose down` (encerra o container) ou feche o `iniciar.bat`.

> O n8n roda em Docker e acessa a máquina host por `host.docker.internal:8000`
> — funciona igual com as duas opções. Em **Linux**, o compose do n8n precisa
> de `extra_hosts: ["host.docker.internal:host-gateway"]`.

### 4. WhatsApp (WAHA)

A sessão do WAHA precisa estar `WORKING`:

```http
GET http://localhost:3000/api/sessions
```

Se estiver `SCAN_QR_CODE` ou `FAILED`, regere o QR e escaneie
(WhatsApp → **Aparelhos conectados → Conectar aparelho**):

```http
GET http://localhost:3000/api/{NOME_DA_SESSAO}/auth/qr   → image/png
POST http://localhost:3000/api/sessions/{NOME_DA_SESSAO}/restart
```

O nome da sessão e o destino ficam em dois lugares (use o mesmo nos dois):

- **n8n** → node **"Definir Destinatário"** (campo `session` e `chatId`)
- **Python** → `.env` (`WAHA_SESSION` e `WHATSAPP_CHAT_ID`)

O `chatId` pode ser o **seu número** (`@c.us`) ou o **ID de um grupo**
(`@g.us`) — veja a seção "Trocar o destino (seu número **ou** um grupo)".

### 5. Workflow no n8n

Abra <http://localhost:5678> e importe `n8n_workflow.json`
(⋯ → **Import from File**), ou use o workflow já existente no seu n8n.

> O JSON importado vem com **placeholders** (`SEU_NUMERO_AQUI@c.us`,
> `SUA_SESSAO_AQUI`) — configure o node **"Definir Destinatário"** antes de
> ativar (seção "Trocar o destino (seu número **ou** um grupo)" abaixo).

> ⚠️ **Armadilha do `import:workflow`**: o import **desativa** o workflow
> (o n8n 2.44 traz `--activeState=false` por padrão). Depois de importar,
> ative de um dos dois jeitos:
>
> - **UI** (recomendado): toggle **"Ativo"** no workflow; ou
> - **CLI + restart**: `n8n update:workflow --id=… --active=true` e depois
>   `docker restart n8n` — sem o restart o servidor não re-registra o cron e
>   o agendamento não dispara.

### 6. Workflow de alerta de falha (recomendado)

Se a API estiver desligada ou o WAHA cair, o robô para de vez — ninguém
avisa. O `n8n_error_workflow.json` resolve: é um workflow separado com
**Error Trigger** que manda um ❌ no seu WhatsApp com o node que falhou e o
motivo.

Importe (⋯ → **Import from File**), configure o node **"Definir
Destinatário"** (mesmos `chatId`/`session` do principal) e então no
**workflow principal** abra *Settings* → **Error Workflow** → escolha
*"Alerta de falha — Clima Windy"* → Save.

Teste: com a API **desligada**, clique em *Execute Workflow* no principal —
em segundos chega:

```
❌ Falha no robô do clima
📍 Nó: Gerar Relatório (API local)
⚠️ The service refused the connection - perhaps it is offline
```

> O alerta também tem um node **"Executar na mão (teste)"** que manda um 🧪
> pra confirmar que o caminho WhatsApp está vivo, sem precisar de falha.

---

## Testes e lint

```bash
pip install -r requirements-dev.txt   # pytest + ruff
python -m pytest -q                   # 22 testes (rápidos, sem internet)
python -m ruff check .                # lint
```

> Use `python -m pytest` (e não `pytest` solto): o executável não coloca a
> raiz do repo no `sys.path` e o import de `config.py`/`scraper.py` falha.
> O `pyproject.toml` já resolve isso, mas o `python -m` é o mais garantido.

O CI (`.github/workflows/ci.yml`) roda exatamente esses dois comandos em
todo push/PR — se passar local, passa lá. As regras do ruff estão fixadas no
`ruff.toml` pra valer igual em qualquer máquina.

---

## Configurações do dia a dia

### 🕐 Trocar o horário do envio

Node **"Agendado (escolha a hora)"** → ajuste *Trigger at Hour* /
*Trigger at Minute* → **Save**. Pronto, re-agenda sozinho.

> Se algum dia não disparar: desliga e liga o toggle **"Ativo"** do workflow
> (ou `n8n update:workflow --active=true` + `docker restart n8n`) — o
> servidor só re-registra o cron quando o workflow é (re)ativado.

### 📱 Trocar o destino (seu número **ou** um grupo)

O relatório pode ir para o **seu privado** ou para um **grupo do WhatsApp** — é
só o valor do `chatId` que muda (o sufixo `@c.us` = pessoa, `@g.us` = grupo).

**No n8n** → node **"Definir Destinatário"** → campo **`chatId`**, e **No
Python** → `WHATSAPP_CHAT_ID` do `.env` (os dois com o **mesmo** valor):

| Destino | Formato do `chatId` | Exemplo |
|---|---|---|
| 👤 Seu número (privado) | `55` + DDD + número + `@c.us` | `5514999999999@c.us` |
| 👥 Um grupo | ID do grupo + `@g.us` | `120363000000000000@g.us` |

#### Como descobrir o ID do grupo

```http
GET http://localhost:3000/api/{NOME_DA_SESSAO}/groups
```

Cada grupo vem com o campo **`JID`** — é esse valor que vai no `chatId`:

```json
[
  { "JID": "120363000000000000@g.us", "Name": "Meu grupo do clima", ... }
]
```

> ⚠️ **A conta do WAHA precisa estar no grupo** (e, de preferência, ser admin
> dela). Crie o grupo pelo WhatsApp, adicione a conta do bot e só depois
> configure o `chatId`.

> 💡 Dica: o mesmo endpoint mostra o nome do grupo, então dá pra confirmar
> que você pegou o grupo certo antes de configurar.

### 👥 Mandar para um grupo — passo a passo

1. **Crie o grupo** no WhatsApp e adicione a conta do bot (a mesma que está
   logada no WAHA).
2. **Descubra o ID**: `GET http://localhost:3000/api/{sessao}/groups` → copie
   o `JID` do grupo.
3. **No n8n**: node *"Definir Destinatário"* → `chatId` = o JID.
4. **No `.env`**: `WHATSAPP_CHAT_ID=` o mesmo JID.
5. **Teste**: clique em *Execute Workflow* — imagem + texto chegam no grupo.

> O alerta de falha (❌) tem um `chatId` **próprio** (node *"Definir
> Destinatário"* do workflow de alerta). Se quiser que o erro também vá para o
> grupo, ponha o mesmo JID lá — senão ele continua indo só para o privado.

> 📸 **WhatsApp comprime mais as imagens em grupo** do que no privado. Se o
> print do Windy ficar ruim, delete o node *"WAHA → Enviar Imagem"* e deixe
> só o texto (mais o resumo, que vai na legenda).

### ⚡ Enviar na hora (sem esperar o horário)

Clique em **Execute Workflow** (o node **"Executar na mão"** dispara o fluxo).
Em ~20s chega imagem + texto no seu WhatsApp (privado ou grupo).

---

## Mensagem que chega

1. **Imagem** 🖼 — print do mapa do Windy com *legenda* = resumo
   (temperaturas por hora de hoje + previsibilidade dos próximos dias)
2. **Texto** 📄 — relatório completo extraído da página

> Pra mudar: delete o node **"WAHA → Enviar Texto"** (só imagem) ou
> **"WAHA → Enviar Imagem"** (só texto).

## Variáveis de ambiente (`.env`)

Todas ficam no `.env` (modelo: `.env.example`) e são lidas pelo `config.py`:

| Variável | Padrão | O que faz |
|---|---|---|
| `WHATSAPP_CHAT_ID` | — | Destino: seu número `…@c.us` **ou** um grupo `…@g.us` (obrigatório no `teste_envio.py`) |
| `WAHA_SESSION` | — | Nome da sessão no WAHA (obrigatório no `teste_envio.py`) |
| `WAHA_URL` | `http://localhost:3000` | URL do WAHA |
| `CLIMA_LAT` / `CLIMA_LON` | `-22.264` / `-49.136` | Centro do mapa no Windy |
| `CLIMA_LOCAL` | `Bauru/SP e região` | Rótulo do local nos relatórios |
| `CLIMA_HOST` | `0.0.0.0` | Interface de escuta da API (`127.0.0.1` = só esta máquina) |
| `CLIMA_PORT` | `8000` | Porta da API |
| `CLIMA_WAIT_MS` | `15000` | Espera o Windy carregar (ms) |
| `CLIMA_HEADLESS` | `1` | `0` abre a janela do navegador (depuração) |

> O n8n em Docker precisa da API em `0.0.0.0` para chegar via
> `host.docker.internal`.

## 🔒 Privacidade

- O `.env` (número/grupo, sessão, coordenadas) está no `.gitignore` e **não é
  versionado** — seus dados ficam só na sua máquina.
- O repositório público traz apenas `.env.example` com **placeholders**, e o
  `n8n_workflow.json` também (inclusive os IDs de grupo — são do seu WhatsApp).
- A API devolve caminhos de arquivo apenas como **nome** (sem caminho
  absoluto com usuário da máquina).
- Mandar para um grupo **não expõe nada além do relatório**: só quem estiver
  no grupo lê. Ainda assim, o ID do grupo é dado pessoal — ele fica no `.env`
  e no n8n, nunca no git.

> **Trocou de máquina?** `copy .env.example .env`, preencha de novo e pronto.

## Solução de problemas

| Sintoma | Causa / solução |
|---|---|
| `ERRO DE CONFIGURAÇÃO: Variável '…' não definida` | Falta o `.env` → `copy .env.example .env` e preencha |
| n8n erro `ECONNREFUSED host.docker.internal:8000` | API não está rodando → `docker compose up -d` ou execute `iniciar.bat` |
| `docker compose up` falha com porta 8000 em uso | Já existe uma API rodando → feche o `iniciar.bat` ou `docker compose down` |
| Container `unhealthy` / sem subir | `docker compose logs api` mostra o erro; confirme que o Docker Desktop está aberto |
| Agendamento **não dispara** (nada nas Executions) | Workflow inativo → ative de novo (toggle **"Ativo"** na UI, ou `update:workflow --active=true` + `docker restart n8n`) |
| WAHA `404` em `sendImage` | Sessão errada/parada ou número inválido |
| Envia pro privado mas **não chega no grupo** | A conta do WAHA não está no grupo → adicione-a; confira o ID em `GET /api/{sessao}/groups` (campo **JID**) |
| `chatId inválido no node "Definir Destinatário"` | ID mal formatado — deve terminar em `@c.us` (pessoa) ou `@g.us` (grupo), sem espaços |
| WAHA `"status": "SCAN_QR_CODE"` / `"FAILED"` | Regere o QR e escaneie de novo (seção 4) |
| Falha no agendamento e **ninguém sabe** | Configure o workflow de alerta (seção 6) — ele avisa ❌ no WhatsApp quando o principal falha |
| Print chegando em branco/preto | Aumente o tempo: `CLIMA_WAIT_MS=20000` |
| Mensagem duplicada | Existem 2 workflows iguais → apague/ative só 1 |
| Code node: `Unexpected token ','` | `jsCode` do n8n precisa ser **string**, não array de linhas (reimporte o `n8n_workflow.json` corrigido) |
