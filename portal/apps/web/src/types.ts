export type Role = 'analyst' | 'reviewer' | 'requester' | 'auditor' | 'admin'
export interface User {
  id: string
  tenant_id: string
  name: string
  email: string
  role: Role
  preferences: { language: 'en' | 'ar'; digest: boolean }
}
export interface Evidence {
  id: string
  title: string
  filename: string
  category: string
  classification: string
  language: string
  status: string
  version: number
  page_count: number
  size: number
  source: string
  created_at: string
  pages?: {
    page: number
    text: string
    method?: string
    ocr_confidence?: number
    warnings?: string[]
  }[]
}
export interface Quote {
  source_version?: number
  review_id?: string
  supplier: string
  amount: string
  currency: string
  delivery_days: number | ''
  valid_until: string
  document_id: string
  tax_percent: string
  total?: string
  tax?: string
  issues?: string[]
}
export interface Approval {
  id: string
  status: string
  revision: number
  requested_by: string
}
export interface ProcurementCase {
  evidence_versions: Record<string, number>
  id: string
  reference: string
  title: string
  description: string
  department: string
  created_by: string
  budget: string
  currency: string
  due_date: string
  priority: string
  status: string
  revision: number
  document_ids: string[]
  quotes: Quote[]
  comparison: { quotes?: Quote[]; issues?: string[]; calculation?: string; rules_version?: string }
  approval: Approval | null
  created_at: string
  evidence_restricted?: boolean
}
export interface WorkflowRun {
  id: string
  case_id: string
  actor_id: string
  revision: number
  status: string
  steps: { name: string; status: string; detail: string }[]
  created_at: string
}
export interface AuditEvent {
  id: string
  actor: string
  role: string
  action: string
  resource: string
  details: Record<string, unknown>
  created_at: string
}
export interface Ticket {
  id: string
  title: string
  category: string
  priority: string
  status: string
  created_by: string
  created_at: string
}
export interface Workload {
  history: { date: string; label: string; volume: number }[]
  forecast: { date: string; label: string; volume: number; lower: number; upper: number }[]
  model: string
  baseline: string
  holdout_mae: number
  source: string
  uncertainty: string
}
export interface Workspace {
  tenant: { id: string; name: string }
  cases: ProcurementCase[]
  documents: Evidence[]
  runs: WorkflowRun[]
  events: AuditEvent[]
  tickets: Ticket[]
  analytics: Workload
  config: {
    auth_mode: string
    model_mode: string
    retrieval_mode: string
    ocr_mode: string
    environment: string
    database: string
  }
  stats: {
    active_cases: number
    pending_reviews: number
    documents: number
    completed: number
    budget: string
  }
}
export interface Citation {
  document_id: string
  title: string
  version: number
  page: number
  text: string
  score: number
}
export interface Answer {
  status: string
  answer: string
  citations: Citation[]
  mode: string
  reason?: string
  requested_fields?: string[]
}

export interface QuotationDraft {
  extraction_id: string
  extractor_version: string
  source: { document_id: string; title: string; version: number; sha256: string }
  requires_review: boolean
  notice: string
  fields: Record<
    string,
    { value: string | null; status: string; evidence: { page: number; excerpt: string }[] }
  >
}

export interface SourceVersion {
  id: string
  version: number
  filename: string
  content_hash: string
  status: string
  size: number
  created_at: string
}
export interface ExtractionHistory {
  id: string
  actor_id: string
  extractor_version: string
  created_at: string
  payload: QuotationDraft
  reviews: {
    id: string
    actor_id: string
    actor_name?: string
    reason: string
    created_at: string
    values: Record<string, string | null>
    changes: Record<string, { before: string | null; after: string | null }>
  }[]
}
