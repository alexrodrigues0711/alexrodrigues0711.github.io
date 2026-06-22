# Market Intel Bancário

Backend de inteligência financeira que consulta a API pública [BCB IF.data](https://olinda.bcb.gov.br/olinda/servico/IFDATA/versao/v1/odata) e transforma dados regulatórios em indicadores comparáveis para Itaú, Bradesco, Banco do Brasil, Santander e Nubank.

## Pipeline de dados

1. O cliente OData identifica o trimestre mais recente disponível no IF.data.
2. Os conglomerados prudenciais são consultados pelo código institucional no relatório Resumo do BCB.
3. Lucro líquido, Patrimônio Líquido e Índice de Basileia são convertidos em um contrato JSON comum.
4. Resultados acumulados do segundo e do quarto trimestre são normalizados pela diferença em relação ao trimestre anterior.
5. O ROE é anualizado pela fórmula `(lucro trimestral / patrimônio líquido) × 4 × 100`.
6. As respostas do BCB são mantidas em cache por uma hora para reduzir chamadas repetidas à API de origem.

## Indicadores

| Indicador | Tratamento |
|---|---|
| Lucro líquido trimestral | Valor do BCB normalizado para trimestre isolado e apresentado em R$ bilhões. |
| ROE anualizado | Calculado pelo backend a partir do lucro trimestral e do Patrimônio Líquido. |
| Índice de Basileia | Obtido do relatório Resumo do BCB e convertido para percentual. |
| Histórico de lucro | Série trimestral iniciada em `1T23`, organizada por instituição. |

## API

| Método | Endpoint | Responsabilidade |
|---|---|---|
| `GET` | `/api/health` | Informa o estado da aplicação. |
| `GET` | `/api/meta` | Retorna período, fonte, escopo e indicadores disponíveis. |
| `GET` | `/api/banks/current` | Retorna o snapshot comparativo do trimestre mais recente. |
| `GET` | `/api/banks/history?metric=lucro` | Retorna a série histórica trimestral por banco. |

## Componentes

- `backend/bcb_client.py`: cliente OData, normalização trimestral, cálculo dos indicadores e cache.
- `backend/config.py`: códigos dos conglomerados e colunas utilizadas no relatório do BCB.
- `backend/main.py`: endpoints FastAPI e composição das respostas.
- `frontend/`: dashboard em JavaScript com visualizações Chart.js.

## Stack

Python, FastAPI, HTTPX, JavaScript, Tailwind CSS e Chart.js.
