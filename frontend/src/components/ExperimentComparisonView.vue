<script setup lang="ts">
import { computed, ref } from 'vue'
import comparisonText from '../data/evidence/exp-002-astropy-12907.json?raw'
import {
  formatToolArguments,
  issueContext,
  parseExperimentComparison,
  parseUnifiedDiff,
  toolCalls,
  type ExperimentEvent,
} from '../domain/experiment-comparison'

const comparison = parseExperimentComparison(comparisonText)
const selectedModel = ref(comparison.runs[0].model)
const selectedEventIndex = ref(0)
const selectedRun = computed(() => comparison.runs.find((run) => run.model === selectedModel.value) ?? comparison.runs[0])
const selectedEvent = computed(() => selectedRun.value.events[selectedEventIndex.value] ?? selectedRun.value.events[0])
const callsByModel = computed(() => Object.fromEntries(comparison.runs.map((run) => [run.model, toolCalls(run)])))
const diffsByModel = computed(() => Object.fromEntries(comparison.runs.map((run) => [run.model, parseUnifiedDiff(run.patch)])))

function selectRun(model: string): void {
  selectedModel.value = model
  selectedEventIndex.value = 0
}

function selectEvent(event: ExperimentEvent): void {
  selectedEventIndex.value = event.index
}

function formatCost(value: number | null): string {
  return value === null ? '—' : `US$ ${value.toFixed(8).replace(/0+$/, '').replace(/\.$/, '')}`
}
</script>

<template>
  <section id="main-content" class="experiment-hero" aria-labelledby="experiment-title">
    <div>
      <h1 id="experiment-title">Comparação de agentes</h1>
      <p class="lede"><code>{{ comparison.instance_id }}</code> · resultados publicados</p>
    </div>
    <div class="case-study-note">SWE-bench Verified · estudo de caso, não ranking</div>
  </section>

  <section class="metadata" aria-label="Procedência do experimento">
    <span>Contrato: {{ comparison.schema_version }}</span><span>Comparabilidade: mesma issue</span><span>Reexecução local: não</span>
  </section>

  <section class="issue-card" aria-labelledby="issue-context-title">
    <div class="section-heading"><h2 id="issue-context-title">Problema original</h2><span>{{ comparison.instance_id }}</span></div>
    <pre>{{ issueContext(comparison) }}</pre>
  </section>

  <section class="agent-comparison" aria-label="Tentativas publicadas">
    <article v-for="run in comparison.runs" :key="run.model" class="agent-run-card">
      <div class="candidate-heading"><h2>{{ run.model }}</h2><span class="result pass">Resolvido · publicado</span></div>
      <dl class="run-metrics">
        <div><dt>Chamadas de API</dt><dd>{{ run.reported_api_calls ?? '—' }}</dd></div>
        <div><dt>Chamadas de ferramenta</dt><dd>{{ callsByModel[run.model]?.length ?? 0 }}</dd></div>
        <div><dt>Mensagens</dt><dd>{{ run.message_count }}</dd></div>
        <div><dt>Custo reportado</dt><dd>{{ formatCost(run.reported_cost_usd) }}</dd></div>
        <div><dt>Duração</dt><dd>—</dd></div>
        <div><dt>Patch</dt><dd>{{ run.patch_status === 'provided' ? 'Disponível' : 'Não registrado' }}</dd></div>
      </dl>
      <p class="run-status">Saída: {{ run.exit_status }} · resultado e custo declarados pela fonte.</p>
      <dl class="source-block">
        <div><dt>Arquivo</dt><dd><a :href="run.source.url" rel="noreferrer">{{ run.source.path }}</a></dd></div>
        <div><dt>Revisão</dt><dd><code>{{ run.source.revision }}</code></dd></div>
        <div><dt>SHA-256 local</dt><dd><code>{{ run.source.local_sha256 }}</code></dd></div>
      </dl>
    </article>
  </section>

  <section class="patch-card" aria-labelledby="patch-title">
    <div class="section-heading"><h2 id="patch-title">Patches publicados</h2><span>0 arquivos disponíveis</span></div>
    <p v-if="comparison.runs.every((run) => run.patch === null)" class="empty-evidence">O campo <code>info.submission</code> está vazio nas duas trajetórias. O LCP não reconstrói patches a partir dos logs.</p>
    <template v-for="run in comparison.runs" :key="`diff-${run.model}`">
      <article v-for="file in diffsByModel[run.model]" :key="`${run.model}-${file.path}`" class="diff-file">
        <h3>{{ run.model }} · {{ file.path }}</h3><span class="added">+{{ file.additions }}</span> <span class="removed">−{{ file.removals }}</span><pre>{{ file.lines.join('\n') }}</pre>
      </article>
    </template>
  </section>

  <section class="trajectory-card" aria-labelledby="trajectory-title">
    <div class="section-heading"><h2 id="trajectory-title">Ações e chamadas de ferramentas</h2><span>{{ selectedRun.events.length }} mensagens</span></div>
    <div class="run-switcher" role="group" aria-label="Selecionar agente">
      <button v-for="run in comparison.runs" :key="run.model" type="button" :class="{ active: selectedModel === run.model }" :aria-pressed="selectedModel === run.model" @click="selectRun(run.model)">{{ run.model }}</button>
    </div>
    <div class="trajectory-grid">
      <div class="trajectory-list">
        <button v-for="event in selectedRun.events" :key="event.index" type="button" :class="{ selected: selectedEvent?.index === event.index }" :aria-pressed="selectedEvent?.index === event.index" @click="selectEvent(event)">
          <span>{{ event.index + 1 }}</span><strong>{{ event.role }}</strong><small>{{ event.tool_calls.length ? `${event.tool_calls.length} chamada(s)` : 'sem chamada' }}</small>
        </button>
      </div>
      <aside v-if="selectedEvent" class="trajectory-detail" aria-live="polite">
        <h3>Mensagem {{ selectedEvent.index + 1 }} · {{ selectedEvent.role }}</h3>
        <pre>{{ selectedEvent.content ?? '—' }}</pre>
        <div v-for="(call, index) in selectedEvent.tool_calls" :key="index" class="tool-call-block">
          <strong>{{ typeof call === 'object' && call && 'function' in call ? String(call.function) : 'Ferramenta' }}</strong>
          <pre>{{ formatToolArguments(typeof call === 'object' && call && 'arguments' in call ? call.arguments : null) }}</pre>
        </div>
      </aside>
    </div>
  </section>
</template>
