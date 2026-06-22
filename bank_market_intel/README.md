# Market Intel Bancário

Dashboard com **dados reais** do [BCB IF.data](https://olinda.bcb.gov.br/olinda/servico/IFDATA/versao/v1/odata) (API OData pública).

## O que funciona (dados factuais)

| Métrica | Fonte |
|---------|--------|
| Lucro líquido trimestral | BCB IF.data — relatório Resumo |
| ROE (anualizado) | Calculado: `(lucro / PL) × 4 × 100` |
| Índice de Basileia | BCB IF.data — relatório Resumo |
| Histórico de lucro | BCB IF.data — séries trimestrais |

Bancos: **Itaú, Bradesco, BB, Santander e Nubank** (conglomerado prudencial).

## O que não está no MVP

- Base de clientes / market share
- Inadimplência (>90 dias) — relatórios de crédito instáveis no IF.data
- Reclame Aqui e nota de app — sem API oficial gratuita

## Como rodar

```bash
cd bank-market-intel
pip install -r requirements.txt
uvicorn backend.main:app --reload --port 8088
```

Abra [http://localhost:8088](http://localhost:8088) (use outra porta se 8088 estiver ocupada).

> A primeira carga pode demorar ~30–60s porque a API do BCB é lenta. Respostas ficam em cache por 1 hora.

## Endpoints da API

- `GET /api/meta` — metadados e período de referência
- `GET /api/banks/current` — snapshot do trimestre mais recente
- `GET /api/banks/history?metric=lucro` — série histórica de lucro

## Stack

- **Backend:** Python, FastAPI, httpx
- **Frontend:** JavaScript puro, Tailwind CSS e Chart.js (via CDN, sem build)
- **Fonte:** Banco Central do Brasil — IF.data OData
