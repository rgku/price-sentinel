# Price Sentinel 🔍

Monitor de promoções automático que pesquisa sites e canais Telegram para encontrar as melhores ofertas.

## Funcionalidades

- 🌐 **Websites**: Amazon ES, Continente PT
- 📱 **Canais Telegram**: Monitoriza canais de promoções
- 🤖 **IA**: Gemini extrai preços e descontos automaticamente
- 🔔 **Alertas**: Recebe notificações Telegram quando encontra promoções

## Configuração Inicial

### 1. Criar Bot Telegram

1. Abre o Telegram e procura por @BotFather
2. Envia `/newbot` e segue as instruções
3. Guarda o **Token** (ex: `123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11`)

### 2. Obter Chat ID

1. Procura por @userinfobot no Telegram
2. Envia `/start`
3. Guarda o **ID** (número)

### 3. Obter API Key Gemini

1. Vai a https://aistudio.google.com/app/apikey
2. Cria uma nova API key
3. Guarda a key

### 4. Configurar GitHub Secrets

No teu repositório GitHub:
1. Settings → Secrets and variables → Actions
2. Adiciona:
   - `GEMINI_API_KEY`: tua key do Gemini
   - `TELEGRAM_TOKEN`: token do bot
   - `CHAT_ID`: o teu ID

---

## Como Criar as Tuas Pesquisas

Edita o ficheiro `queries.json`:

### Estrutura de uma Query

```json
{
  "id": 1,
  "name": "Nome da Pesquisa",
  "type": "category|product|brand",
  "source": "amazon.es|continente.pt|canal:@nome",
  "search_term": "termo a pesquisar",
  "min_discount_percent": 20
}
```

### Campos

| Campo | Obrigatório | Descrição |
|-------|-------------|-----------|
| `name` | ✅ | Nome identificador (tu defines) |
| `type` | ✅ | `category`, `product` ou `brand` |
| `source` | ✅ | Site ou canal Telegram |
| `search_term` | ✅ | Termo a pesquisar (em português) |
| `min_discount_percent` | ✅ | Desconto mínimo (%) para alertar |

### Tipos de Pesquisa

| Tipo | Quando usar | Exemplo |
|------|------------|---------|
| `category` | Categoria genérica | "televisores", "telemóveis", "pilhas" |
| `product` | Produto específico | "Fraldas Dodot", "Nutella 500g" |
| `brand` | Marca específica | "Nike Air Max", "Samsung Galaxy" |

### Fontes Suportadas

**Websites:**
- `amazon.es`
- `continente.pt`

**Canais Telegram:**
```
PORTUGAL:
@wolf_ofertas
@portugalgeek
@linguica_das_promocoes
@economizzandodg

ESPANHA:
@chollos           (232K membros - maior!)
@descuentos        (115K membros)
@ganga24           (tem IA que filtra)
@ofertacash        (Amazon, AliExpress, Miravia)
@blogdeofertas

VIAGENS:
@viajerospiratas   (67K membros)
@guidellowcost     (40K membros)
```

### Tradução Automática

O sistema traduz automaticamente o `search_term` para a língua do source:
- Amazon ES → traduz PT → ES
- Canais ES → traduz PT → ES
- Continente PT → mantém PT

Exemplo: "pilhas" → "pilas" (Amazon ES)

---

## Exemplos de Queries

### Pesquisas Recomendadas

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
      "name": "Fraldas Dodot Continente",
      "type": "product",
      "source": "continente.pt",
      "search_term": "Fraldas Dodot",
      "min_discount_percent": 20
    },
    {
      "name": "Nutella Chollos ES",
      "type": "product",
      "source": "canal:@chollos",
      "search_term": "Nutella",
      "min_discount_percent": 25
    },
    {
      "name": "Nike Air Max Descuentos",
      "type": "brand",
      "source": "canal:@descuentos",
      "search_term": "Nike Air Max",
      "min_discount_percent": 30
    },
    {
      "name": "Vooos Viagens",
      "type": "category",
      "source": "canal:@viajerospiratas",
      "search_term": "vuelo",
      "min_discount_percent": 40
    },
    {
      "name": "Pilhas Amazon ES",
      "type": "category",
      "source": "amazon.es",
      "search_term": "pilhas",
      "min_discount_percent": 20
    }
  ]
}
```

---

## Como Editar as Pesquisas

1. Edita o ficheiro `queries.json`
2. Adiciona/modifica/remove objetos na lista
3. Faz commit das alterações
4. O GitHub Actions corre automaticamente (a cada 60 min)

---

## Executar Localmente (Desenvolvimento)

```bash
# Instalar dependências
pip install -r requirements.txt
playwright install chromium

# Criar ficheiro .env (copia de .env.example)
cp .env.example .env
# Edita .env com as tuas keys

# Executar
python sentinel.py
```

---

## Ficheiros

| Ficheiro | Descrição |
|----------|-----------|
| `sentinel.py` | Script principal |
| `queries.json` | Queries de pesquisa (edita isto!) |
| `requirements.txt` | Dependências Python |
| `.env.example` | Template de configuração |
| `.github/workflows/main.yml` | CI/CD (executa a cada 60 min) |
| `history.db` | Histórico de preços (criado automaticamente) |

---

## Perguntas Frequentes

### Quanto custa?
- **GitHub Actions**: 2000 min/mês grátis
- **Gemini API**: ~$0.001 por execução (muito barato)
- **Deep-translator**: Grátis
- **Total**: Zero Budget!

### Com que frequência corre?
- A cada 60 minutos (configurável no `main.yml`)
- Podes executar manualmente no GitHub

### Recebo alertas em duplicado?
- Não! O sistema guarda o último desconto visto
- Só alerta se o novo desconto for **maior** que o anterior

---

## Fase 2 (Futuro)

- 🌐 Website com login para gerir queries
- 📊 Dashboard com histórico
- 📈 Gráficos de preços
