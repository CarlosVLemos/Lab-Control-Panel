# Lab Control Panel

Plataforma experimental para comparar execuções, avaliar evidências e, futuramente, orientar decisões sobre agentes de IA, tarefas e código.

## Executar a demonstração

Requisitos: Docker e Docker Compose.

```bash
docker compose up -d --build --wait
docker compose exec -T api alembic upgrade head
```

Abra **http://localhost:5173**, clique em **Executar comparação** e inspecione os seis casos de classificação. A API responde em **http://localhost:8000** (rotas /health e /docs). Os resultados permanecem no PostgreSQL após reiniciar a API.

**Limites:** demo sintética e determinística (baseline 2/6, candidato 6/6); não executa LLM real, não mede custos/tokens/latência de produção e não constitui um deploy de produção.

### Testes

A CI executa pytest com PostgreSQL, Vitest/build do frontend, smoke HTTP após reinício e dois testes Playwright (comparação real via API + falha 503 simulada). Para reproduzir o E2E localmente, com os containers e a migração acima em execução:

```bash
cd frontend
npm ci
npm install --no-save --package-lock=false --ignore-scripts @playwright/test@1.56.1
npx playwright install chromium
npx playwright test --config playwright.config.ts
```

Não use docker compose down -v se desejar manter o volume e seus resultados.
