# Manual do Price Sentinel 🔍

Guia completo para configurares e usares o teu monitor de promoções automático.

---

## Índice

1. [Configuração Inicial](#1-configuração-inicial)
2. [Como Criar Pesquisas](#2-como-criar-pesquisas)
3. [Estrutura do queries.json](#3-estrutura-do-queriesjson)
4. [Fuentes Suportadas](#4-fontes-suportadas)
5. [Exemplos Práticos](#5-exemplos-práticos)
6. [Executar Localmente](#6-executar-localmente)
7. [Perguntas Frequentes](#7-perguntas-frequentes)

---

## 1. Configuração Inicial

### 1.1 Criar Bot Telegram

1. Abre o Telegram
2. Procura por **@BotFather**
3. Envia `/newbot`
4. Segue as instruções:
   - Nome: `Price Sentinel` (ou outro)
   - Username: `PriceSentinelBot` (tem de acabar em `Bot`)
5. **Guarda o Token** que o BotFather dá (algo como `123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11`)

### 1.2 Obter Chat ID

1. Procura por **@userinfobot** no Telegram
2. Envia `/start`
3. O bot responde com o teu **ID** (número grande, ex: `123456789`)

### 1.3 Obter API Key Gemini

1. Vai a https://aistudio.google.com/app/apikey
2. Clica em **"Create API Key"**
3. Copia a key (começa por `AIza...`)

### 1.4 Configurar GitHub Secrets

1. Vai ao teu repositório no GitHub
2. Clica em **Settings** → **Secrets and variables** → **Actions**
3. Clica em **New repository secret**
4. Adiciona estes 3 secrets:

| Secret | Valor |
|--------|-------|
| `GEMINI_API_KEY` | A key do Gemini |
| `TELEGRAM_TOKEN` | O token do bot |
| `CHAT_ID` | O teu ID |

---

## 2. Como Criar Pesquisas

### O принципо

Tu defines **o que queres pesquisar** + **de onde** + **desconto mínimo**.

O sistema:
1. Traduz automaticamente o termo para a língua correta
2. Pesquisa no site/canal
3. Pede ao Gemini para extrair preços
4. Envia alerta se desconto >= mínimo

### Параметры

| Parâmetro | Obrigatório | Descrição |
|----------|------------|-----------|
| `name` | ✅ | Nome identificador (tu decides) |
| `type` | ✅ | `category`, `product` ou `brand` |
| `source` | ✅ | Onde pesquisar |
| `search_term` | ✅ | O que pesquisar (em português!) |
| `min_discount_percent` | ✅ | Desconto mínimo para alertar |

### Tipos de Pesquisa

| Tipo | Quando usar | Exemplo |
|------|------------|---------|
| `category` | Categoria genérica | "televisores", "telemóveis", "computadores", "pilhas" |
| `product` | Produto específico (marca + tipo) | "Fraldas Dodot", "Nutella 500g", "iPhone 15" |
| `brand` | Marca específicos | "Nike Air Max", "Samsung Galaxy", "Apple" |

### Exemplos

```json
// Categoria: Televisores 4K na Amazon ES
{"name": "TVs 4K", "type": "category", "source": "amazon.es", "search_term": "televisor 4k", "min_discount_percent": 25}

// Produto específico: Fraldas Dodot no Continente
{"name": "Fraldas", "type": "product", "source": "continente.pt", "search_term": "Fraldas Dodot", "min_discount_percent": 20}

// Marca: Nike Air Max nos canais espanhóis
{"name": "Nike", "type": "brand", "source": "canal:@descuentos", "search_term": "Nike Air Max", "min_discount_percent": 30}
```

---

## 3. Estrutura do queries.json

O ficheiro `queries.json` contém uma lista de queries:

```json
{
  "queries": [
    {/* query 1 */},
    {/* query 2 */},
    {/* query 3 */}
  ]
}
```

### Como Adicionar/Editar

1. Abre `queries.json`
2. Adiciona/modifica objekos na lista `queries`
3. Guarda o ficheiro
4. Faz commit (as alterações são aplicadas automaticamente)

---

## 4. Fuentes Suportadas

### 4.1 Websites

| Source | País | Lingua | Exemplo |
|--------|-----|--------|--------|
| `amazon.es` | 🇪🇸 | ES | Amazon Spain |
| `continente.pt` | 🇵🇹 | PT | Continente Portugal |

### 4.2 Canais Telegram

**Portugal:**
| Canal | Membros | Tipo |
|-------|--------|------|
| @wolf_ofertas | 62K | Geral |
| @portugalgeek | 27K | Geral |
| @linguica_das_promocoes | 10K | Geral |
| @economizzandodg | 7K | Cupons |

**Espanha:**
| Canal | Membros | Tipo |
|-------|--------|------|
| @chollos | 232K | **Maior!** |
| @descuentos | 115K | Geral |
| @ganga24 | Ativo | IA filtra |
| @ofertacash | 8K | Amazon, AliExpress |
| @blogdeofertas | 532 | Blog |

**Viagens:**
| Canal | Membros | Tipo |
|-------|--------|------|
| @viajerospiratas | 67K | Voos, hotéis |
| @guidellowcost | 40K | Voos low cost |

---

## 5. Exemplos Práticos

### 5.1 Pesquisas Recomendadas para Iniciar

```json
{
  "queries": [
    {
      "name": "TVs 4K Amazon ES",
      "type": "category",
      "source": "amazon.es",
      "search_term": "televisor 4k",
      "min_discount_percent": 25
    },
    {
      "name": "Fraldas Dodot",
      "type": "product",
      "source": "continente.pt",
      "search_term": "Fraldas Dodot",
      "min_discount_percent": 20
    },
    {
      "name": "Nutella Telegram",
      "type": "product",
      "source": "canal:@chollos",
      "search_term": "Nutella",
      "min_discount_percent": 25
    },
    {
      "name": "Nike Air Max",
      "type": "brand",
      "source": "canal:@descuentos",
      "search_term": "Nike Air Max",
      "min_discount_percent": 30
    },
    {
      "name": "Voos Baratos",
      "type": "category",
      "source": "canal:@viajerospiratas",
      "search_term": "vuelo",
      "min_discount_percent": 40
    },
    {
      "name": "Pilhas",
      "type": "category",
      "source": "amazon.es",
      "search_term": "pilhas",
      "min_discount_percent": 20
    }
  ]
}
```

### 5.2 Como Criar Novas Pesquisas

**Para adicionares uma nova pesquisa:**

1. Decide o que queres monitorizar
2. Escolhe o tipo (`category`, `product`, `brand`)
3. Escolhe a fonte (site ou canal)
4. Define o desconto mínimo

Exemplo - Quero monitorizar "iPhone 16" nos canais espanhóis:

```json
{
  "name": "iPhone 16 Chollos",
  "type": "product",
  "source": "canal:@chollos",
  "search_term": "iPhone 16",
  "min_discount_percent": 25
}
```

---

## 6. Executar Localmente

### 6.1 Instalação

```bash
# Clonar o repositório
git clone https://github.com/teu-user/price-sentinel.git
cd price-sentinel

# Criar ambiente virtual (opcional)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows

# Instalar dependências
pip install -r requirements.txt
playwright install chromium
```

### 6.2 Configurar

```bash
# Criar ficheiro .env
cp .env.example .env

# Editar .env com as tuas keys
# GEMINI_API_KEY=...
# TELEGRAM_TOKEN=...
# CHAT_ID=...
```

### 6.3 Executar

```bash
python sentinel.py
```

---

## 7. Perguntas Frequentes

### Quanto custa?

| Serviço | Custo |
|---------|-------|
| GitHub Actions | Grátis (2000 min/mês) |
| Gemini API | ~$0.001/execução |
| Deep-translator | Grátis |
| Telegram | Gr��tis |
| **Total** | **Zero Budget!** |

### Com que frequência corre?

- A cada 60 minutos automaticamente
- Podes executar manualmente no GitHub (Actions → Run workflow)

### Por que não recebo alertas?

Verifica:
1. ✅ Secrets estão configuradas no GitHub?
2. ✅ O termo de pesquisa existe nos canais/sites?
3. ✅ O desconto é maior que `min_discount_percent`?

### Posso adicionar mais pesquisas?

Sim! Edita `queries.json` e adiciona queries. Mas cuidado - mais queries = mais execuções = mais custo Gemini.

### Como parar?

Remove o repositório ou desativa o workflow em GitHub Actions Settings.

---

## Suporte

Se tiveres dúvidas, abre um issue no GitHub ou consulta este manual.

---

**Price Sentinel** - Poupa dinheiro sem pensar!