# Real Evaluation v1a — imports offline, sem execução de agentes

**Issue:** #38 · **Trilha:** STANDARD · **Estado:** implementação submetida à CI, revisão e merge humanos.

## Objetivo

Comparar duas execuções da mesma tarefa de programação a partir de evidências **fornecidas pelo operador**: relatório JUnit e patch unified diff, acompanhados de um manifesto versionável. A ferramenta **não executa** os testes/patches importados, não chama agentes ou modelos, não consulta rede, não migra tabelas e não modifica o MVP Response.

O resultado COMPARABLE significa **somente** que os bundles atendem aos critérios mínimos para comparação. Não constitui veredito de qualidade de código, eficácia de Spec, segurança ou medição independente.

## Como executar

Em backend/, com as dependências existentes instaladas:

    python -m app.evaluation.code_artifacts \
      ../fixtures/without-spec/manifest.json \
      ../fixtures/with-spec/manifest.json

A ferramenta gera JSON em stdout; exit status 0 para COMPARABLE, 1 para INCONCLUSIVE, 2 para evidências inválidas.

Um diretório local contém três arquivos (nenhum é gerado pelo LCP):

    manifest.json
    tests.xml
    changes.diff

Exemplo de manifest.json para uma execução **sem Spec**:

    {
      "task_id": "code-001",
      "repository": "org/repo",
      "base_commit": "0123456789abcdef0123456789abcdef01234567",
      "agent": "mini-swe-agent",
      "model": "nome-e-versao-exata-do-modelo",
      "strategy": "WITHOUT_SPEC",
      "provenance": "link-ou-identificador-da-execucao-coletada",
      "junit_file": "tests.xml",
      "diff_file": "changes.diff",
      "usage": {
        "input_tokens": 1542,
        "output_tokens": 678,
        "cost_usd": "0.0042",
        "duration_ms": 44000
      }
    }

O segundo manifesto deve usar WITH_SPEC, com a mesma identidade de tarefa, repositório, commit base, agente, modelo e os **mesmos IDs de testcase**. Não use esse exemplo como dado observado; os números são apenas campos ilustrativos do formato.

O campo usage é **opcional** e só pode conter medições efetivamente disponíveis. Ausência é null, **nunca zero inventado**. Recolha testes e diffs em ambiente controlado, sem credenciais e com identificação de proveniência.

## Como coletar evidências reais

1. Prepare uma tarefa de código de repositório controlado, em commit inicial imutável e com suíte de aceite idêntica.
2. Execute o mesmo agente/modelo com duas estratégias (sem Spec / com Spec), guardando parâmetros e condições. **Execução deve acontecer fora do LCP**, em sandbox apropriada.
3. Capture JUnit XML de cada execução e unified diff. Guarde os artefatos como arquivos locais, sem segredos. Este importador apenas lê os arquivos; não executa o conteúdo.
4. Crie os manifestos, execute a comparação e registre os hashes SHA-256 produzidos no JSON de saída.
5. Interprete testes aprovados apenas como resultados relatados pelo JUnit importado. Faça uma verificação independente se precisar sustentar uma alegação pública mais forte.

## Invariantes

- JUnit com XML inválido, DTD/ENTITY, casos duplicados, sem IDs ou sem casos é rejeitado.
- Manifestos/artifacts com symlink, path traversal ou tamanho acima dos limites são rejeitados.
- Identidades de tarefa, repositório, base, agente/modelo ou suítes diferentes retornam INCONCLUSIVE.
- Diff é contado como adições/remoções textuais, não como medida de qualidade.
- Erros de avaliação não são convertidos em PASS ou em recomendação de estratégia.
- Esta fase não gera uma base própria nem usa dados sintéticos como evidência real.

## Continuação planejada, fora deste PR

v1b: transportar e persistir os bundles aceitos e mostrar comparação no dashboard. Isso altera API/banco, portanto requer avaliação CRITICAL e contrato FROZEN antes da implementação.

## Validação

    cd backend
    python -m pytest -q tests/test_code_artifacts.py
    python -m pytest -q

Registrar a execução real e SHA em PR antes de alegar aprovação. Não executar artefatos externos como código.
