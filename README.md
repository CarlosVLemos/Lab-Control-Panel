# Lab Control Panel

O Lab Control Panel (LCP) é um projeto experimental para comparar resultados de tarefas e examinar evidências de execução de agentes. A interface reúne experimentos de classificação, avaliação de código e observabilidade. Os dados importados são analisados, não executados.

## O que está implementado

- **Experimentos / Classificação sintética:** compara dois classificadores determinísticos sobre seis casos. FastAPI, PostgreSQL e Vue; o relatório fica persistido no banco.
- **Experimentos / CODE-001:** apresenta resultados importados de uma tarefa de código executada com e sem especificação, incluindo testes, diffs e hashes. A interface não executa código.
- **Experimentos / SWE-bench:** compara duas trajetórias publicadas da mesma issue, mantendo resultados e métricas atribuídos à fonte.
- **Observabilidade:** importa AgentTrace (JSON/JSONL) e LCP Evidence v1 no navegador. Exibe traces, ferramentas, erros, duração e tokens reportados, além de filtros, diagnósticos e replay visual de eventos.
- **RAG-001 (backend):** corpus fictício e avaliação determinística offline. O adaptador para chamadas remotas existe, mas não há resultados de execução paga comprovados.

## Agentes de desenvolvimento

Os nomes abaixo identificam papéis do fluxo de desenvolvimento assistido, não agentes executados ou avaliados pelo LCP.

| Agente | Responsabilidade |
| --- | --- |
| **Jarvis** | Planejamento, distribuição de tarefas e contratos |
| **Maquiavel** | Backend, persistência e testes Python |
| **Van Gogh** | Interface Vue/TypeScript |
| **Mefisto** | Revisão independente, riscos e evidências |

As responsabilidades e regras de revisão estão em [AGENTS.md](AGENTS.md) e [SDD/rules.md](SDD/rules.md). Os perfis ficam em [`.codex/agents/`](.codex/agents/).

## Fontes

- **Classificação:** seis casos sintéticos definidos em [`response_fixture.py`](backend/app/demo/response_fixture.py).
- **CODE-001:** artefatos do experimento [lcp-agent-benchmark](https://github.com/CarlosVLemos/lcp-agent-benchmark), importados em [`code-001-import.json`](frontend/src/data/code-001-import.json).
- **SWE-bench Verified:** [trajetórias publicadas](https://huggingface.co/datasets/tarsur385/swebench-verified-trajectories), revisão `773748a7c1222e8a642a7059821498e14293562a`.
- **AgentTrace:** [dataset](https://huggingface.co/datasets/pagarsky/agent-trace) e [código da instrumentação](https://github.com/pagarsky/agent-trace). A revisão exata do dataset não foi registrada no manifesto local.
- **RAG-001:** 12 políticas fictícias definidas no [módulo de avaliação](backend/app/evaluation/rag.py).

O processo de seleção, sanitização e importação das amostras externas está documentado em [EXP-002 / OBS-002](docs/EXP-002-OBS-002.md). Hashes verificam os arquivos locais, não autenticam sua origem.

## Evidências e limites

- **Classificação:** baseline **2/6** e candidato **6/6**, em dados sintéticos. Não é avaliação de um LLM.
- **CODE-001:** ambas as estratégias passaram **9/9** testes; resultado **sem vencedor**. Tokens, custo e duração do agente não foram registrados. [Registro](docs/evidence/code-001-real-evaluation-view.md).
- **SWE-bench / AgentTrace:** dois registros de trajetória da mesma issue e uma amostra de 12 traces externos incorporados à interface. São resultados importados, não execuções feitas pelo LCP. [Origem e validação](docs/EXP-002-OBS-002.md).
- **RAG-001:** 36 casos offline sobre 12 documentos fictícios. A correção semântica de texto gerado não foi avaliada. [Registro](docs/evidence/rag-001-offline-foundation.md).

A [CI](.github/workflows/ci.yml) inclui pytest com PostgreSQL, Vitest, build do frontend, Playwright e um teste de persistência após reiniciar a API. O LCP não é um serviço de produção, nem mede custos reais quando a fonte não os fornece.

## Rodar localmente

Requisitos: Git, Docker e Docker Compose.

```bash
git clone https://github.com/CarlosVLemos/Lab-Control-Panel.git
cd Lab-Control-Panel
docker compose up -d --build --wait
docker compose exec -T api alembic upgrade head
```

Acesse:

- Interface: **http://localhost:5173**
- API: **http://localhost:8000/docs**
- Saúde da API: **http://localhost:8000/health**

Em **Experimentos**, abra **Classificação sintética** e clique em **Executar comparação**. As telas **SWE-bench** e **CODE-001** exibem dados importados. Em **Observabilidade**, carregue a amostra incluída ou importe um arquivo local compatível.

Para encerrar:

```bash
docker compose down
```

O comando preserva o volume do PostgreSQL. `docker compose down -v` remove os dados persistidos.
