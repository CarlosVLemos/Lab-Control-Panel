# Lab Control Panel

Plataforma para executar, comparar e avaliar agentes de IA, tarefas e código. Usa evidências de qualidade, custo, segurança e desempenho para controlar aprovações e releases.

## Rodar (estrutura inicial)

Requisitos: Docker e Docker Compose.

```bash
docker compose up --build
```

API: `http://localhost:8000` · Saúde: `http://localhost:8000/health` · Docs: `http://localhost:8000/docs`

No momento, apenas a API base está implementada. Os módulos de avaliação e rollout estão no backlog.
