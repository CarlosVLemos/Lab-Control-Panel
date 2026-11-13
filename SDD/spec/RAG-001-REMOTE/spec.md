# RAG-001-REMOTE — MVP de avaliação real

**Estado:** DRAFT (não FROZEN) · **Issue:** #45 · **Experimento:** #43 · **PR de contrato:** #46 · **Track:** CRITICAL pelo uso de credenciais e gastos, não pela complexidade do produto.

## Intenção de produto

O Lab Control Panel é um **MVP de portfólio**. Deve demonstrar engenharia competente com escolhas contidas, dados verificáveis e uma experiência utilizável. O diferencial é **executar e explicar um experimento real**, não imitar a infraestrutura de uma plataforma corporativa.

**Princípio de corte:** se uma funcionalidade não torna o piloto mais confiável, reproduzível ou fácil de entender, fica fora do MVP.

## Entrega inicial

- Um experimento pareado com **6 casos × 2 braços = 12 gerações**, `NO_CONTEXT` vs `SEMANTIC_RAG` (top-k=3), modelo e parâmetros iguais, mesma pergunta. Embeddings do corpus e das consultas têm custos e contagens próprios.
- Um executor Python via CLI, **offline/dry-run por padrão**; execução real somente por opção explícita e orçamento autorizado em etapa separada.
- Registro local sanitizado em JSONL e **um relatório Markdown/JSON resumido** pronto para apresentação: resposta visível por caso, avaliação humana, recuperação, tokens, latência, custo estimado e falhas. Pode ser importado pelo dashboard existente posteriormente; sem UI nova obrigatória nesta fase.
- Uma rubrica humana pequena e pré-definida: **correção factual 0/1/2**, adequação de abstenção/recusa, e evidência de fontes apenas quando houver contexto. **Um revisor cego ao braço**, com limitação explícita; não contratar dois juízes nem inventar significância estatística.
- Corpus **fictício** e seleção congelada em [pilot-manifest.json](pilot-manifest.json); fingerprint SHA-256 validado no início, antes de conectar ao provedor.

## Retenção mínima adequada ao MVP

- Versionar no GitHub somente corpus, rubrica, parâmetros, fingerprints, resultados **sanitizados e fictícios**, números observados e relatório reproduzível.
- Não persistir chave, headers, request bruto, traceback nem resposta crua do SDK; credencial só por ambiente.
- Arquivos temporários de depuração são **locais, ignorados pelo Git**, apagados após a validação/publicação do relatório ou por comando explícito de limpeza. Sem jobs de expurgo, banco de logs, política de retenção corporativa ou prazo arbitrário de 14/30/180 dias.
- Se algum dia houver dados pessoais reais, este contrato não basta: redefinir finalidade, minimização, retenção e acesso em uma fase posterior.

## Fora do MVP

Langfuse/Promptfoo como dependência, framework de agentes, vetor externo, banco de dados novo, serviço HTTP novo, workers, orquestração, múltiplos avaliadores, LLM-as-judge, gerenciamento multiusuário, telemetria corporativa, ranking estatístico, pipeline contínuo de experimentos ou execução completa de 216 chamadas.

## Limites e honestidade

Amostra pequena de integração; nenhuma alegação de vencedor geral. Falha, resposta inválida, custo desconhecido ou revisão pendente são apresentados como tal; não se preenchem números desconhecidos com zero. Um eventual resultado favorável a RAG é **observação do piloto**, não demonstração universal.

**Governança:** aprovação humana do [contrato](contract.md) como FROZEN é necessária **antes do runtime**. Revisão independente exige controles críticos; aprovação financeira e merge são decisões distintas. Nenhuma execução paga autorizada por esta PR.
