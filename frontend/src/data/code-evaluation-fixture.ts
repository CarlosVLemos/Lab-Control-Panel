import rawCode001Import from './code-001-import.json'
import { loadCodeEvaluation, type EvaluationLoad } from '../domain/code-evaluation'

export const code001ImportFixture: EvaluationLoad = loadCodeEvaluation(rawCode001Import)
