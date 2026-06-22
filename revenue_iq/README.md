# RevenueIQ Backend

Backend analítico do RevenueIQ, um dashboard de inteligência de receita que combina cálculos determinísticos em Pandas com interpretação executiva por LLM.

## Fluxo de dados

1. `data/revenue_data.csv` fornece 2.402 transações simuladas e reproduzíveis.
2. `api/analytics.py` valida o schema, aplica filtros e calcula KPIs, séries mensais, rankings e concentração de receita.
3. O backend monta um catálogo de evidências a partir dessas métricas calculadas.
4. `api/app.py` envia para a Groq somente o contexto agregado e os identificadores de evidência disponíveis.
5. A resposta estruturada da LLM é validada antes de ser devolvida ao dashboard. Se a resposta for inválida ou o provedor estiver indisponível, o backend gera uma análise determinística com os mesmos dados.

## API

| Método | Endpoint | Responsabilidade |
|---|---|---|
| `GET` | `/api/health` | Informa o estado da API, volume carregado e disponibilidade da integração com a LLM. |
| `GET` | `/api/dashboard` | Retorna KPIs, séries e dimensões para os filtros de segmento, região e período. |
| `POST` | `/api/analyze` | Responde a uma pergunta executiva e vincula a resposta às evidências calculadas. |

O endpoint de análise aceita uma pergunta e os filtros ativos do dashboard. A resposta segue um contrato com `answer`, `evidence`, `confidence` e `mode`, permitindo que o frontend diferencie respostas da Groq, demonstrações locais e fallbacks.

## Componentes

- `api/app.py`: endpoints FastAPI, modelos de entrada e saída, integração com a Groq e controle de requisições.
- `api/analytics.py`: transformações Pandas, filtros, KPIs e geração do catálogo de evidências.
- `data/revenue_data.csv`: base simulada usada pelo motor analitico.
- `tests/`: testes dos calculos, filtros e contratos principais da API.

## Decisões técnicas

- Os indicadores financeiros são calculados antes da chamada à LLM.
- O prompt usa contexto JSON estruturado e temperatura baixa para reduzir variação.
- A LLM seleciona apenas evidências existentes no catálogo produzido pelo backend.
- Filtros são normalizados no servidor para manter o dashboard e a análise consistentes.
- CORS, limite de tamanho da pergunta e rate limiting protegem a API publica.

## Stack

Python, FastAPI, Pandas, Pydantic, HTTPX e Groq API.
