<script setup lang="ts">
import { computed, ref } from 'vue'
import { fixtureSource } from './data/synthetic-fixture'
import { HttpReportSource, type ReportSource } from './data/report-source'
import { accuracy, displayOutput, evidenceState, type ExperimentCase, type ExperimentReport } from './domain/report'

type ViewState = 'loading' | 'ready' | 'empty' | 'error'
type Filter = 'all' | 'improved' | 'regressed' | 'stable'

const report = ref<ExperimentReport | null>(null)
const state = ref<ViewState>('empty')
const selected = ref<ExperimentCase | null>(null)
const filter = ref<Filter>('all')
const errorMessage = ref('')
const filters: { value: Filter; label: string }[] = [
  { value: 'all', label: 'Todos' }, { value: 'improved', label: 'Melhorou' },
  { value: 'regressed', label: 'Regrediu' }, { value: 'stable', label: 'Estável' },
]

const filteredCases = computed(() => report.value?.cases.filter((item) => filter.value === 'all' || evidenceState(item) === filter.value) ?? [])
const delta = computed(() => report.value ? accuracy(report.value.summary.candidate.passed, report.value.summary.candidate.total) - accuracy(report.value.summary.baseline.passed, report.value.summary.baseline.total) : 0)

const source: ReportSource = import.meta.env.VITE_DEMO_OFFLINE === 'true'
  ? fixtureSource
  : new HttpReportSource('/api/demo/experiments')
const sourceLabel = import.meta.env.VITE_DEMO_OFFLINE === 'true' ? 'FIXTURE OFFLINE' : 'API PERSISTIDA'

function demonstrateError() {
  void executeFrom({ execute: async () => { throw new Error('Falha simulada da fonte de dados. Nenhum dado de fallback foi exibido.') } })
}

async function executeFrom(selectedSource: ReportSource) {
  state.value = 'loading'
  report.value = null
  selected.value = null
  errorMessage.value = ''
  try {
    const next = await selectedSource.execute()
    report.value = next
    state.value = next.cases.length === 0 ? 'empty' : 'ready'
  } catch (error) {
    state.value = 'error'
    errorMessage.value = error instanceof Error ? error.message : 'Não foi possível carregar o relatório.'
  }
}

function execute() { return executeFrom(source) }
</script>

