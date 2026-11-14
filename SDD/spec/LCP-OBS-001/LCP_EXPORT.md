# LCP_EXPORT — Prompt declarativo para conversa/tarefa já concluída (DRAFT)

Copie o trecho abaixo para a conversa do agente que realizou a tarefa **somente se desejar produzir um autorrelato**. O agente não deve executar comandos, acessar rede ou buscar telemetria que não tenha nos registros existentes.

---

Você está preparando um **arquivo de evidências retrospectivas para importação no Lab Control Panel**. Sua missão é organizar exclusivamente dados comprovadamente acessíveis nesta conversa e em arquivos de execução já visíveis.

1. Produza um JSON UTF-8 válido com `schema_version: "lcp.observation.v1"`, `run_id`, `source.kind: "self_report"`, `source.format: "lcp.observation.v1"`, `source.producer`, `agent`, `started_at`, `ended_at`, `total_duration_ms` (se medido) e `events`.
2. Para cada evento conhecido, registre `id`, `seq`, `kind`, `name`, `status`, `started_at`, `ended_at`, `usage` e `detail`. Use `null` para métricas ausentes; não preencha com zeros.
3. Não invente ferramentas, comandos executados, durações, timestamps, tokens, preço, número de tentativas, observações ou erros. Distingua claramente o que foi visto no histórico do que é apenas descrição sua.
4. Não altere logs ou testes originais, não rode nada, não baixe pacotes, não faça chamadas externas, não instale instrumentação, não crie arquivos executáveis.
5. Se tiver referências de mensagens/logs/artefatos, inclua um identificador de origem em `source.reference` e informações textuais nas `detail` dos eventos; não trate uma referência como prova de autenticidade.
6. Remova credenciais, tokens secretos, dados pessoais e material confidencial. Nunca inclua texto bruto de raciocínio privado.
7. Se não souber a ordem ou se não houver eventos verificáveis, não crie uma timeline fictícia: use `events: []` e explique lacunas brevemente em uma nota separada.
8. Retorne **somente JSON** e, fora dele, uma lista curta de quais evidências ficaram indisponíveis. Não afirme qualidade, sucesso ou eficiência geral da tarefa.

---

**Aviso:** gerado pelo próprio agente = **autorrelato**, não rastreamento independente. O LCP deve mostrar esse rótulo. O envelope v1 está FROZEN para a Etapa A; este prompt retrospectivo permanece **DRAFT** e deve ser testado antes de divulgação pública.
