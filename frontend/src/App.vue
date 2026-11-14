<script setup lang="ts">
import { computed, ref } from 'vue'
import CodeEvaluationView from './components/CodeEvaluationView.vue'
import ObservabilityView from './components/ObservabilityView.vue'
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
const activeView = ref<'response' | 'code' | 'observability'>('response')
const filters: { value: Filter; label: string }[] = [
  { value: 'all', label: 'Todos' }, { value: 'improved', label: 'Melhorou' },
  { value: 'regressed', label: 'Regrediu' }, { value: 'stable', label: 'Estável' },
]

const filteredCases = computed(() => report.value?.cases.filter((item) => filter.value === 'all' || evidenceState(item) === filter.value) ?? [])
const delta = computed(() => report.value ? accuracy(report.value.summary.candidate.passed, report.value.summary.candidate.total) - accuracy(report.value.summary.baseline.passed, report.value.summary.baseline.total) : 0)

const source: ReportSource = import.meta.env.VITE_DEMO_OFFLINE === 'true'
  ? fixtureSource
  : new HttpReportSource('/api/demo/experiments')
const sourceLabel = import.meta.env.VITE_DEMO_OFFLINE === 'true' ? 'Fixture offline' : 'API'

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
      <a class="brand" href="#main-content" aria-label="Ir para o conteúdo">LCP</a>
      <nav class="view-switcher" aria-label="Selecionar avaliação"><button type="button" :class="{ active: activeView === 'response' }" @click="activeView = 'response'">Classificação</button><button type="button" :class="{ active: activeView === 'code' }" @click="activeView = 'code'">Código</button><button type="button" :class="{ active: activeView === 'observability' }" @click="activeView = 'observability'">Observabilidade</button></nav>
    </header>

    <template v-if="activeView === 'response'">
    <section id="main-content" class="hero" aria-labelledby="page-title">
      <div>
        <h1 id="page-title">Comparação de classificadores</h1>
        <p class="lede"><code>support-intents/v1</code> · dados sintéticos</p>
      </div>
      <div class="hero-actions">
        <button class="button secondary" type="button" @click="execute">Executar comparação</button>
      </div>
    </section>

    <section v-if="state === 'loading'" class="state-card" role="status" aria-live="polite">
      <span class="spinner" aria-hidden="true"></span><div><strong>Carregando relatório</strong></div>
    </section>

    <section v-else-if="state === 'error'" class="state-card error" role="alert">
      <div><strong>Relatório indisponível</strong><p>{{ errorMessage }}</p></div>
      <button class="button secondary" type="button" @click="execute">Tentar novamente</button>
    </section>

    <section v-else-if="state === 'empty'" class="state-card" role="status">
      <div><strong>Nenhuma comparação executada</strong></div>
    </section>

    <template v-else-if="report">
      <section class="metadata" aria-label="Metadados do relatório">
        <span>Experimento: {{ report.experimentId }}</span><span>Dataset: {{ report.dataset.id }}/{{ report.dataset.version }}</span><span>Fonte: {{ sourceLabel }}</span>
      </section>

      <section class="score-grid" aria-label="Comparação de acurácia">
        <article class="score-card baseline">
          <p>{{ report.baseline.label }}</p><strong>{{ accuracy(report.summary.baseline.passed, report.summary.baseline.total) }}<small>%</small></strong>
          <span>{{ report.summary.baseline.passed }}/{{ report.summary.baseline.total }} aprovados</span>
        </article>
        <article class="score-card candidate">
          <p>{{ report.candidate.label }}</p><strong>{{ accuracy(report.summary.candidate.passed, report.summary.candidate.total) }}<small>%</small></strong>
          <span>{{ report.summary.candidate.passed }}/{{ report.summary.candidate.total }} aprovados</span>
        </article>
        <article class="delta-card">
          <p>Variação</p><strong>{{ delta > 0 ? '+' : '' }}{{ delta }} <small>p.p.</small></strong>
        </article>
      </section>

      <section class="workspace" aria-label="Casos e detalhes">
        <div class="case-panel">
          <div class="section-heading"><h2>Casos</h2><span>{{ filteredCases.length }} visíveis</span></div>
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
            <h2>{{ selected.id }}</h2><p class="input">“{{ selected.input.text }}”</p>
            <dl><div><dt>Esperado</dt><dd><code>{{ selected.expected.label }}</code></dd></div><div><dt>Baseline</dt><dd><code>{{ displayOutput(selected.baseline.output) }}</code> · {{ selected.baseline.passed ? 'passou' : 'falhou' }}</dd></div><div><dt>Candidato</dt><dd><code>{{ displayOutput(selected.candidate.output) }}</code> · {{ selected.candidate.passed ? 'passou' : 'falhou' }}</dd></div></dl>
          </template>
          <template v-else><h2>Selecione um caso</h2><p>Escolha uma linha na tabela.</p></template>
        </aside>
      </section>
    </template>

    </template>
    <CodeEvaluationView v-else-if="activeView === 'code'" />
    <ObservabilityView v-else />
  </main>
</template>
