import { useEffect, useRef, useState } from 'react'
import type { FormEvent } from 'react'
import {
  ArrowDownToLine,
  ArrowRight,
  ArrowUpRight,
  Check,
  CheckCircle2,
  ChevronRight,
  Clock3,
  FileText,
  Info,
  Link2,
  LoaderCircle,
  LockKeyhole,
  Plus,
  Printer,
  ShieldCheck,
  ShoppingBag,
  Trash2,
  UserCheck,
  Workflow,
  X,
} from 'lucide-react'
import { api } from './api'
import { useWorkspace } from './context'
import { useI18n } from './i18n'
import { Badge, Empty, Field, humanDate, Modal, money } from './ui'
import type {
  Evidence,
  ProcurementCase,
  Quote,
  QuotationDraft,
  SourceVersion,
  ExtractionHistory,
} from './types'

function blankQuote(): Quote {
  return {
    supplier: '',
    amount: '',
    currency: 'AED',
    delivery_days: 14,
    valid_until: new Date(Date.now() + 30 * 86400000).toISOString().slice(0, 10),
    document_id: '',
    tax_percent: '5',
  }
}

export function NewCase({ onClose }: { onClose: () => void }) {
  const { data, refresh, notify, openCase } = useWorkspace(),
    { t } = useI18n()
  const [quotes, setQuotes] = useState<Quote[]>([]),
    [docs, setDocs] = useState<string[]>([]),
    [busy, setBusy] = useState(false),
    [error, setError] = useState('')
  async function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    const f = new FormData(e.currentTarget)
    setBusy(true)
    setError('')
    try {
      const payload = {
        title: f.get('title'),
        description: f.get('description'),
        department: f.get('department'),
        budget: f.get('budget'),
        currency: f.get('currency'),
        due_date: f.get('due_date'),
        priority: f.get('priority'),
        document_ids: [...new Set([...docs, ...quotes.map((q) => q.document_id)])],
        quotes,
      }
      const c = await api<ProcurementCase>('/api/v1/cases', {
        method: 'POST',
        body: JSON.stringify(payload),
      })
      await refresh()
      notify('Procurement case created. Add or verify evidence, then run the comparison.')
      onClose()
      openCase(c.id)
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setBusy(false)
    }
  }
  return (
    <Modal title={t('New case')} wide onClose={onClose}>
      <form onSubmit={submit}>
        <div className="form-intro">
          <span className="case-glyph tone-0">
            <ShoppingBag size={23} />
          </span>
          <div>
            <h3>A clear request is a better beginning.</h3>
            <p>Create a draft now. Add source-linked quotations before requesting review.</p>
          </div>
        </div>
        <div className="form-section-label">
          <span>01</span>Case information
        </div>
        <Field label="Title">
          <input
            name="title"
            placeholder="e.g. Cloud infrastructure renewal"
            required
            minLength={4}
            maxLength={200}
          />
        </Field>
        <Field label="Description">
          <textarea
            name="description"
            placeholder="What are you procuring, and what should reviewers know?"
            rows={3}
            maxLength={4000}
          />
        </Field>
        <div className="form-grid">
          <Field label="Department">
            <select name="department">
              {[
                'Digital Services',
                'IT Operations',
                'Human Capital',
                'Corporate Services',
                'Cybersecurity',
                'Strategy & Planning',
              ].map((x) => (
                <option key={x}>{x}</option>
              ))}
            </select>
          </Field>
          <Field label="Budget">
            <input
              name="budget"
              type="number"
              min="0.01"
              max="100000000"
              step="0.01"
              required
              placeholder="0.00"
            />
          </Field>
          <Field label="Currency">
            <select name="currency">
              <option>AED</option>
              <option>USD</option>
              <option>EUR</option>
            </select>
          </Field>
          <Field label="Due date">
            <input
              name="due_date"
              type="date"
              required
              defaultValue={new Date(Date.now() + 14 * 86400000).toISOString().slice(0, 10)}
            />
          </Field>
          <Field label="Priority">
            <select name="priority">
              <option>Normal</option>
              <option>High</option>
              <option>Urgent</option>
            </select>
          </Field>
        </div>
        <div className="form-section-label">
          <span>02</span>Supporting evidence
        </div>
        <p className="muted">
          Attach an applicable policy. Each quotation below must also link to an accessible source.
        </p>
        <div className="evidence-choices">
          {data.documents
            .filter((d) => d.status === 'ready' && d.category !== 'Quotation')
            .map((d) => (
              <label key={d.id}>
                <input
                  type="checkbox"
                  checked={docs.includes(d.id)}
                  onChange={(e) =>
                    setDocs(e.target.checked ? [...docs, d.id] : docs.filter((id) => id !== d.id))
                  }
                />
                <FileText size={15} />
                <span>{d.title}</span>
              </label>
            ))}
        </div>
        <div className="form-section-label">
          <span>03</span>Supplier quotations{' '}
          <button
            type="button"
            className="text-btn"
            onClick={() => setQuotes((q) => [...q, blankQuote()])}
          >
            <Plus size={14} />
            {t('Add quotation')}
          </button>
        </div>
        {!quotes.length && (
          <div className="quote-empty">
            <FileText size={22} />
            <p>Start with a draft, or add two quotations for a complete comparison.</p>
            <button
              type="button"
              className="btn small"
              onClick={() => setQuotes([blankQuote(), blankQuote()])}
            >
              <Plus size={14} />
              Add two quotations
            </button>
          </div>
        )}
        <QuoteEditor quotes={quotes} setQuotes={setQuotes} documents={data.documents} />
        {error && (
          <div className="form-error" role="alert">
            {error}
          </div>
        )}
        <div className="modal-actions">
          <span className="muted">
            <ShieldCheck size={13} />
            Saved as draft · no external action
          </span>
          <button className="btn" type="button" onClick={onClose}>
            {t('Cancel')}
          </button>
          <button className="btn primary" disabled={busy}>
            {busy ? 'Creating…' : t('Create case')}
            <ArrowRight size={16} />
          </button>
        </div>
      </form>
    </Modal>
  )
}

