import type { ExperimentReport } from '../domain/report'

export interface ReportSource { load(): Promise<ExperimentReport> }

export class HttpReportSource implements ReportSource {
  constructor(private readonly url: string) {}

  async load(): Promise<ExperimentReport> {
    const response = await fetch(this.url)
    if (!response.ok) throw new Error(`Não foi possível carregar o relatório (${response.status}).`)
    return response.json() as Promise<ExperimentReport>
  }
}
