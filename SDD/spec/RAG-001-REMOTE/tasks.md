# Tasks — RAG-001-REMOTE

**Modo:** SINGLE_WRITER. **Contrato:** DRAFT; não há autorização de implementação de runtime. **Issue:** #45.

| Tarefa | Responsável | Caminhos permitidos | Gate | Evidência |
| --- | --- | --- | --- | --- |
| T-00 Criar proposta de Spec/contrato/aceite | Jarvis | `SDD/spec/RAG-001-REMOTE/*`, `SDD/index.md` | Esta PR | Diff e revisão |
| T-01 Revisão independente de threat model, custo e desenho experimental | Mefisto | Comentários na PR; `review.md` após revisão | T-00 | Parecer `passed` / restrições |
| T-02 Aprovação humana de contrato e marcação FROZEN | Humano + Jarvis | `contract.md` e `SDD/index.md` | T-01 | Referência explícita de aprovação, commit |
| T-03 Cliente offline injetável e schema de registros | Maquiavel | `backend/app/evaluation/rag_remote*.py`, `backend/tests/test_rag_remote*.py` | T-02 | Testes mock, schema |
| T-04 Adaptador OpenAI isolado e prova de bloqueio de rede no default | Maquiavel | Mesmos caminhos | T-03 | Fakes, sem credenciais reais |
| T-05 Controle fail-closed de custo, retries, idempotência de artefatos e cotas | Maquiavel | Mesmos caminhos | T-04 | Testes adversariais sem API |
| T-06 Exportação JSONL/relatórios e evidência de CI | Maquiavel | Mesmos caminhos + `docs/evidence/rag-001-*` | T-05 | CI completa |
| T-07 Revisão independente do runtime e aprovação humana de merge | Mefisto + humano | PR/`review.md` | T-06 | Parecer e decisão |
| T-08 Piloto de 6 × 2 com orçamento autorizado | Operador humano | Apenas comando opt-in, fora da CI | T-07 + autorização de gasto separada | Logs de execução observados |

Nenhum trabalho da T-03 em diante ocorre antes de T-02. T-08 não está autorizada por merge nem por freeze.

## Handoff

- Os papéis Maquiavel, Jarvis e Mefisto não implicam subagentes efetivamente invocados.
- Não alterar `backend/app/evaluation/rag.py` nem gabarito após olhar resultados de geração sem versionar nova hipótese/dataset.
- Impedimentos: SDK/modelo indisponível => `BLOCKED`; usage ausente => `INCONCLUSIVE`, não PASS.
- Qualquer mudança no schema, fonte de verdade, orçamento ou execução remota após FROZEN exige Change Request.