function QuoteEditor({
  quotes,
  setQuotes,
  documents,
}: {
  quotes: Quote[]
  setQuotes: (q: Quote[]) => void
  documents: Evidence[]
}) {
  const { t, locale } = useI18n()
  const [draft, setDraft] = useState<{ index: number; result: QuotationDraft } | null>(null)
  const [extracting, setExtracting] = useState<number | null>(null)
  const [extractError, setExtractError] = useState('')
  const [reviewed, setReviewed] = useState(false)
  const [reviewValues, setReviewValues] = useState<Record<string, string>>({})
  const [reviewReason, setReviewReason] = useState('')
  const [savingReview, setSavingReview] = useState(false)
  async function extract(index: number) {
    const document = documents.find((d) => d.id === quotes[index]?.document_id)
    if (!document) return
    setExtracting(index)
    setExtractError('')
    setReviewed(false)
    try {
      const result = await api<QuotationDraft>(`/api/v1/documents/${document.id}/quotation-draft`, {
        method: 'POST',
        body: JSON.stringify({ expected_version: document.version }),
      })
      setDraft({ index, result })
      setReviewValues(
        Object.fromEntries(Object.entries(result.fields).map(([k, f]) => [k, f.value ?? ''])),
      )
      setReviewReason('')
    } catch (e) {
      setExtractError((e as Error).message)
    } finally {
      setExtracting(null)
    }
  }
  async function applyDraft() {
    if (!draft || !reviewed) return
    const { index, result } = draft
    const q = quotes[index]
    const document = documents.find((d) => d.id === result.source.document_id)
    if (
      !q ||
      q.document_id !== result.source.document_id ||
      document?.version !== result.source.version
    ) {
      setDraft(null)
      setExtractError('The quotation or source changed. Extract and review again.')
      return
    }
    setSavingReview(true)
    try {
      const review = await api<{ id: string; values: Record<string, string | null> }>(
        `/api/v1/extractions/${result.extraction_id}/reviews`,
        {
          method: 'POST',
          body: JSON.stringify({
            values: Object.fromEntries(
              Object.entries(reviewValues).map(([k, v]) => [k, v === '' ? null : v]),
            ),
            reason: reviewReason,
          }),
        },
      )
      const value = (key: string) => review.values[key] ?? ''
      const next: Quote = {
        ...q,
        review_id: review.id,
        source_version: result.source.version,
        supplier: value('supplier'),
        amount: value('amount'),
        currency: value('currency'),
        tax_percent: value('tax_percent'),
        delivery_days: value('delivery_days') === '' ? '' : Number(value('delivery_days')),
        valid_until: value('valid_until'),
      }
      setQuotes(quotes.map((item, i) => (i === index ? next : item)))
      setDraft(null)
    } catch (e) {
      setExtractError((e as Error).message)
    } finally {
      setSavingReview(false)
    }
  }
  const labels: Record<string, string> = {
    supplier: t('Supplier'),
    amount: t('Net amount'),
    currency: t('Currency'),
    tax_percent: t('Tax percentage'),
    delivery_days: t('Delivery days'),
    valid_until: t('Valid until'),
  }
  function change(index: number, key: string, value: string | number) {
    setQuotes(
      quotes.map((q, i) =>
        i === index ? { ...q, [key]: value, review_id: undefined, source_version: undefined } : q,
      ),
    )
  }
  return (
    <div className="quote-editor">
      {quotes.map((q, i) => (
        <section className="quote-form" key={i}>
          <div className="quote-form-head">
            <span>Quotation {i + 1}</span>
            <button
              className="icon-btn danger-text"
              type="button"
              aria-label={`Remove quotation ${i + 1}`}
              onClick={() => setQuotes(quotes.filter((_, j) => j !== i))}
            >
              <Trash2 size={15} />
            </button>
          </div>
          <div className="form-grid">
            <Field label="Supplier">
              <input
                required
                minLength={2}
                maxLength={120}
                value={q.supplier}
                onChange={(e) => change(i, 'supplier', e.target.value)}
                placeholder="Supplier name"
              />
            </Field>
            <Field label="Net amount">
              <input
                type="number"
                min="0.01"
                max="100000000"
                step="0.01"
                required
                value={q.amount}
                onChange={(e) => change(i, 'amount', e.target.value)}
                placeholder="0.00"
              />
            </Field>
            <Field label="Currency">
              <select
                required
                value={q.currency}
                onChange={(e) => change(i, 'currency', e.target.value)}
              >
                <option value="">{t('Select currency')}</option>
                <option>AED</option>
                <option>USD</option>
                <option>EUR</option>
              </select>
            </Field>
            <Field label="Tax percentage">
              <input
                required
                type="number"
                min="0"
                max="100"
                step="0.01"
                value={q.tax_percent}
                onChange={(e) => change(i, 'tax_percent', e.target.value)}
              />
            </Field>
            <Field label="Delivery days">
              <input
                required
                type="number"
                min="0"
                max="730"
                value={q.delivery_days}
                onChange={(e) =>
                  change(i, 'delivery_days', e.target.value === '' ? '' : Number(e.target.value))
                }
              />
            </Field>
            <Field label="Valid until">
              <input
                required
                type="date"
                value={q.valid_until}
                onChange={(e) => change(i, 'valid_until', e.target.value)}
              />
            </Field>
          </div>
          <Field label="Source document">
            <select
              required
              value={q.document_id}
              onChange={(e) => change(i, 'document_id', e.target.value)}
            >
              <option value="">Select source evidence…</option>
              {documents
                .filter((d) => d.status === 'ready')
                .map((d) => (
                  <option key={d.id} value={d.id}>
                    {d.title}
                  </option>
                ))}
            </select>
          </Field>
          <div className="extraction-actions">
            <button
              type="button"
              className="btn small"
              disabled={!q.document_id || extracting !== null}
              onClick={() => extract(i)}
            >
              <FileText size={15} />
              {extracting === i ? t('Reading source…') : t('Extract from source')}
            </button>
            <span>
              {locale === 'ar'
                ? 'حقول نصية معنونة فقط. راجع القيم قبل استخدامها.'
                : 'Labelled text only. Review values before applying.'}
            </span>
          </div>
        </section>
      ))}
      {extractError && (
        <div className="form-error" role="alert">
          {extractError}
        </div>
      )}
      {draft && (
        <Modal title={t('Review extracted quotation')} wide onClose={() => setDraft(null)}>
          <div className="callout">
            <Info size={19} />
            <p>
              {locale === 'ar'
                ? 'مسودة فقط. تحقق من كل قيمة. القيم المفقودة أو المتعارضة تبقى فارغة ويجب إدخالها يدوياً. لا يتم حفظ الطلب أو تشغيل المقارنة هنا.'
                : 'Draft only. Verify every value. Missing or conflicting fields remain blank for manual entry. Applying this draft does not save the case or run a comparison.'}
            </p>
          </div>
          <p className="extraction-source">
            <strong>{draft.result.source.title}</strong> · {t('Version')}{' '}
            {draft.result.source.version}
            <br />
            <code>SHA-256: {draft.result.source.sha256}</code>
          </p>
          <div className="table-scroll">
            <table className="data-table extraction-table">
              <thead>
                <tr>
                  <th>{t('Field')}</th>
                  <th>{t('Draft value')}</th>
                  <th>{t('Source passage')}</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(draft.result.fields).map(([key, field]) => (
                  <tr key={key}>
                    <td>
                      {labels[key] || key}
                      <small className="extraction-state">{t(field.status)}</small>
                    </td>
                    <td>
                      <input
                        aria-label={`${t('Reviewed')} ${labels[key] || key}`}
                        value={reviewValues[key] ?? ''}
                        onChange={(e) =>
                          setReviewValues({ ...reviewValues, [key]: e.target.value })
                        }
                        type={key === 'valid_until' ? 'date' : 'text'}
                        placeholder={t('Manual entry required')}
                      />
                    </td>
                    <td>
                      {field.evidence.length ? (
                        field.evidence.map((e, i) => (
                          <blockquote key={i}>
                            <span>
                              {t('Page')} {e.page}
                            </span>
                            <p dir="auto">{e.excerpt}</p>
                          </blockquote>
                        ))
                      ) : (
                        <span>{t('No labelled value found')}</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <Field label="Correction / review reason">
            <textarea
              value={reviewReason}
              onChange={(e) => setReviewReason(e.target.value)}
              minLength={5}
              maxLength={2000}
              rows={2}
              placeholder="Explain the corrections or confirm that the source values were checked."
            />
          </Field>
          {extractError && (
            <div className="form-error" role="alert">
              {extractError}
            </div>
          )}
          <label className="extraction-confirm">
            <input
              type="checkbox"
              checked={reviewed}
              onChange={(e) => setReviewed(e.target.checked)}
            />
            {t('I reviewed these values against the source.')}
          </label>
          <div className="modal-actions">
            <button type="button" className="btn" onClick={() => setDraft(null)}>
              {t('Cancel')}
            </button>
            <button
              type="button"
              className="btn primary"
              disabled={!reviewed || reviewReason.trim().length < 5 || savingReview}
              onClick={applyDraft}
            >
              {t('Apply reviewed draft')}
            </button>
          </div>
        </Modal>
      )}
    </div>
  )
}

export function CaseDetail({ id, onClose }: { id: string; onClose: () => void }) {
  const { data, user, refresh, notify, openDocument } = useWorkspace(),
    { t, locale } = useI18n()
  const [tab, setTab] = useState('overview'),
    [busy, setBusy] = useState(false),
    [editing, setEditing] = useState(false),
    [quotes, setQuotes] = useState<Quote[]>([]),
    [docs, setDocs] = useState<string[]>([]),
    [reason, setReason] = useState(''),
    [error, setError] = useState(''),
    [confirm, setConfirm] = useState('')
  const c = data.cases.find((c) => c.id === id),
    run = data.runs.find((r) => r.case_id === id)
  useEffect(() => {
    setTab('overview')
    setEditing(false)
    setReason('')
    setConfirm('')
    setError('')
  }, [id])
  if (!c)
    return (
      <Modal title="Case unavailable" onClose={onClose}>
        <Empty title="Case not found" text="Refresh the workspace or choose another case." />
      </Modal>
    )
  const canEdit = ['analyst', 'admin'].includes(user.role),
    locked = ['approved_simulation', 'rejected', 'cancelled', 'processing'].includes(c.status),
    canReview =
      ['reviewer', 'admin'].includes(user.role) && c.status === 'awaiting_review' && !!c.approval
  async function execute() {
    if (!c) return
    setBusy(true)
    setError('')
    try {
      await api(`/api/v1/cases/${c.id}/runs`, {
        method: 'POST',
        headers: { 'Idempotency-Key': crypto.randomUUID() },
      })
      await refresh()
      setTab('comparison')
      notify('Comparison completed. Review findings and the next step.')
    } catch (e) {
      setError((e as Error).message)
      await refresh().catch(() => {})
    } finally {
      setBusy(false)
    }
  }
  async function decide(decision: string) {
    if (!c?.approval) return
    setBusy(true)
    setError('')
    try {
      await api(`/api/v1/approvals/${c.approval.id}/decisions`, {
        method: 'POST',
        body: JSON.stringify({ decision, reason, expected_revision: c.revision }),
      })
      await refresh()
      setConfirm('')
      setReason('')
      notify('Your review decision has been recorded.')
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setBusy(false)
    }
  }
  async function save(e: FormEvent) {
    e.preventDefault()
    if (!c) return
    setBusy(true)
    setError('')
    try {
      await api(`/api/v1/cases/${c.id}`, {
        method: 'PATCH',
        body: JSON.stringify({
          expected_revision: c.revision,
          quotes,
          document_ids: [...new Set([...docs, ...quotes.map((q) => q.document_id)])],
        }),
      })
      await refresh()
      setEditing(false)
      notify('Evidence revised. Previous pending approval was invalidated.')
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setBusy(false)
    }
  }
  const compared = c.comparison.quotes || c.quotes
  return (
    <Modal title={editing ? 'Revise case evidence' : t('Review workspace')} wide onClose={onClose}>
      <div className="case-detail-heading">
        <div>
          <span className="reference-label">
            {c.reference}
            <span>REVISION {c.revision}</span>
          </span>
          <h2>{c.title}</h2>
          <p>{c.description}</p>
        </div>
        <Badge status={c.status} />
      </div>
      <div className="case-facts">
        {[
          ['Budget', money(c.budget, c.currency)],
          ['Department', c.department],
          ['Due date', humanDate(c.due_date, locale)],
          ['Priority', c.priority],
        ].map(([label, value]) => (
          <div key={label}>
            <span>{t(label)}</span>
            <strong>{value}</strong>
          </div>
        ))}
      </div>
      {editing ? (
        <form onSubmit={save}>
          <div className="callout warning">
            <Info size={20} />
            <p>
              Saving a revision resets this case to draft and invalidates its pending approval. A
              fresh comparison and independent review will be required.
            </p>
          </div>
          <div className="form-section-label">Attached sources</div>
          <div className="evidence-choices">
            {data.documents
              .filter((d) => d.status === 'ready')
              .map((d) => (
                <label key={d.id}>
                  <input
                    type="checkbox"
                    checked={docs.includes(d.id)}
                    onChange={(e) =>
                      setDocs(e.target.checked ? [...docs, d.id] : docs.filter((x) => x !== d.id))
                    }
                  />
                  <FileText size={15} />
                  <span>{d.title}</span>
                </label>
              ))}
          </div>
          <div className="form-section-label">
            Quotations
            <button
              type="button"
              className="text-btn"
              onClick={() => setQuotes((q) => [...q, blankQuote()])}
            >
              <Plus size={14} />
              {t('Add quotation')}
            </button>
          </div>
          <QuoteEditor quotes={quotes} setQuotes={setQuotes} documents={data.documents} />
          {error && (
            <div className="form-error" role="alert">
              {error}
            </div>
          )}
          <div className="modal-actions">
            <button type="button" className="btn" onClick={() => setEditing(false)}>
              {t('Cancel')}
            </button>
            <button className="btn primary" disabled={busy}>
              {busy ? 'Saving…' : t('Save changes')}
            </button>
          </div>
        </form>
      ) : (
        <>
          <div className="detail-tabs tabs">
            {[
              ['overview', 'Overview'],
              ['comparison', 'Quotations'],
              ['evidence', 'Evidence'],
              ['workflow', 'Workflow'],
            ].map(([key, label]) => (
              <button className={tab === key ? 'active' : ''} key={key} onClick={() => setTab(key)}>
                {t(label)}
                {key === 'evidence' && <span>{c.document_ids.length}</span>}
              </button>
            ))}
          </div>
          {c.evidence_restricted && (
            <div className="callout warning">
              <LockKeyhole size={19} />
              <p>
                Some case evidence is restricted or withdrawn. Derived quotation values are hidden
                until you have access to all sources.
              </p>
            </div>
          )}
          {tab === 'overview' && (
            <div className="case-overview">
              <div
                className={`case-next-step ${c.status === 'approved_simulation' ? 'approved' : ''}`}
              >
                <span>
                  <UserCheck size={25} />
                </span>
                <div>
                  <h3>
                    {c.status === 'awaiting_review'
                      ? 'Ready for an independent perspective'
                      : c.status === 'approved_simulation'
                        ? 'Simulation approved'
                        : c.status === 'needs_information'
                          ? 'A little more evidence is needed'
                          : c.status === 'rejected'
                            ? 'Review complete · not approved'
                            : 'Build a decision on solid evidence'}
                  </h3>
                  <p>
                    {c.status === 'awaiting_review'
                      ? 'The comparison is prepared. A permitted reviewer can inspect the source-linked amounts and record a decision.'
                      : c.status === 'approved_simulation'
                        ? 'An independent review was recorded. No actual procurement award or payment has been made.'
                        : 'Inspect source documents, confirm the quotation fields, and run the deterministic comparison.'}
                  </p>
                </div>
              </div>
              <div className="two-col case-summary">
                <section>
                  <h3>Evidence at a glance</h3>
                  <div className="model-row">
                    <span>Attached source documents</span>
                    <strong>{c.document_ids.length}</strong>
                  </div>
                  <div className="model-row">
                    <span>Supplier quotations</span>
                    <strong>{c.quotes.length}</strong>
                  </div>
                  <div className="model-row">
                    <span>Calculation rules</span>
                    <strong>Decimal · versioned checklist</strong>
                  </div>
                </section>
                <section>
                  <h3>Review safeguards</h3>
                  <div className="safeguard">
                    <CheckCircle2 size={16} />
                    Current revision must match
                  </div>
                  <div className="safeguard">
                    <CheckCircle2 size={16} />
                    Evidence versions are bound
                  </div>
                  <div className="safeguard">
                    <CheckCircle2 size={16} />
                    Independent human decision
                  </div>
                  <div className="safeguard">
                    <CheckCircle2 size={16} />
                    Outcome is a simulation
                  </div>
                </section>
              </div>
            </div>
          )}
          {tab === 'comparison' && (
            <div className="comparison-content">
              <div className="comparison-intro">
                <h3>{t('Evidence-linked comparison')}</h3>
                <p>
                  Quotation fields are supplied by the analyst and must be checked against original
                  evidence. Totals are calculated on the server.
                </p>
              </div>
              {compared.length ? (
                <div className="table-scroll">
                  <table className="data-table comparison-table">
                    <thead>
                      <tr>
                        <th>{t('Supplier')}</th>
                        <th>{t('Net amount')}</th>
                        <th>{t('Tax')}</th>
                        <th>{t('Total')}</th>
                        <th>{t('Delivery')}</th>
                        <th>{t('Evidence')}</th>
                      </tr>
                    </thead>
                    <tbody>
                      {compared.map((q, i) => (
                        <tr key={i}>
                          <td>
                            <strong>{q.supplier}</strong>
                            <small className="time-sub">Valid to {q.valid_until}</small>
                          </td>
                          <td className="amount">{money(q.amount, q.currency)}</td>
                          <td>{q.tax ? money(q.tax, q.currency) : `${q.tax_percent}%`}</td>
                          <td className="amount">
                            {q.total ? money(q.total, q.currency) : 'Run comparison'}
                          </td>
                          <td>
                            {q.delivery_days} {t('days')}
                          </td>
                          <td>
                            <button
                              className="text-btn"
                              onClick={() =>
                                openDocument(q.document_id, c.evidence_versions[q.document_id])
                              }
                            >
                              <FileText size={14} />
                              Source
                              <ArrowUpRight size={12} />
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <Empty
                  title="No quotations attached"
                  text="Add two source-linked quotations using Edit evidence."
                />
              )}
              {c.comparison.calculation && (
                <div className="inline-note">
                  <Info size={16} />
                  {c.comparison.calculation}
                </div>
              )}
            </div>
          )}
          {tab === 'evidence' && (
            <div className="attached-evidence">
              {c.document_ids.map((docId) => {
                const d = data.documents.find((d) => d.id === docId)
                return (
                  <button
                    disabled={!d}
                    key={docId}
                    onClick={() => openDocument(docId, c.evidence_versions[docId])}
                  >
                    <span className="document-glyph">
                      <FileText size={20} />
                    </span>
                    <span>
                      <strong>{d?.title || 'Source unavailable or access restricted'}</strong>
                      <small>
                        {d
                          ? `${d.category} · v${d.version} · ${d.classification}`
                          : 'Review requires current accessible evidence.'}
                      </small>
                    </span>
                    {d && (
                      <>
                        <Badge status={d.status} />
                        <ArrowUpRight size={16} />
                      </>
                    )}
                  </button>
                )
              })}
              {!c.document_ids.length && (
                <Empty
                  title="No evidence attached"
                  text="Attach permitted source documents before requesting review."
                />
              )}
            </div>
          )}
          {tab === 'workflow' && (
            <div className="run-steps">
              {run?.steps.length ? (
                run.steps.map((s, i) => (
                  <div key={i}>
                    <span className="step-check">
                      <Check size={16} />
                    </span>
                    <section>
                      <strong>{s.name}</strong>
                      <p>{s.detail}</p>
                    </section>
                    <Badge status="ready">Completed</Badge>
                  </div>
                ))
              ) : (
                <Empty
                  title="No recorded run yet"
                  text="Run comparison to create the case's validation history."
                />
              )}
              {run && (
                <div>
                  <span className="step-check pending">
                    <UserCheck size={17} />
                  </span>
                  <section>
                    <strong>Independent review</strong>
                    <p>Current case state: {c.status.replaceAll('_', ' ')}</p>
                  </section>
                  <Badge status={c.status} />
                </div>
              )}
            </div>
          )}
          {!!c.comparison.issues?.length && (
            <div className="findings">
              <h3>
                <Info size={17} />
                Items to resolve
              </h3>
              <ul>
                {c.comparison.issues.map((issue, i) => (
                  <li key={i}>{issue}</li>
                ))}
              </ul>
            </div>
          )}
          {canReview && (
            <section className="review-decision">
              <div className="section-label">
                <UserCheck size={20} />
                <div>
                  <h3>{t('Review decision')}</h3>
                  <p>
                    You are reviewing revision {c.revision}. Verify the evidence before deciding.
                  </p>
                </div>
              </div>
              <Field label="Decision reason">
                <textarea
                  minLength={5}
                  maxLength={2000}
                  value={reason}
                  onChange={(e) => setReason(e.target.value)}
                  rows={3}
                  placeholder="Record your reasoning for the audit trail…"
                />
              </Field>
              {confirm ? (
                <div className="decision-confirm">
                  <strong>
                    {confirm === 'approve'
                      ? 'Record an approved simulation?'
                      : confirm === 'reject'
                        ? 'Reject this case?'
                        : 'Request additional information?'}
                  </strong>
                  <p>Your decision and reason will be saved against this evidence snapshot.</p>
                  <div>
                    <button className="btn small" onClick={() => setConfirm('')}>
                      {t('Cancel')}
                    </button>
                    <button
                      className={`btn small ${confirm === 'approve' ? 'primary' : 'danger'}`}
                      disabled={busy}
                      onClick={() => decide(confirm)}
                    >
                      {busy ? 'Recording…' : 'Confirm decision'}
                    </button>
                  </div>
                </div>
              ) : (
                <div className="decision-actions">
                  <button
                    className="btn primary"
                    disabled={reason.trim().length < 5 || busy}
                    onClick={() => setConfirm('approve')}
                  >
                    <Check size={16} />
                    {t('Approve simulation')}
                  </button>
                  <button
                    className="btn"
                    disabled={reason.trim().length < 5 || busy}
                    onClick={() => setConfirm('request_changes')}
                  >
                    {t('Request changes')}
                  </button>
                  <button
                    className="btn danger-text"
                    disabled={reason.trim().length < 5 || busy}
                    onClick={() => setConfirm('reject')}
                  >
                    {t('Reject')}
                  </button>
                </div>
              )}
            </section>
          )}
          {c.status === 'awaiting_review' && !canReview && (
            <div className="callout">
              <UserCheck size={19} />
              <p>
                This case is waiting for an independent reviewer. Sign in with the reviewer demo
                identity to inspect and record a decision.
              </p>
            </div>
          )}
          {error && (
            <div className="form-error" role="alert">
              {error}
            </div>
          )}
          <div className="modal-actions case-actions">
            <a className="btn small" href={`/api/v1/report/${c.id}`} download>
              <ArrowDownToLine size={15} />
              {t('Export report')}
            </a>
            <a
              className="btn small"
              href={`/api/v1/report/${c.id}/print`}
              target="_blank"
              rel="noopener noreferrer"
            >
              <Printer size={15} />
              {t('Print / Save PDF')}
            </a>
            <span className="action-spacer" />
            {canEdit && !locked && (
              <button
                className="btn small"
                onClick={() => {
                  setQuotes(c.quotes.map((q) => ({ ...q })))
                  setDocs([...c.document_ids])
                  setEditing(true)
                }}
              >
                {t('Edit evidence')}
              </button>
            )}
            {canEdit && ['draft', 'needs_information', 'failed'].includes(c.status) && (
              <button className="btn primary" disabled={busy} onClick={execute}>
                {busy ? <LoaderCircle size={16} className="spin" /> : <Workflow size={16} />}
                {busy ? 'Running…' : t('Run comparison')}
              </button>
            )}
          </div>
        </>
      )}
    </Modal>
  )
}

export function DocumentDetail({
  id,
  onClose,
  initialVersion,
}: {
  id: string
  onClose: () => void
  initialVersion?: number
}) {
  const { user, refresh, notify } = useWorkspace(),
    { t, locale } = useI18n()
  const [doc, setDoc] = useState<Evidence | null>(null),
    [error, setError] = useState(''),
    [confirm, setConfirm] = useState(false),
    [busy, setBusy] = useState(false)
  const [latest, setLatest] = useState<Evidence | null>(null)
  const [versions, setVersions] = useState<SourceVersion[]>([])
  const [history, setHistory] = useState<ExtractionHistory[]>([])
  const [versionFile, setVersionFile] = useState<File | null>(null)
  const [historyTab, setHistoryTab] = useState(false)
  const selectedVersion = useRef<number | undefined>(initialVersion)
  const historyRequest = useRef(0)
  async function loadHistory() {
    const request = ++historyRequest.current
    const selected = selectedVersion.current
    const [current, all, extractions, historical] = await Promise.all([
      api<Evidence>(`/api/v1/documents/${id}`),
      api<SourceVersion[]>(`/api/v1/documents/${id}/versions`),
      api<ExtractionHistory[]>(`/api/v1/documents/${id}/extractions`),
      selected
        ? api<Evidence>(`/api/v1/documents/${id}/versions/${selected}`)
        : Promise.resolve(null),
    ])
    if (request !== historyRequest.current || selected !== selectedVersion.current) return
    setDoc(historical ?? current)
    setLatest(current)
    setVersions(all)
    setHistory(extractions)
  }
  async function chooseVersion(number: string) {
    try {
      selectedVersion.current = Number(number)
      setError('')
      await loadHistory()
    } catch (e) {
      setError((e as Error).message)
    }
  }
  async function uploadVersion(e: FormEvent) {
    e.preventDefault()
    if (!latest || !versionFile) return
    setBusy(true)
    setError('')
    const form = new FormData()
    form.append('file', versionFile)
    form.append('expected_version', String(latest.version))
    try {
      await api(`/api/v1/documents/${id}/versions`, { method: 'POST', body: form })
      setVersionFile(null)
      await refresh()
      selectedVersion.current = undefined
      await loadHistory()
      notify('New source version uploaded. Affected pending approvals require a new comparison.')
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setBusy(false)
    }
  }
  useEffect(() => {
    if (!latest || !['queued', 'processing'].includes(latest.status)) return
    const timer = setInterval(() => loadHistory().catch((e) => setError(e.message)), 2000)
    return () => clearInterval(timer)
  }, [id, latest?.status])
  useEffect(() => {
    setDoc(null)
    setError('')
    selectedVersion.current = initialVersion
    loadHistory().catch((e) => setError(e.message))
    return () => {
      historyRequest.current += 1
    }
  }, [id, initialVersion])
  async function remove() {
    setBusy(true)
    try {
      await api(`/api/v1/documents/${id}`, { method: 'DELETE' })
      await refresh()
      notify(
        'Document withdrawn. Live retrieval access was removed and affected pending reviews were invalidated.',
      )
      onClose()
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setBusy(false)
    }
  }
  async function retry() {
    setBusy(true)
    try {
      await api(`/api/v1/documents/${id}/retry`, { method: 'POST' })
      await refresh()
      notify('Document queued for another processing attempt.')
      onClose()
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setBusy(false)
    }
  }
  return (
    <Modal title={t('Source document')} wide onClose={onClose}>
      {error && (
        <div className="form-error" role="alert">
          {error}
        </div>
      )}
      {!doc && !error ? (
        <div className="modal-loading">
          <LoaderCircle className="spin" />
          Loading source evidence…
        </div>
      ) : (
        doc && (
          <>
            <div className="document-detail-heading">
              <span className="document-glyph">
                <FileText size={27} />
              </span>
              <div>
                <h2>{doc.title}</h2>
                <p>
                  {doc.source} · {doc.language === 'ar' ? 'Arabic' : 'English'} · Version{' '}
                  {doc.version}
                </p>
              </div>
              <Badge status={doc.status} />
            </div>
            <div className="document-meta-line">
              <span>
                <LockKeyhole size={13} />
                {doc.classification}
              </span>
              <span>{doc.page_count} pages</span>
              <span>{(doc.size / 1024).toFixed(1)} KB</span>
              <span>{doc.category}</span>
            </div>
            <div className="version-toolbar">
              <label>
                {t('Source version')}
                <select
                  aria-label="Source version"
                  value={doc.version}
                  onChange={(e) => chooseVersion(e.target.value)}
                >
                  {versions.map((v) => (
                    <option key={v.id} value={v.version}>
                      v{v.version} · {v.filename} · {v.status}
                    </option>
                  ))}
                </select>
              </label>
              <button className="btn small" onClick={() => setHistoryTab(!historyTab)}>
                {historyTab ? t('Read source') : t('Extraction history')}
              </button>
            </div>
            {latest && doc.version !== latest.version && (
              <div className="callout">
                <Info size={18} />
                <p>
                  {t(
                    'You are viewing historical evidence. New comparisons use the current source version.',
                  )}
                </p>
              </div>
            )}
            {['analyst', 'admin'].includes(user.role) &&
              latest &&
              !['queued', 'processing'].includes(latest.status) && (
                <form className="version-upload" onSubmit={uploadVersion}>
                  <label>
                    {t('Add a new version')}
                    <input
                      type="file"
                      accept=".pdf,.txt"
                      aria-label="New version file"
                      onChange={(e) => setVersionFile(e.target.files?.[0] ?? null)}
                    />
                  </label>
                  <button className="btn small" disabled={!versionFile || busy}>
                    {t('Upload new version')}
                  </button>
                  <small>
                    {t('Previous versions are retained. Pending reviews will be invalidated.')}
                  </small>
                </form>
              )}
            {historyTab && (
              <section className="version-history">
                <h3>{t('Extraction and correction history')}</h3>
                {!history.length && (
                  <Empty
                    title="No saved extractions yet"
                    text="Extract a quotation from this source to create its first history record."
                  />
                )}
                {history.map((e) => (
                  <article key={e.id}>
                    <strong>
                      v{e.payload.source?.version} · {e.extractor_version}
                    </strong>
                    <p>
                      {humanDate(e.created_at, locale)} · {e.reviews.length} {t('reviews')}
                    </p>
                    {e.reviews.map((r) => (
                      <div className="review-history" key={r.id}>
                        <strong>{r.reason}</strong>
                        <small>
                          {r.actor_name || r.actor_id} · {humanDate(r.created_at, locale)}
                        </small>
                        {Object.entries(r.changes).map(([key, change]) => (
                          <p key={key}>
                            <b>{key}</b>: <bdi>{change.before ?? '—'}</bdi> →{' '}
                            <bdi>{change.after ?? '—'}</bdi>
                          </p>
                        ))}
                        {!Object.keys(r.changes).length && (
                          <p>{t('Source values confirmed without corrections.')}</p>
                        )}
                      </div>
                    ))}
                  </article>
                ))}
              </section>
            )}
            <div className="source-pages" hidden={historyTab}>
              {doc.pages?.map((p) => (
                <section className="source-page" key={p.page}>
                  <div>
                    <FileText size={14} />
                    Page {p.page}
                    <span>
                      {p.method === 'ocr'
                        ? 'OCR text · verify against original'
                        : 'Original extracted text'}
                    </span>
                  </div>
                  {p.warnings?.map((warning, index) => (
                    <div className="source-warning" role="note" key={index}>
                      {warning}
                    </div>
                  ))}
                  <p dir="auto">{p.text || 'No text could be extracted from this page.'}</p>
                </section>
              ))}
              {!doc.pages?.length && (
                <Empty
                  title={
                    doc.status === 'needs_ocr'
                      ? 'This document needs OCR'
                      : 'No extracted text available'
                  }
                  text={
                    doc.status === 'needs_ocr'
                      ? 'Image-only PDFs need an OCR pipeline before they can be searched.'
                      : 'The document may still be processing, or its parser could not extract supported text.'
                  }
                />
              )}
            </div>
            {confirm && (
              <div className="withdraw-confirm">
                <strong>Withdraw this source?</strong>
                <p>
                  This removes active passages and file access. Pending approvals using this source
                  will be invalidated. Historical backup retention is governed separately.
                </p>
                <div>
                  <button className="btn small" onClick={() => setConfirm(false)}>
                    {t('Cancel')}
                  </button>
                  <button className="btn small danger" disabled={busy} onClick={remove}>
                    {busy ? 'Withdrawing…' : 'Confirm withdrawal'}
                  </button>
                </div>
              </div>
            )}
            <div className="modal-actions">
              <a
                className="btn"
                href={`/api/v1/documents/${id}/versions/${doc.version}/download`}
                download
              >
                <ArrowDownToLine size={16} />
                {t('Download source')}
              </a>
              <span className="action-spacer" />
              {['analyst', 'admin'].includes(user.role) && (
                <>
                  {['failed', 'needs_ocr'].includes(doc.status) && (
                    <button className="btn" disabled={busy} onClick={retry}>
                      {t('Retry processing')}
                    </button>
                  )}
                  <button className="btn danger-text" onClick={() => setConfirm(true)}>
                    <Trash2 size={15} />
                    {t('Withdraw document')}
                  </button>
                </>
              )}
            </div>
          </>
        )
      )}
    </Modal>
  )
}