<template>
  <main class="shell">
    <header class="topbar">
      <a class="brand" href="#main-content" aria-label="Ir para a comparação">LCP<span>/</span> LAB</a>
      <div class="badges" aria-label="Contexto da demonstração">
        <span class="badge warning">DEMONSTRAÇÃO</span><span class="badge">DADOS SINTÉTICOS</span><span class="badge">MOCK</span>
      </div>
    </header>

    <section id="main-content" class="hero" aria-labelledby="page-title">
      <div>
        <p class="eyebrow">Experimento de classificação · dataset sintético</p>
        <h1 id="page-title">Compare decisões.<br><em>Não invente confiança.</em></h1>
        <p class="lede">Uma visão auditável do dataset <code>support-intents/v1</code>. Resultados persistidos de {{ report?.cases.length ?? 0 }} casos sintéticos; sem execução de IA real.</p>
      </div>
      <div class="hero-actions">
        <button class="button secondary" type="button" @click="execute">Executar comparação</button>
        <button class="button ghost" type="button" @click="demonstrateError">Ver estado de erro</button>
      </div>
    </section>

    <section v-if="state === 'loading'" class="state-card" role="status" aria-live="polite">
      <span class="spinner" aria-hidden="true"></span><div><strong>Carregando relatório</strong><p>A fonte de dados está sendo consultada.</p></div>
    </section>

    <section v-else-if="state === 'error'" class="state-card error" role="alert">
      <div><strong>Relatório indisponível</strong><p>{{ errorMessage }}</p><p>Nenhum resultado sintético é usado como fallback para ocultar a falha.</p></div>
      <button class="button secondary" type="button" @click="execute">Tentar novamente</button>
    </section>

    <section v-else-if="state === 'empty'" class="state-card" role="status">
      <div><strong>Nenhuma comparação executada</strong><p>Execute a comparação para carregar os resultados persistidos.</p></div>
    </section>

    <template v-else-if="report">
      <section class="metadata" aria-label="Metadados do relatório">
        <span>EXPERIMENTO · {{ report.experimentId }}</span><span>DATASET · {{ report.dataset.id }}/{{ report.dataset.version }}</span><span>FONTE · {{ sourceLabel }}</span>
      </section>

      <section class="score-grid" aria-label="Comparação de acurácia">
        <article class="score-card baseline">
          <p>{{ report.baseline.label }}</p><strong>{{ accuracy(report.summary.baseline.passed, report.summary.baseline.total) }}<small>%</small></strong>
          <span>{{ report.summary.baseline.passed }} de {{ report.summary.baseline.total }} casos aprovados</span>
        </article>
        <article class="score-card candidate">
          <p>{{ report.candidate.label }}</p><strong>{{ accuracy(report.summary.candidate.passed, report.summary.candidate.total) }}<small>%</small></strong>
          <span>{{ report.summary.candidate.passed }} de {{ report.summary.candidate.total }} casos aprovados</span>
        </article>
        <article class="delta-card">
          <p>Diferença observada</p><strong>+{{ delta }} <small>p.p.</small></strong><span>Derivada da fixture; não é métrica de produção.</span>
        </article>
      </section>

      <section class="workspace" aria-label="Casos e detalhes">
        <div class="case-panel">
          <div class="section-heading"><div><p class="eyebrow">EVIDÊNCIAS</p><h2>Casos executados</h2></div><span>{{ filteredCases.length }} visíveis</span></div>
          <div class="filters" role="group" aria-label="Filtrar evidências">
            <button v-for="option in filters" :key="option.value" class="filter" :class="{ active: filter === option.value }" type="button" :aria-pressed="filter === option.value" @click="filter = option.value">
              {{ option.label }}
            </button>
          </div>
          <div class="table-wrap">
            <table>
              <thead><tr><th>Caso</th><th>Esperado</th><th>Baseline</th><th>Candidato</th><th>Estado</th></tr></thead>
              <tbody>
                <tr v-for="item in filteredCases" :key="item.id" tabindex="0" :class="{ selected: selected?.id === item.id }" @click="selected = item" @keydown.enter="selected = item" @keydown.space.prevent="selected = item">
                  <td><strong>{{ item.id }}</strong><span>{{ item.input.text }}</span></td><td><code>{{ item.expected.label }}</code></td>
                  <td><span class="result" :class="item.baseline.passed ? 'pass' : 'fail'">{{ item.baseline.passed ? 'Passou' : 'Falhou' }}</span></td>
                  <td><span class="result" :class="item.candidate.passed ? 'pass' : 'fail'">{{ item.candidate.passed ? 'Passou' : 'Falhou' }}</span></td>
                  <td><span class="evidence" :class="evidenceState(item)">{{ { improved: 'Melhorou', regressed: 'Regrediu', stable: 'Estável' }[evidenceState(item)] }}</span></td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <aside class="detail-panel" aria-live="polite">
          <template v-if="selected">
            <p class="eyebrow">DETALHE DO CASO</p><h2>{{ selected.id }}</h2><p class="input">“{{ selected.input.text }}”</p>
            <dl><div><dt>Esperado</dt><dd><code>{{ selected.expected.label }}</code></dd></div><div><dt>Baseline</dt><dd><code>{{ displayOutput(selected.baseline.output) }}</code> · {{ selected.baseline.passed ? 'passou' : 'falhou' }}</dd></div><div><dt>Candidato</dt><dd><code>{{ displayOutput(selected.candidate.output) }}</code> · {{ selected.candidate.passed ? 'passou' : 'falhou' }}</dd></div></dl>
            <p class="detail-note">Evidência: <strong>{{ { improved: 'candidato corrigiu a decisão', regressed: 'candidato perdeu uma decisão', stable: 'sem mudança observada' }[evidenceState(selected)] }}</strong>.</p>
          </template>
          <template v-else><p class="eyebrow">DETALHE DO CASO</p><h2>Selecione uma evidência</h2><p>Use Tab e Enter ou clique numa linha para inspecionar esperado, obtido e estado.</p></template>
        </aside>
      </section>
    </template>

    <footer>LAB CONTROL PANEL · DEMONSTRAÇÃO COM DADOS SINTÉTICOS · custo, latência e tokens não foram capturados.</footer>
  </main>
</template>
