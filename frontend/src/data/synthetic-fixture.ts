import type { ExperimentReport } from '../domain/report'
import type { ReportSource } from './report-source'

export const syntheticReport: ExperimentReport = {
  experimentId: 'demo-support-intents-v1',
  synthetic: true,
  dataset: { id: 'support-intents', version: 'v1' },
  baseline: { id: 'baseline-v1', label: 'Baseline' },
  candidate: { id: 'candidate-v2', label: 'Candidato' },
  summary: { baseline: { passed: 3, total: 5 }, candidate: { passed: 4, total: 5 } },
  cases: [
    { id: 'case-01', input: { text: 'Meu pedido veio errado' }, expected: { label: 'complaint' }, baseline: { output: { label: 'question' }, passed: false }, candidate: { output: { label: 'complaint' }, passed: true } },
    { id: 'case-02', input: { text: 'Onde está minha entrega?' }, expected: { label: 'tracking' }, baseline: { output: { label: 'tracking' }, passed: true }, candidate: { output: { label: 'tracking' }, passed: true } },
    { id: 'case-03', input: { text: 'Quero cancelar este pedido' }, expected: { label: 'cancel' }, baseline: { output: { label: 'cancel' }, passed: true }, candidate: { output: { label: 'cancel' }, passed: true } },
    { id: 'case-04', input: { text: 'Como uso meu cupom?' }, expected: { label: 'coupon' }, baseline: { output: { label: 'coupon' }, passed: true }, candidate: { output: { label: 'coupon' }, passed: false } },
    { id: 'case-05', input: { text: 'Preciso falar com atendimento' }, expected: { label: 'human_support' }, baseline: { output: { label: 'question' }, passed: false }, candidate: { output: { label: 'human_support' }, passed: true } }
  ]
}

export const fixtureSource: ReportSource = { async execute() { return syntheticReport } }
