import type { ExperimentReport } from '../domain/report'

export interface ReportSource { execute(): Promise<ExperimentReport> }

export class HttpReportSource implements ReportSource {
  constructor(private readonly url: string) {}

  async execute(): Promise<ExperimentReport> {
    const response = await fetch(this.url, { method: 'POST' })
    if (!response.ok) throw new Error(`Não foi possível executar a comparação (${response.status}).`)
    return response.json() as Promise<ExperimentReport>
  }
}
