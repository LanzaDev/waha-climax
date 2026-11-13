# 🌤 Clima Windy → n8n → WAHA → WhatsApp

Robô de monitoramento meteorológico: captura o **mapa e a previsão do Windy**
(Bauru/SP) com Playwright, gera um relatório em texto e manda **imagem + texto
no privado do seu número** via WhatsApp (WAHA), tudo orquestrado pelo **n8n**.

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
│  WAHA (Docker :3000)   │ ─────────────────────► │  SEU NÚMERO (privado) │
│  sessão WORKING        │                        │                       │
└────────────────────────┘                        └──────────────────────┘
```

## Arquivos

| Arquivo | O que é |
|---|---|
| `print.py` | Scraper do Windy. Expõe `gerar_relatorio()`; `python print.py` continua funcionando (salva em `prints_windy/`) |
| `api.py` | Servidor HTTP local (porta 8000) que o n8n chama. Devolve JSON com `resumo`, `texto` e `imagem_base64` |
| `iniciar.bat` | Sobe a API com 1 clique (Windows) |
| `n8n_workflow.json` | Export do workflow pra referência / reimport no n8n |
| `teste_envio.py` | Teste de ponta a ponta via Python (gera relatório e manda no WhatsApp) |
| `requirements.txt` | Dependências (`pip install -r requirements.txt`) |

> `prints_windy/` é criado automaticamente (prints, relatórios e QRs) e não
> é versionado.

---

## Setup (uma vez só)

### 1. Dependências Python

```bash
pip install -r requirements.txt
python -m playwright install chromium
```

### 2. Subir a API

```bat
iniciar.bat
```

Ou manualmente: `python api.py` → confirme em <http://localhost:8000/relatorio>
(a primeira chamada leva ~15s — é o scraper rodando, é normal).

> O n8n roda em Docker e acessa a máquina host por `host.docker.internal:8000`.

### 3. WhatsApp (WAHA)

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

O nome da sessão e o número de destino estão no node **"Definir Destinatário"**
do workflow (campo `session` e `chatId`).

### 4. Workflow no n8n

Abra <http://localhost:5678> e importe `n8n_workflow.json`
(⋯ → **Import from File**), ou use o workflow já existente:
**"Clima Windy → WhatsApp (Bauru)"**.

> ⚠️ **Armadilha do `import:workflow`**: o import **desativa** o workflow
> (o n8n 2.44 traz `--activeState=false` por padrão e a flag `fromJson` só
> funciona em modo queue). Depois de importar, **ative pela UI** (toggle
> "Ativo") — nunca por CLI, senão o servidor não registra o cron e o
> agendamento não dispara.

---

## Configurações do dia a dia

### 🕐 Trocar o horário do envio

Node **"Agendado (escolha a hora)"** → ajuste *Trigger at Hour* /
*Trigger at Minute* → **Save**. Pronto, re-agenda sozinho.

> Se algum dia não disparar: desliga e liga o toggle **"Ativo"** do workflow
> (ativação feita **pela UI** é processada pelo servidor e re-registra o cron).

### 📱 Trocar o número de destino

Node **"Definir Destinatário"** → campo **`chatId`**:

```
55 + DDD + número + @c.us      ex: 5514999222285@c.us
```

### ⚡ Enviar na hora (sem esperar o horário)

Clique em **Execute Workflow** (o node **"Executar na mão"** dispara o fluxo).
Em ~20s chega imagem + texto no seu WhatsApp.

---

## Mensagem que chega

1. **Imagem** 🖼 — print do mapa do Windy com *legenda* = resumo
   (temperaturas por hora de hoje + previsibilidade dos próximos dias)
2. **Texto** 📄 — relatório completo extraído da página

> Pra mudar: delete o node **"WAHA → Enviar Texto"** (só imagem) ou
> **"WAHA → Enviar Imagem"** (só texto).

## Variáveis de ambiente (`api.py`)

| Variável | Padrão | O que faz |
|---|---|---|
| `CLIMA_PORT` | `8000` | Porta da API |
| `CLIMA_WAIT_MS` | `15000` | Espera o Windy carregar (ms) |
| `CLIMA_HEADLESS` | `1` | `0` abre a janela do navegador (depuração) |

## Solução de problemas

| Sintoma | Causa / solução |
|---|---|
| n8n erro `ECONNREFUSED host.docker.internal:8000` | API não está rodando → execute `iniciar.bat` |
| Agendamento **não dispara** (nada nas Executions) | Workflow inativo ou ativado por CLI → abra a UI e ligue o toggle **"Ativo"** |
| WAHA `404` em `sendImage` | Sessão errada/parada ou número inválido |
| WAHA `"status": "SCAN_QR_CODE"` / `"FAILED"` | Regere o QR e escaneie de novo (seção 3) |
| Print chegando em branco/preto | Aumente o tempo: `CLIMA_WAIT_MS=20000` |
| Mensagem duplicada | Existem 2 workflows iguais → apague/ative só 1 |
| Code node: `Unexpected token ','` | `jsCode` do n8n precisa ser **string**, não array de linhas (reimporte o `n8n_workflow.json` corrigido) |
