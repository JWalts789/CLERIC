// ============================================================
// C.L.E.R.I.C. — Type Definitions
// ============================================================

// WebSocket Events
export interface StageStartEvent {
  type: 'stage_start';
  stage: string;
  timestamp: string;
}

export interface StageCompleteEvent {
  type: 'stage_complete';
  stage: string;
  data: Record<string, any>;
  tokens: Record<string, number>;
  content: string;
  tool_calls: number;
  timestamp: string;
}

export interface PipelineCompleteEvent {
  type: 'pipeline_complete';
  result: PipelineResult;
  mermaid_diagrams: Record<string, string>;
  timestamp: string;
}

export interface ErrorEvent {
  type: 'error';
  message: string;
  timestamp: string;
}

export type WSEvent = StageStartEvent | StageCompleteEvent | PipelineCompleteEvent | ErrorEvent;

// Pipeline Data
export interface PipelineResult {
  query: string;
  timestamp: string;
  stages: Record<string, StageData>;
  evaluation: Record<string, any>;
  overall_grade: string;
  total_tokens: { input: number; output: number };
  duration_seconds: number;
}

export interface StageData {
  agent: string;
  role: string;
  data: Record<string, any>;
  tool_calls: Array<Record<string, any>>;
  tokens: { input: number; output: number };
}

export interface Source {
  url: string;
  title: string;
  claims: string[];
  perspective: string;
  credibility_notes: string;
  conflict_of_interest: string;
  conflict_detail: string;
}

// Stage Metadata
export type StageName = 'bias_detection' | 'research' | 'fact_checking' | 'devils_advocate' | 'synthesis' | 'evaluation';
export type StageStatus = 'pending' | 'running' | 'complete' | 'error';

export interface StageInfo {
  key: StageName;
  icon: string;
  label: string;
  color: string;
}

export const STAGES: StageInfo[] = [
  { key: 'bias_detection', icon: '\u{1F6E1}\uFE0F', label: 'Bias Detection', color: '#e53e3e' },
  { key: 'research', icon: '\u{1F50E}', label: 'Research', color: '#3182ce' },
  { key: 'fact_checking', icon: '\u2705', label: 'Fact Checking', color: '#38a169' },
  { key: 'devils_advocate', icon: '\u{1F608}', label: "Devil's Advocate", color: '#d69e2e' },
  { key: 'synthesis', icon: '\u{1F4DD}', label: 'Synthesis', color: '#805ad5' },
  { key: 'evaluation', icon: '\u{1F4CA}', label: 'Evaluation', color: '#dd6b20' },
];

// Fact Check Status
export type ClaimStatus = 'VERIFIED' | 'DISPUTED' | 'UNVERIFIED' | 'FALSE';

export interface ClaimResult {
  claim: string;
  status: ClaimStatus;
  confidence: number;
  supporting_sources: number;
  contradicting_sources: number;
  explanation: string;
}

// Evaluation
export interface EvaluationDimension {
  name: string;
  score: number;
  feedback: string;
}

// Challenge
export interface Challenge {
  challenge: string;
  severity: 'HIGH' | 'MEDIUM' | 'LOW';
  type: string;
  recommendation: string;
}
