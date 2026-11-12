<script setup lang="ts">
import { computed } from 'vue'
import { code001ImportFixture } from '../data/code-evaluation-fixture'
import { candidateCommit, metricLabel } from '../domain/code-evaluation'

const loaded = code001ImportFixture
const evaluation = computed(() => 'evaluation' in loaded ? loaded.evaluation : null)
const candidates = computed(() => evaluation.value?.observed ?? [])
const title = computed(() => candidates.value[0]?.task_id ?? 'Avaliação de código')
</script>

<template>
  <section id="main-content" class="code-hero" aria-labelledby="code-evaluation-title">
    <div>
      <p class="eyebrow">EVIDÊNCIA IMPORTADA · REAL EVALUATION V1A</p>
      <h1 id="code-evaluation-title">{{ title }}<br><em>sem veredito inventado.</em></h1>
      <p class="lede">Fixture versionada da saída do importador offline. JUnit e diffs são artefatos observados; esta tela não executa código, agentes ou testes.</p>
    </div>
    <span class="badge warning">CODE EVALUATION</span>
  </section>

  <section v-if="loaded.state === 'missing'" class="state-card" role="status"><div><strong>Evidência ausente</strong><p>{{ loaded.message }}</p></div></section>
  <section v-else-if="loaded.state === 'invalid'" class="state-card error" role="alert"><div><strong>Evidência inválida</strong><p>{{ loaded.message }}</p></div></section>

  <template v-else-if="evaluation">
    <section class="evaluation-status" :class="loaded.state === 'valid' ? 'comparable' : 'inconclusive'" aria-label="Estado da comparação">
      <div>
        <p class="eyebrow">COMPARABILIDADE ESTRUTURAL</p>
        <strong>{{ loaded.state === 'valid' ? 'COMPARÁVEL' : 'INCONCLUSIVA' }}</strong>
        <p v-if="loaded.state === 'valid'">Mesma tarefa, repositório, base, identificação declarada e IDs de testes no importador v1a.</p>
        <p v-else>{{ evaluation.reasons.join(' · ') || 'O importador não encontrou identidade suficiente para comparar.' }}</p>
      </div>
      <div class="conclusion-note"><p class="eyebrow">CONCLUSÃO EXPERIMENTAL</p><strong>SEM VENCEDOR</strong><p>Comparabilidade estrutural não mede qualidade nem prova superioridade de estratégia.</p></div>
    </section>

    <section class="metadata" aria-label="Metadados da avaliação de código">
      <span>REPOSITÓRIO · {{ candidates[0]?.repository }}</span><span>BASE · {{ candidates[0]?.base_commit }}</span><span>FONTE · JSON V1A VERSIONADO</span>
    </section>

    <section class="candidate-grid" aria-label="Candidatos comparados">
      <article v-for="candidate in candidates" :key="candidate.strategy" class="candidate-card">
        <div class="candidate-heading"><p>{{ candidate.strategy === 'WITH_SPEC' ? 'Com Spec' : 'Sem Spec' }}</p><span class="badge">{{ candidate.strategy }}</span></div>
        <strong>{{ candidate.tests.passed }}/{{ candidate.tests.total }}</strong><span class="card-caption">testes aprovados importados</span>
        <dl class="test-counts"><div><dt>Falhas</dt><dd>{{ candidate.tests.failed }}</dd></div><div><dt>Erros</dt><dd>{{ candidate.tests.errors }}</dd></div><div><dt>Ignorados</dt><dd>{{ candidate.tests.skipped }}</dd></div></dl>
        <p class="commit-line">CANDIDATO · <code>{{ candidateCommit(candidate) ?? 'Não registrado' }}</code></p>
      </article>
    </section>

    <section class="evaluation-grid">
      <article class="evidence-card">
        <div class="section-heading"><div><p class="eyebrow">PROVENIÊNCIA</p><h2>Artefatos importados</h2></div></div>
        <div v-for="candidate in candidates" :key="`${candidate.strategy}-hashes`" class="artifact-block">
          <h3>{{ candidate.strategy }}</h3><p class="provenance">{{ candidate.provenance }}</p>
          <dl class="hash-list"><div><dt>Manifesto</dt><dd><code>{{ candidate.source_hashes.manifest_sha256 }}</code></dd></div><div><dt>JUnit</dt><dd><code>{{ candidate.source_hashes.junit_sha256 }}</code></dd></div><div><dt>Diff</dt><dd><code>{{ candidate.source_hashes.diff_sha256 }}</code></dd></div></dl>
        </div>
      </article>

      <aside class="evidence-card">
        <p class="eyebrow">MÉTRICAS DO AGENTE</p><h2>Não observadas</h2>
        <dl class="unknown-list"><div><dt>Modelo</dt><dd>{{ candidates[0]?.model === 'UNKNOWN-NOT-RECORDED' ? 'Desconhecido' : candidates[0]?.model }}</dd></div><div><dt>Tokens de entrada</dt><dd>{{ candidates[0] ? metricLabel(candidates[0], 'input_tokens') : 'Desconhecida' }}</dd></div><div><dt>Tokens de saída</dt><dd>{{ candidates[0] ? metricLabel(candidates[0], 'output_tokens') : 'Desconhecida' }}</dd></div><div><dt>Custo</dt><dd>{{ candidates[0] ? metricLabel(candidates[0], 'cost_usd') : 'Desconhecida' }}</dd></div><div><dt>Duração do agente</dt><dd>{{ candidates[0] ? metricLabel(candidates[0], 'duration_ms') : 'Desconhecida' }}</dd></div></dl>
        <p class="detail-note">A duração da suíte não é apresentada como duração do agente. Campos ausentes continuam desconhecidos.</p>
      </aside>
    </section>

    <section class="evidence-card diff-card" aria-label="Resumo de diffs">
      <div class="section-heading"><div><p class="eyebrow">ALTERAÇÕES</p><h2>Resumo dos diffs</h2></div><span>Contagem textual, não medida de qualidade</span></div>
      <div class="diff-summary"><div v-for="candidate in candidates" :key="`${candidate.strategy}-diff`"><strong>{{ candidate.strategy }}</strong><p><span class="added">+{{ candidate.diff.added_lines }}</span> linhas adicionadas · <span class="removed">−{{ candidate.diff.removed_lines }}</span> removidas</p></div></div>
    </section>

    <p class="importer-note">{{ evaluation.interpretation }}</p>
  </template>
</template>
