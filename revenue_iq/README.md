# RevenueIQ

Dashboard de inteligência de receita com dados simulados, cálculos determinísticos em Pandas e interpretação dos resultados por uma LLM hospedada na Groq.

## Arquitetura

1. `data/revenue_data.csv` contém 2.402 transações simuladas e reproduzíveis.
2. `api/analytics.py` aplica filtros e calcula KPIs, séries e evidências.
3. `api/app.py` publica os endpoints FastAPI e chama a Groq quando há uma chave.
4. O frontend `../revenue-ai-dashboard-mockup.html` consome a API.
5. Sem chave ou quando a Groq está indisponível, a API retorna uma resposta demonstrativa baseada nos mesmos cálculos.

## Instalação no Windows

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r revenue_iq\requirements.txt
```

## Configuração da Groq

Configure a chave com entrada mascarada:

```powershell
powershell -ExecutionPolicy Bypass -File revenue_iq\configure_groq.ps1
```

O script cria `revenue_iq/.env` com esta estrutura:

```text
GROQ_API_KEY=sua_chave_local
GROQ_MODEL=llama-3.3-70b-versatile
```

O arquivo `.env` está ignorado pelo Git. Nunca coloque a chave no HTML, em commits ou em mensagens.

## Execução

```powershell
powershell -ExecutionPolicy Bypass -File revenue_iq\run.ps1
```

Ou inicie os serviços separadamente:

```powershell
.\.venv\Scripts\python.exe -m uvicorn revenue_iq.api.app:app --host 127.0.0.1 --port 8000
.\.venv\Scripts\python.exe -m http.server 8765 --bind 127.0.0.1
```

Dashboard: `http://127.0.0.1:8765/revenue-ai-dashboard-mockup.html`

Documentação da API: `http://127.0.0.1:8000/docs`

## Testes

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s revenue_iq\tests -v
```

## Segurança da demonstração

- A chave existe apenas no backend.
- A pergunta possui limite de tamanho.
- A API limita requisições por IP.
- A LLM recebe métricas agregadas, não o CSV completo.
- Evidências são selecionadas de um catálogo calculado pelo backend.
- Respostas sem evidência válida são substituídas por um fallback seguro.
