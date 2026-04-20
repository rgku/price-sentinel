# 📖 Price Sentinel - Manual Completo

Guia completo para configurar e usar o seu monitor de promoções automático.

---

## 1. O que é o Price Sentinel?

O Price Sentinel é uma aplicação **Zero Budget** que:
- ✅ Monitoriza sites e canais Telegram automaticamente
- ✅ Usa IA (Gemini) para extrair preços e descontos
- ✅ Envia alertas quando encontra boas promoções
- ✅ Corre no GitHub Actions (grátis!)

---

## 2. Configuração Inicial

### 2.1 Criar Bot Telegram

1. Abra o **Telegram**
2. Procure por **@BotFather**
3. Envie `/newbot`
4. Siga as instruções:
   - Nome: `PriceSentinel` (ou outro)
   - Username: `PriceSentinelBot` (tem de acabar em Bot)
5. **Guarde o Token** fornecido (ex: `123456:ABC-DEF...`)

### 2.2 Obter Chat ID

1. Procure por **@userinfobot** no Telegram
2. Envie `/start`
3. Guarde o **ID** (número)

### 2.3 Obter API Key Gemini

1. Vá a https://aistudio.google.com/app/apikey
2. Clique em **"Create API Key"**
3. Guarde a key

### 2.4 Configurar no GitHub

1. Vá ao repositório: https://github.com/rgku/price-sentinel/settings/secrets/actions
2. Adicione:
   - `GEMINI_API_KEY`: sua key
   - `TELEGRAM_TOKEN`: token do bot
   - `CHAT_ID`: seu ID

---

## 3. Como Criar Pesquisas

### 3.1 Estrutura das Queries

Edite o ficheiro `queries.json`:

```json
{
  "name": "Nome da Pesquisa",
  "type": "category|product|brand",
  "source": "fonte",
  "search_term": "termo",
  "min_discount_percent": 20,
  "max_price": 50
}
```

### 3.2 Parâmetros Disponíveis

| Parâmetro | Obrigatório | Descrição | Exemplo |
|----------|------------|----------|---------|
| `name` | ✅ | Nome identificador | "TVs 4K" |
| `type` | ✅ | Tipo de pesquisa | `category`, `product`, `brand` |
| `source` | ✅ | Onde pesquisar | `amazon.es`, `canal:@chollos` |
| `search_term` | ✅ | Termo a pesquisar (PT) | "televisor 4k" |
| `min_discount_percent` | ❌ | Desconto mínimo (%) | 25 |
| `max_price` | ❌ | Preço máximo (€) | 100 |

### 3.3 Tipos de Pesquisa

| Tipo | Quando usar | Exemplo |
|------|------------|---------|
| `category` | Categoria genérica | "televisores", "pilhas", "computadores" |
| `product` | Produto específico | "Fraldas Dodot", "Nutella 500g" |
| `brand` | Marca específica | "Nike Air Max", "Samsung Galaxy" |

### 3.4 Fontes Suportadas

**Websites:**
| Source | País | Língua |
|--------|------|--------|
| `amazon.es` | 🇪🇸 | ES |
| `continente.pt` | 🇵🇹 | PT |

**Canais Telegram:**

| Canal | Membros | País |
|-------|---------|------|
| @chollos | 232K | 🇪🇸 |
| @descuentos | 115K | 🇪🇸 |
| @ganga24 | Ativo | 🇪🇸 |
| @wolf_ofertas | 62K | 🇵🇹 |
| @portugalgeek | 27K | 🇵🇹 |
| @viajerospiratas | 67K | ✈️ |

**RSS Feeds:**

| Fonte | URL | Tipo |
|-------|-----|------|
| DealDump All | `rss:https://dealdump.com/rss.php` | Geral |
| DealDump Tech | `rss:https://dealdump.com/rss.php?cat=computers-and-accessories` | Tecnologia |
| DealDump Laptops | `rss:https://dealdump.com/rss.php?cat=Laptops` | Laptops |
| eDealinfo | `rss:https://www.edealinfo.com/rss/` | Geral |
| DealNews | `rss:https://dealnews.com/pages/rss.html` | Geral |

---

## 4. Exemplos de Pesquisas

### 4.1 Exemplos Recomendados

```json
{
  "queries": [
    {
      "name": "TVs 4K Amazon",
      "type": "category",
      "source": "amazon.es",
      "search_term": "televisor 4k",
      "min_discount_percent": 25,
      "max_price": 400
    },
    {
      "name": "Fraldas Dodot",
      "type": "product",
      "source": "continente.pt",
      "search_term": "Fraldas Dodot",
      "min_discount_percent": 20,
      "max_price": 15
    },
    {
      "name": "Nutella",
      "type": "product",
      "source": "canal:@chollos",
      "search_term": "Nutella",
      "min_discount_percent": 25,
      "max_price": 5
    },
    {
      "name": "Nike Air Max",
      "type": "brand",
      "source": "canal:@descuentos",
      "search_term": "Nike Air Max",
      "min_discount_percent": 30,
      "max_price": 120
    }
  ]
}
```

### 4.2 Filtros Disponíveis

**Desconto Mínimo:**
```json
"min_discount_percent": 20  // Só alerta se desconto >= 20%
```

**Preço Máximo:**
```json
"max_price": 50  // Só alerta se preço <= 50€
```

**Ambos:**
```json
"min_discount_percent": 30,
"max_price": 100
```

---

## 5. Como Editar as Pesquisas

### 5.1 Adicionar Nova Pesquisa

1. Edite `queries.json`
2. Adicione um novo objeto:
```json
{
  "name": "Nome",
  "type": "category",
  "source": "amazon.es",
  "search_term": "termo",
  "min_discount_percent": 20
}
```
3. Faça commit das alterações

### 5.2 Remover Pesquisa

Basta apagar o objeto correspondente do `queries.json`.

---

## 6. Frequência de Execução

O sistema corre automaticamente:
- **A cada 8 horas** (3x/dia)
- Pode executar manualmente no GitHub Actions

---

## 7. Onde Receber Alertas

Quando o sistema encontrar uma promoção que cumpra os filtros, recebe uma mensagem no Telegram como:

```
📉 Promoção Detetada!

Query: TVs 4K Amazon
Produto: Televisor Samsung 55" 4K
Preço: €399.99
Original: €599.99
Desconto: 33%

Ver produto: [link]
```

---

## 8. Custo

| Serviço | Custo |
|---------|-------|
| GitHub Actions | Grátis (2000 min/mês) |
| Gemini API | Grátis (1000 req/dia) |
| deep-translator | Grátis |
| Telegram | Grátis |
| **Total** | **Zero Budget!** |

---

## 9. Perguntas Frequentes

**P: Por que não recebo alertas?**
R: Verifique se o termo existe nas fontes e se o desconto cumpre os filtros.

**P: Posso adicionar mais pesquisas?**
R: Sim, mas mais queries = mais tempo e custo (ainda assim baixo).

**P: Como parar?**
R: Edite o workflow para remover ou delete o repositório.

---

## 10. Formato JSON Completo

Exemplo com todos os campos:

```json
{
  "queries": [
    {
      "id": 1,
      "name": "Exemplo",
      "type": "category",
      "source": "amazon.es",
      "search_term": "exemplo",
      "min_discount_percent": 20,
      "max_price": 100
    }
  ]
}
```

---

## 11. Suporte

Para dúvidas, abra um issue no GitHub.

---

**Price Sentinel** - Poupe dinheiro sem pensar! 💰