import { useEffect, useRef, useState } from 'react'
import type { FormEvent } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import {
  Activity,
  ArrowDownToLine,
  ArrowRight,
  ArrowUpRight,
  BarChart3,
  BookOpen,
  Bot,
  Check,
  CheckCheck,
  CheckCircle2,
  ChevronRight,
  Clock3,
  Cloud,
  Database,
  FileCheck2,
  FileText,
  Filter,
  FolderOpen,
  Globe2,
  Info,
  KeyRound,
  Layers3,
  ListChecks,
  LockKeyhole,
  MessageSquare,
  MoreHorizontal,
  Plus,
  RefreshCw,
  Search,
  Send,
  Settings2,
  Shield,
  ShieldCheck,
  ShoppingBag,
  Sparkles,
  Upload,
  UserCheck,
  Users,
  Workflow,
  X,
} from 'lucide-react'
import { api } from './api'
import { useWorkspace } from './context'
import { useI18n } from './i18n'
import { CapabilityRegister } from './capability-register'
import {
  Avatar,
  Badge,
  Empty,
  Field,
  humanDate,
  LinkButton,
  Modal,
  money,
  PageTitle,
  SectionHead,
  Select,
} from './ui'
import type { Answer, ProcurementCase, Ticket, WorkflowRun } from './types'

export function CaseTable({
  cases,
  compact = false,
}: {
  cases: ProcurementCase[]
  compact?: boolean
}) {
  const { openCase } = useWorkspace(),
    { t, locale } = useI18n()
  return (
    <div className="table-scroll">
      <table className={`data-table case-table ${compact ? 'compact' : ''}`}>
        <thead>
          <tr>
            <th>{t('Case')}</th>
            {!compact && <th>{t('Department')}</th>}
            <th>{t('Budget')}</th>
            <th>{t('Status')}</th>
            <th>{t('Due date')}</th>
            <th>
              <span className="sr-only">{t('Actions')}</span>
            </th>
          </tr>
        </thead>
        <tbody>
          {cases.map((c, i) => (
            <tr key={c.id}>
              <td>
                <button className="table-case" onClick={() => openCase(c.id)}>
                  <span className={`case-glyph tone-${i % 4}`}>
                    <ShoppingBag size={17} />
                  </span>
                  <span>
                    <strong>{c.title}</strong>
                    <small>
                      {c.reference}
                      {compact && ` · ${c.department}`}
                    </small>
                  </span>
                </button>
              </td>
              {!compact && (
                <td>
                  <span className="department">{c.department}</span>
                </td>
              )}
              <td className="amount" data-label={t('Budget')}>
                {money(c.budget, c.currency, true)}
              </td>
              <td data-label={t('Status')}>
                <Badge status={c.status} />
              </td>
              <td className="muted nowrap" data-label={t('Due date')}>
                {humanDate(c.due_date, locale, true)}
              </td>
              <td>
                <button
                  className="icon-btn"
                  aria-label={`View ${c.title}`}
                  onClick={() => openCase(c.id)}
                >
                  <ArrowUpRight size={17} />
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {!cases.length && <Empty />}
    </div>
  )
}

export function Dashboard({ onNewCase }: { onNewCase: () => void }) {
  const { data, user, openCase } = useWorkspace(),
    { t, locale } = useI18n(),
    navigate = useNavigate()
  const [days, setDays] = useState('7')
  const pending = data.cases.filter((c) => c.status === 'awaiting_review'),
    history = data.analytics.history.slice(-Number(days))
  const stats = [
    {
      title: 'Active cases',
      value: data.stats.active_cases,
      icon: ShoppingBag,
      note: 'Current procurement pipeline',
      path: '/procurement',
      tone: 'emerald',
    },
    {
      title: 'Pending reviews',
      value: data.stats.pending_reviews,
      icon: UserCheck,
      note: 'Ready for independent review',
      path: '/procurement?status=awaiting_review',
      tone: 'amber',
    },
    {
      title: 'Evidence documents',
      value: data.stats.documents,
      icon: FileCheck2,
      note: 'Permission-scoped source library',
      path: '/documents',
      tone: 'blue',
    },
    {
      title: 'Completed cases',
      value: data.stats.completed,
      icon: CheckCheck,
      note: 'Approved simulation outcomes',
      path: '/procurement?status=approved_simulation',
      tone: 'purple',
    },
  ]
  return (
    <>
      <PageTitle
        eyebrow="WORKSPACE OVERVIEW"
        title="Your operations, in focus."
        description={
          locale === 'ar'
            ? `مرحباً ${user.name.split(' ')[0]}، هذه نظرة على مساحة العمل.`
            : `Welcome back, ${user.name.split(' ')[0]}. Here’s what’s happening across your workspace.`
        }
        actions={
          <>
            <span className="date-label">
              {new Intl.DateTimeFormat(locale === 'ar' ? 'ar-AE' : 'en-GB', {
                day: 'numeric',
                month: 'long',
                year: 'numeric',
                timeZone: 'Asia/Dubai',
              }).format(new Date())}
            </span>
            {['analyst', 'requester', 'admin'].includes(user.role) && (
              <button className="btn primary" onClick={onNewCase}>
                <Plus size={17} />
                {t('New case')}
              </button>
            )}
          </>
        }
      />
      <section className="overview-banner">
        <div>
          <div className="banner-eyebrow">
            <span className="pulse-dot" />
            {locale === 'ar' ? 'الإمارات العربية المتحدة · ذكاء مسؤول' : 'UAE SOVEREIGN AGENTIC AI'}
          </div>
          <h2>
            {locale === 'ar'
              ? 'من المعلومات إلى قرارات واضحة.'
              : 'Intelligence, grounded in evidence.'}
          </h2>
          <p>
            {locale === 'ar'
              ? 'المستندات وسير العمل والمراجعات في مساحة عمل واحدة.'
              : 'One workspace for your evidence, procurement and decisions. Built around people.'}
          </p>
          <button onClick={() => navigate('/knowledge')}>
            {t('Ask assistant')}
            <ArrowRight size={15} />
          </button>
          <div
            className="hero-domains"
            aria-label={locale === 'ar' ? 'قدرات المنصة' : 'Platform capabilities'}
          >
            <span>{t('Procurement')}</span>
            <i />
            <span>{t('Knowledge assistant')}</span>
            <i />
            <span>{locale === 'ar' ? 'الحوكمة' : 'Governance'}</span>
          </div>
        </div>
        <div className="banner-art" aria-hidden="true">
          <img className="emirates-flag" src="/uae-flag-soft.svg" alt="" />
          <div className="art-grid" />
          <div className="art-sheet back">
            <span />
            <span />
            <span />
          </div>
          <div className="art-sheet front">
            <div className="art-stamp">
              <ShieldCheck size={28} />
            </div>
            <i />
            <i />
            <div className="art-check">
              <Check size={12} />
              Evidence verified
            </div>
          </div>
          <span className="art-orbit a" />
          <span className="art-orbit b" />
          <span className="art-star">✦</span>
        </div>
      </section>
      <section
        className="quick-actions"
        aria-label={locale === 'ar' ? 'إجراءات سريعة' : 'Quick actions'}
      >
        <div>
          <span className="eyebrow">{locale === 'ar' ? 'ابدأ من هنا' : 'YOUR WORKSPACE'}</span>
          <strong>{locale === 'ar' ? 'ماذا تريد أن تنجز؟' : 'What would you like to do?'}</strong>
        </div>
        <button onClick={() => navigate('/documents')}>
          <Upload size={19} />
          <span>{t('Evidence library')}</span>
          <ArrowUpRight size={16} />
        </button>
        <button onClick={() => navigate('/procurement?status=awaiting_review')}>
          <UserCheck size={19} />
          <span>{locale === 'ar' ? 'قائمة المراجعة' : 'Review queue'}</span>
          <ArrowUpRight size={16} />
        </button>
        <button onClick={() => navigate('/knowledge')}>
          <Sparkles size={19} />
          <span>{t('Ask assistant')}</span>
          <ArrowUpRight size={16} />
        </button>
      </section>
      <div className="stats-grid">
        {stats.map((s) => (
          <section className={`stat-card ${s.tone}`} key={s.title}>
            <div className="stat-top">
              <button className="stat-link" onClick={() => navigate(s.path)}>
                {t(s.title)} <ArrowUpRight size={15} />
              </button>
              <span className="stat-icon">
                <s.icon size={18} />
              </span>
            </div>
            <strong>{s.value.toString().padStart(2, '0')}</strong>
            <div className="stat-note">
              <span className="mini-line" />
              {s.note}
            </div>
          </section>
        ))}
      </div>
      <div className="dashboard-main-grid">
        <section className="panel cases-panel">
          <SectionHead
            title="Recent procurement"
            subtitle="From intake to an evidence-backed decision."
            action={
              <LinkButton onClick={() => navigate('/procurement')}>{t('View all')}</LinkButton>
            }
          />
          <CaseTable cases={data.cases.slice(0, 5)} compact />
          <div className="table-foot">
            <span>
              <span className="pulse-dot" />
              Live workspace records
            </span>
            <span>{data.cases.length} total cases</span>
          </div>
        </section>
        <section className="panel review-panel">
          <SectionHead
            title="Needs your attention"
            subtitle="A human perspective makes the difference."
            action={<span className="count-chip">{pending.length}</span>}
          />
          <div className="review-list">
            {pending.slice(0, 3).map((c, i) => (
              <div className="review-card" key={c.id}>
                <div className="review-top">
                  <span className="review-type">
                    <Clock3 size={13} />
                    {t('Independent review')}
                  </span>
                  <span className="muted">{i + 1}</span>
                </div>
                <h3>{c.title}</h3>
                <p>
                  {c.reference} <span>·</span> {c.department}
                </p>
                <div className="review-bottom">
                  <strong>{money(c.budget, c.currency, true)}</strong>
                  <button onClick={() => openCase(c.id)}>
                    {t('Review case')}
                    <ArrowRight size={14} />
                  </button>
                </div>
              </div>
            ))}
            {!pending.length && (
              <Empty title="No pending reviews" text="Everything is up to date." />
            )}
          </div>
          <div className="review-reminder">
            <ShieldCheck size={18} />
            <p>Approvals are bound to the current evidence version. You stay in control.</p>
          </div>
        </section>
      </div>
      <div className="dashboard-bottom-grid">
        <section className="panel chart-panel">
          <SectionHead
            title="Service workload"
            subtitle="Synthetic historical activity · not production traffic"
            action={
              <div className="segmented small">
                {['7', '28'].map((n) => (
                  <button
                    className={days === n ? 'selected' : ''}
                    onClick={() => setDays(n)}
                    key={n}
                  >
                    {n} days
                  </button>
                ))}
              </div>
            }
          />
          <div className="chart-legend">
            <span>
              <i className="legend-dot emerald" />
              Service requests
            </span>
            <span className="muted">
              {history.reduce((a, b) => a + b.volume, 0)} in selected period
            </span>
          </div>
          <div className="activity-chart">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={history} margin={{ top: 15, right: 12, left: -25, bottom: 0 }}>
                <defs>
                  <linearGradient id="activityFill" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#b49560" stopOpacity={0.2} />
                    <stop offset="100%" stopColor="#b49560" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid vertical={false} stroke="#edf0f1" strokeDasharray="4 4" />
                <XAxis
                  dataKey="label"
                  axisLine={false}
                  tickLine={false}
                  tick={{ fontSize: 10, fill: '#89929b' }}
                  minTickGap={32}
                />
                <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 10, fill: '#89929b' }} />
                <Tooltip
                  contentStyle={{ borderRadius: 12, border: '1px solid #e8ece9', fontSize: 12 }}
                />
                <Area
                  isAnimationActive={false}
                  type="monotone"
                  dataKey="volume"
                  name="Service requests"
                  stroke="#263f64"
                  fill="url(#activityFill)"
                  strokeWidth={2.2}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </section>
        <section className="panel activity-panel">
          <SectionHead
            title="Workspace activity"
            action={<LinkButton onClick={() => navigate('/audit')}>{t('View all')}</LinkButton>}
          />
          <div className="timeline-list">
            {data.events.slice(0, 4).map((e, i) => (
              <div className="timeline-item" key={e.id}>
                <span className={`timeline-icon tone-${i % 4}`}>
                  {e.action.includes('Session') ? (
                    <Users size={14} />
                  ) : e.action.includes('Review') ? (
                    <Check size={14} />
                  ) : (
                    <FileText size={14} />
                  )}
                </span>
                <div>
                  <strong>{e.action}</strong>
                  <p>{e.resource === 'workspace' ? e.actor : e.resource}</p>
                  <small>{humanDate(e.created_at, locale, true)}</small>
                </div>
              </div>
            ))}
          </div>
        </section>
      </div>
      <CapabilityRegister />
    </>
  )
}

export function Procurement({ onNewCase }: { onNewCase: () => void }) {
  const { data, user } = useWorkspace(),
    { t } = useI18n(),
    [params, setParams] = useSearchParams()
  const [search, setSearch] = useState(''),
    [sort, setSort] = useState('due'),
    [mine, setMine] = useState(false),
    status = params.get('status') || 'all'
  const filtered = data.cases
    .filter(
      (c) =>
        (status === 'all' || c.status === status) &&
        (!mine || c.created_by === user.id) &&
        (c.title + c.reference + c.department).toLowerCase().includes(search.toLowerCase()),
    )
    .sort((a, b) =>
      sort === 'budget'
        ? Number(b.budget) - Number(a.budget)
        : sort === 'recent'
          ? b.created_at.localeCompare(a.created_at)
          : a.due_date.localeCompare(b.due_date),
    )
  const tabs = [
    ['all', 'All cases'],
    ['awaiting_review', 'In review'],
    ['draft', 'Draft'],
    ['approved_simulation', 'Approved'],
    ['needs_information', 'Needs information'],
    ['rejected', 'Rejected'],
    ['cancelled', 'Cancelled'],
    ['failed', 'Failed'],
  ]
  return (
    <>
      <PageTitle
        eyebrow="OPERATIONS"
        title="Procurement"
        description="Every quotation, source and decision. A clear path from request to review."
        actions={
          ['analyst', 'requester', 'admin'].includes(user.role) && (
            <button className="btn primary" onClick={onNewCase}>
              <Plus size={17} />
              {t('New case')}
            </button>
          )
        }
      />
      <div className="summary-ribbon">
        <div>
          <span className="ribbon-icon">
            <ShoppingBag size={20} />
          </span>
          <span>
            <strong>{data.cases.length}</strong> procurement cases
          </span>
        </div>
        <span className="ribbon-separator" />
        <div>
          <span className="tiny-dot amber" />
          {data.stats.pending_reviews} awaiting review
        </div>
        <span className="ribbon-separator" />
        <div>
          <span className="tiny-dot emerald" />
          {data.stats.completed} approved simulations
        </div>
        <div className="ribbon-end">
          <ShieldCheck size={15} />
          {t('Human review required')}
        </div>
      </div>
      <section className="panel">
        <div className="list-toolbar">
          <div className="tabs">
            {tabs.map(([key, label]) => (
              <button
                className={status === key ? 'active' : ''}
                key={key}
                onClick={() => setParams(key === 'all' ? {} : { status: key })}
              >
                {t(label)}
                <span>{data.cases.filter((c) => key === 'all' || c.status === key).length}</span>
              </button>
            ))}
          </div>
          <div className="search-input">
            <Search size={16} />
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search cases…"
              aria-label="Search procurement cases"
            />
          </div>
        </div>
        <div className="filter-bar">
          <label className="check-filter">
            <input type="checkbox" checked={mine} onChange={(e) => setMine(e.target.checked)} />
            {t('My cases')}
          </label>
          <Select
            label="Sort cases"
            value={sort}
            onChange={setSort}
            options={[
              { value: 'due', label: t('Due date') },
              { value: 'recent', label: t('Newest first') },
              { value: 'budget', label: t('Highest budget') },
            ]}
          />
          <span role="status">
            {filtered.length} {t('cases')}
          </span>
        </div>
        <CaseTable cases={filtered} />
        <div className="table-foot">
          <span>
            Showing {filtered.length} of {data.cases.length} cases
          </span>
          <span>Synthetic procurement workspace</span>
        </div>
      </section>
      <div className="inline-note">
        <Info size={15} />
        <span>
          All outcomes in this workspace are simulated. Evidence changes require a new independent
          review.
        </span>
      </div>
    </>
  )
}

export function Documents() {
  const { data, user, openDocument } = useWorkspace(),
    { t } = useI18n()
  const [search, setSearch] = useState(''),
    [category, setCategory] = useState('all'),
    [processing, setProcessing] = useState('all'),
    [upload, setUpload] = useState(false)
  const docs = data.documents.filter(
    (d) =>
      (category === 'all' || d.category === category) &&
      (processing === 'all' || d.status === processing) &&
      (d.title + d.category).toLowerCase().includes(search.toLowerCase()),
  )
  const categories = ['all', 'Policy', 'Procurement', 'Quotation', 'HR', 'Service desk']
  return (
    <>
      <PageTitle
        eyebrow="TRUSTED KNOWLEDGE"
        title="Evidence library"
        description="One source of context. Versioned, permission-scoped and ready to inspect."
        actions={
          ['analyst', 'admin'].includes(user.role) && (
            <button className="btn primary" onClick={() => setUpload(true)}>
              <Upload size={16} />
              {t('Upload document')}
            </button>
          )
        }
      />
      <div className="document-stat-row">
        <div>
          <span className="doc-stat-icon">
            <FolderOpen size={21} />
          </span>
          <strong>{data.documents.length}</strong>
          <span>source documents</span>
        </div>
        <div>
          <span className="doc-stat-icon green">
            <FileCheck2 size={21} />
          </span>
          <strong>{data.documents.filter((d) => d.status === 'ready').length}</strong>
          <span>ready for retrieval</span>
        </div>
        <div>
          <span className="doc-stat-icon purple">
            <Globe2 size={21} />
          </span>
          <strong>{data.documents.filter((d) => d.language === 'ar').length}</strong>
          <span>Arabic sources</span>
        </div>
        <div className="doc-stat-note">
          <ShieldCheck size={22} />
          <p>
            Evidence stays within
            <br />
            your permitted workspace.
          </p>
        </div>
      </div>
      <section className="panel">
        <div className="list-toolbar">
          <div className="search-input wide">
            <Search size={16} />
            <input
              placeholder="Search the evidence library…"
              aria-label="Search documents"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
          <Select
            label="Document category"
            value={category}
            onChange={setCategory}
            options={categories.map((c) => ({
              value: c,
              label: c === 'all' ? t('All documents') : c,
            }))}
          />
          <Select
            label="Processing status"
            value={processing}
            onChange={setProcessing}
            options={['all', 'ready', 'queued', 'processing', 'failed', 'needs_ocr'].map(
              (value) => ({
                value,
                label: t(
                  value === 'all'
                    ? 'All statuses'
                    : value === 'needs_ocr'
                      ? 'Needs OCR'
                      : value.charAt(0).toUpperCase() + value.slice(1),
                ),
              }),
            )}
          />
        </div>
        <div className="table-scroll">
          <table className="data-table">
            <thead>
              <tr>
                <th>{t('Name')}</th>
                <th>{t('Category')}</th>
                <th>{t('Classification')}</th>
                <th>{t('Status')}</th>
                <th>Version</th>
                <th>Size</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {docs.map((d) => (
                <tr key={d.id}>
                  <td>
                    <button className="table-case" onClick={() => openDocument(d.id)}>
                      <span
                        className={`document-glyph ${d.category === 'Quotation' ? 'quote' : ''}`}
                      >
                        <FileText size={19} />
                      </span>
                      <span>
                        <strong>{d.title}</strong>
                        <small>
                          {d.language === 'ar' ? 'Arabic' : 'English'} · {d.page_count} page
                          {d.page_count !== 1 ? 's' : ''}
                        </small>
                      </span>
                    </button>
                  </td>
                  <td>
                    <span className="category-tag">{d.category}</span>
                  </td>
                  <td>
                    <span className="classification">
                      <LockKeyhole size={12} />
                      {d.classification}
                    </span>
                  </td>
                  <td>
                    <Badge status={d.status} />
                  </td>
                  <td className="muted">v{d.version}.0</td>
                  <td className="muted nowrap">{(d.size / 1024).toFixed(1)} KB</td>
                  <td>
                    <button
                      className="icon-btn"
                      aria-label={`Open ${d.title}`}
                      onClick={() => openDocument(d.id)}
                    >
                      <ArrowUpRight size={17} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {!docs.length && <Empty />}
        </div>
        <div className="table-foot">
          <span>{docs.length} documents in this view</span>
          <span>PDF & UTF-8 TXT · 10 MB maximum</span>
        </div>
      </section>
      {upload && <UploadDialog onClose={() => setUpload(false)} />}
    </>
  )
}

function UploadDialog({ onClose }: { onClose: () => void }) {
  const { refresh, notify } = useWorkspace(),
    { t } = useI18n()
  const [file, setFile] = useState<File | null>(null),
    [category, setCategory] = useState('Policy'),
    [classification, setClassification] = useState('internal'),
    [busy, setBusy] = useState(false),
    [error, setError] = useState(''),
    ref = useRef<HTMLInputElement>(null)
  async function submit(e: FormEvent) {
    e.preventDefault()
    if (!file) return
    setBusy(true)
    setError('')
    const form = new FormData()
    form.append('file', file)
    form.append('category', category)
    form.append('classification', classification)
    try {
      await api('/api/v1/documents', { method: 'POST', body: form })
      await refresh()
      notify('Document received. Processing will continue in the background.')
      onClose()
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setBusy(false)
    }
  }
  function choose(f: File | undefined) {
    if (!f) return
    if (f.size > 10 * 1024 * 1024) {
      setError('Please choose a file smaller than 10 MB.')
      return
    }
    setFile(f)
    setError('')
  }
  return (
    <Modal title={t('Upload document')} onClose={onClose}>
      <form onSubmit={submit}>
        <div
          className={`dropzone ${file ? 'has-file' : ''}`}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => {
            if (['Enter', ' '].includes(e.key)) {
              e.preventDefault()
              ref.current?.click()
            }
          }}
          onClick={() => ref.current?.click()}
          onDragOver={(e) => e.preventDefault()}
          onDrop={(e) => {
            e.preventDefault()
            choose(e.dataTransfer.files[0])
          }}
        >
          <span className="upload-orb">
            <Upload size={25} />
          </span>
          <strong>{file ? file.name : 'Drop your evidence here'}</strong>
          <span>
            {file
              ? `${(file.size / 1024).toFixed(1)} KB · ready to upload`
              : 'or click to browse your files'}
          </span>
          <small>Text-based PDF or UTF-8 TXT · up to 10 MB</small>
        </div>
        <input
          ref={ref}
          type="file"
          accept=".pdf,.txt"
          className="sr-only"
          aria-label="Choose document file"
          onChange={(e) => choose(e.target.files?.[0])}
        />
        <div className="form-grid">
          <Field label="Category">
            <select value={category} onChange={(e) => setCategory(e.target.value)}>
              {['Policy', 'Procurement', 'Quotation', 'HR', 'Service desk'].map((c) => (
                <option key={c}>{c}</option>
              ))}
            </select>
          </Field>
          <Field label="Classification">
            <select value={classification} onChange={(e) => setClassification(e.target.value)}>
              <option value="internal">Internal</option>
              <option value="synthetic">Synthetic</option>
              <option value="confidential">Confidential · restricted roles</option>
            </select>
          </Field>
        </div>
        <div className="callout">
          <ShieldCheck size={19} />
          <p>
            Upload only documents you’re authorised to process. Scanned image-only PDFs are flagged
            as needing OCR; confidential sources are restricted to analyst, reviewer and tenant
            admin roles.
          </p>
        </div>
        {error && (
          <div className="form-error" role="alert">
            {error}
          </div>
        )}
        <div className="modal-actions">
          <button type="button" className="btn" onClick={onClose}>
            {t('Cancel')}
          </button>
          <button className="btn primary" disabled={!file || busy}>
            {busy ? 'Uploading…' : t('Upload')}
            <Upload size={15} />
          </button>
        </div>
      </form>
    </Modal>
  )
}

export function Knowledge() {
  const { data, refresh, notify, openDocument } = useWorkspace(),
    { t } = useI18n()
  const [question, setQuestion] = useState(''),
    [domain, setDomain] = useState('all'),
    [messages, setMessages] = useState<{ question: string; answer: Answer }[]>([]),
    [busy, setBusy] = useState(false),
    bottom = useRef<HTMLDivElement>(null)
  async function ask(value = question) {
    if (value.trim().length < 3 || busy) return
    setBusy(true)
    setQuestion('')
    try {
      const answer = await api<Answer>('/api/v1/knowledge/query', {
        method: 'POST',
        body: JSON.stringify({ question: value, domain }),
      })
      setMessages((m) => [...m, { question: value, answer }])
      await refresh()
      setTimeout(() => bottom.current?.scrollIntoView({ behavior: 'smooth', block: 'end' }), 100)
    } catch (e) {
      notify((e as Error).message, true)
      setQuestion(value)
    } finally {
      setBusy(false)
    }
  }
  return (
    <>
      <PageTitle
        eyebrow="GROUNDED IN YOUR SOURCES"
        title="Knowledge assistant"
        description="Find the passage behind the answer. Your evidence, with context and citations."
        actions={
          <Badge status="ready">
            {data.config.model_mode === 'extractive'
              ? t('Local extractive mode')
              : data.config.model_mode === 'ollama'
                ? 'Local model'
                : 'Approved hosted model'}
          </Badge>
        }
      />
      <div className="knowledge-layout">
        <aside className="panel knowledge-sidebar">
          <div className="knowledge-side-top">
            <BookOpen size={20} />
            <h3>Knowledge spaces</h3>
          </div>
          {[
            {
              id: 'all',
              name: 'All evidence',
              icon: Layers3,
              description: 'Search your permitted library',
            },
            {
              id: 'procurement',
              name: 'Procurement',
              icon: ShoppingBag,
              description: 'Policies & supplier evidence',
            },
            {
              id: 'hr',
              name: 'Human capital',
              icon: Users,
              description: 'Employee policy guidance',
            },
            {
              id: 'service',
              name: 'Service desk',
              icon: LifeBuoyIcon,
              description: 'Support & escalation',
            },
          ].map((d) => (
            <button
              className={`knowledge-space ${domain === d.id ? 'active' : ''}`}
              key={d.id}
              onClick={() => setDomain(d.id)}
            >
              <d.icon size={18} />
              <span>
                <strong>{t(d.name)}</strong>
                <small>{d.description}</small>
              </span>
            </button>
          ))}
          <div className="knowledge-privacy">
            <ShieldCheck size={22} />
            <strong>Permission-aware by design</strong>
            <p>
              Only sources you can access are considered. Extractive answers show source passages.
              Hybrid search, when enabled, uses a local embedding model.
            </p>
            <span>
              {data.documents.filter((d) => d.status === 'ready').length} available sources
            </span>
          </div>
        </aside>
        <section className="panel chat-panel">
          <header className="chat-header">
            <span className="assistant-avatar">
              <Sparkles size={20} />
            </span>
            <div>
              <strong>Nawa Knowledge</strong>
              <span>
                <span className="pulse-dot" />
                {data.config.model_mode === 'extractive'
                  ? 'Local source retrieval'
                  : data.config.model_mode === 'ollama'
                    ? 'Local model route'
                    : 'Approved hosted route'}
              </span>
            </div>
            <button
              className="icon-btn"
              aria-label="Clear conversation"
              disabled={!messages.length || busy}
              onClick={() => setMessages([])}
            >
              <RefreshCw size={17} />
            </button>
          </header>
          <div className="chat-body">
            {!messages.length ? (
              <div className="chat-welcome">
                <div className="welcome-spark">
                  <Sparkles size={34} />
                </div>
                <span className="eyebrow">A CLEARER START</span>
                <h2>
                  What would you like
                  <br />
                  to understand?
                </h2>
                <p>
                  Explore policies, check requirements, or find the evidence you need to move a case
                  forward.
                </p>
                <div className="suggestion-grid">
                  {[
                    'What does the procurement policy require?',
                    'How does independent approval work?',
                    'What is the annual leave guidance?',
                    'ما متطلبات المشتريات؟',
                  ].map((q) => (
                    <button key={q} onClick={() => ask(q)}>
                      {q}
                      <ArrowUpRight size={15} />
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              messages.map((m, i) => (
                <div className="chat-turn" key={i}>
                  <div className="user-message">{m.question}</div>
                  <div className="assistant-message">
                    <span className="assistant-avatar">
                      <Sparkles size={17} />
                    </span>
                    <div>
                      <div className="message-author">
                        Nawa{' '}
                        <span>
                          {m.answer.status === 'insufficient_evidence'
                            ? t(
                                [
                                  'conflicting_field_evidence',
                                  'conflicting_policy_counts',
                                ].includes(m.answer.reason || '')
                                  ? 'Conflicting evidence'
                                  : 'Evidence unavailable',
                              )
                            : m.answer.mode === 'extractive'
                              ? t(
                                  m.answer.reason === 'policy_count_verified'
                                    ? 'Verified source count'
                                    : 'Source passages',
                                )
                              : 'Generated answer'}
                        </span>
                      </div>
                      <p dir="auto">{m.answer.answer}</p>
                      {m.answer.citations.map((c, j) => (
                        <button
                          className="citation-card"
                          key={`${c.document_id}-${j}`}
                          onClick={() => openDocument(c.document_id, c.version)}
                        >
                          <div>
                            <span className="citation-index">{j + 1}</span>
                            <strong>{c.title}</strong>
                            <span className="muted">
                              p. {c.page} · v{c.version}
                            </span>
                            <ArrowUpRight size={14} />
                          </div>
                          <p dir="auto">{c.text}</p>
                        </button>
                      ))}
                      {m.answer.status === 'insufficient_evidence' && (
                        <div className="inline-note">
                          <Info size={15} />
                          {t(
                            ['policy_count_unverified', 'conflicting_policy_counts'].includes(
                              m.answer.reason || '',
                            )
                              ? 'Review the policy passages and confirm the applicable requirement.'
                              : 'Check the requested supplier and field, or add a permitted source that contains the details.',
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))
            )}
            {busy && (
              <div className="chat-thinking">
                <Sparkles size={16} />
                <span>Finding relevant evidence</span>
                <i />
                <i />
                <i />
              </div>
            )}
            <div ref={bottom} />
          </div>
          <form
            className="chat-composer"
            onSubmit={(e) => {
              e.preventDefault()
              ask()
            }}
          >
            <div className="composer-input">
              <input
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                placeholder={t('Ask a question')}
                aria-label="Question for knowledge assistant"
                maxLength={1500}
                disabled={busy}
              />
              <button
                type="submit"
                className="send-button"
                disabled={question.trim().length < 3 || busy}
                aria-label="Send question"
              >
                <Send size={18} />
              </button>
            </div>
            <small>
              <ShieldCheck size={12} />
              Evidence supports the answer. People own the decision.
            </small>
          </form>
        </section>
      </div>
    </>
  )
}
function LifeBuoyIcon(p: { size?: number }) {
  return <MessageSquare {...p} />
}

export function Agents() {
  const { data, openCase } = useWorkspace(),
    { t } = useI18n()
  const [run, setRun] = useState<WorkflowRun | null>(null)
  const modules = [
    {
      name: 'Document intelligence',
      icon: FileText,
      type: 'Local parsing & retrieval',
      description: 'Preserves page provenance and retrieves authorised passages.',
      tone: 'blue',
    },
    {
      name: 'Procurement validation',
      icon: ListChecks,
      type: 'Deterministic rules',
      description: 'Checks amounts, currencies, validity and source references.',
      tone: 'emerald',
    },
    {
      name: 'Evidence comparison',
      icon: Layers3,
      type: 'Bounded LangGraph',
      description: 'Builds an inspectable comparison without choosing a winner.',
      tone: 'purple',
    },
    {
      name: 'Independent review',
      icon: UserCheck,
      type: 'Human authority',
      description: 'Pauses for a permitted reviewer with a current evidence snapshot.',
      tone: 'amber',
    },
  ]
  return (
    <>
      <PageTitle
        eyebrow="ORCHESTRATION"
        title="Agent workflows"
        description="Purposeful automation. Explicit steps, persistent evidence and human control."
        actions={<Badge status="ready">Bounded execution</Badge>}
      />
      <div className="module-grid">
        {modules.map((m) => (
          <div className={`panel module-card ${m.tone}`} key={m.name}>
            <div className="module-icon">
              <m.icon size={23} />
            </div>
            <span className="module-type">{m.type}</span>
            <h3>{m.name}</h3>
            <p>{m.description}</p>
            <div>
              <span className="pulse-dot" />
              Available capability
            </div>
          </div>
        ))}
      </div>
      <section className="panel flow-visual">
        <SectionHead
          title="Evidence to decision"
          subtitle="A controlled graph. No unconstrained autonomous loop."
        />
        <div className="flow-nodes">
          {[
            { label: 'Intake', icon: ShoppingBag },
            { label: 'Evidence', icon: FileText },
            { label: 'Validation', icon: ShieldCheck },
            { label: 'Comparison', icon: Layers3 },
            { label: 'Human review', icon: UserCheck },
          ].map((n, i) => (
            <div className="flow-node-wrap" key={n.label}>
              <div className={`flow-node ${i === 4 ? 'human' : ''}`}>
                <n.icon size={21} />
                <strong>{n.label}</strong>
                <small>{i === 4 ? 'Explicit approval' : 'Typed, bounded step'}</small>
              </div>
              {i < 4 && <ArrowRight className="flow-arrow" size={19} />}
            </div>
          ))}
        </div>
        <div className="flow-controls">
          <span>
            <Database size={13} />
            Persistent run records
          </span>
          <span>
            <ShieldCheck size={13} />
            Version-bound review
          </span>
          <span>
            <Clock3 size={13} />
            Bounded graph steps
          </span>
        </div>
      </section>
      <section className="panel">
        <SectionHead
          title="Run history"
          subtitle="Recorded workflow executions from this workspace."
        />
        <div className="table-scroll">
          <table className="data-table">
            <thead>
              <tr>
                <th>Workflow run</th>
                <th>{t('Case')}</th>
                <th>Steps</th>
                <th>{t('Status')}</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {data.runs.map((r) => {
                const c = data.cases.find((c) => c.id === r.case_id)
                return (
                  <tr key={r.id}>
                    <td>
                      <button className="table-case" onClick={() => setRun(r)}>
                        <span className="case-glyph tone-2">
                          <Workflow size={18} />
                        </span>
                        <span>
                          <strong>Procurement comparison</strong>
                          <small>RUN-{r.id.slice(0, 8).toUpperCase()}</small>
                        </span>
                      </button>
                    </td>
                    <td>
                      <button className="text-btn" onClick={() => openCase(r.case_id)}>
                        {c?.reference || 'View case'}
                      </button>
                    </td>
                    <td>{r.steps.length} recorded</td>
                    <td>
                      <Badge status={r.status} />
                    </td>
                    <td>
                      <button
                        className="icon-btn"
                        aria-label="View run details"
                        onClick={() => setRun(r)}
                      >
                        <ArrowUpRight size={17} />
                      </button>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
          {!data.runs.length && (
            <Empty
              title="No workflow runs yet"
              text="Open a draft procurement case and run its comparison."
            />
          )}
        </div>
      </section>
      {run && (
        <Modal title={t('Run details')} onClose={() => setRun(null)}>
          <div className="detail-meta">
            <code>{run.id}</code>
            <Badge status={run.status} />
          </div>
          <div className="run-steps">
            {run.steps.map((s, i) => (
              <div key={i}>
                <span className="step-check">
                  <Check size={16} />
                </span>
                <section>
                  <strong>{s.name}</strong>
                  <p>{s.detail}</p>
                </section>
                <Badge status="ready">{s.status}</Badge>
              </div>
            ))}
          </div>
          <div className="callout">
            <Info size={18} />
            <p>
              This bounded graph performs deterministic validation and comparison. Model-based
              knowledge answers are a separate, explicitly configured capability. No external
              purchasing action is executed.
            </p>
          </div>
        </Modal>
      )}
    </>
  )
}

export function Analytics() {
  const { data } = useWorkspace(),
    { t } = useI18n(),
    a = data.analytics
  const [range, setRange] = useState('28'),
    history = a.history.slice(-Number(range))
  return (
    <>
      <PageTitle
        eyebrow="DECISION SUPPORT"
        title="Operational intelligence"
        description="Understand workload patterns, compare a baseline, and plan with context."
        actions={
          <Select
            label="Historical period"
            value={range}
            onChange={setRange}
            options={[
              { value: '14', label: 'Last 14 days' },
              { value: '28', label: 'Last 28 days' },
              { value: '56', label: 'Last 56 days' },
            ]}
          />
        }
      />
      <div className="callout analytics-notice">
        <Info size={19} />
        <p>
          <strong>Synthetic demonstration.</strong> The workload below is generated sample data.
          Forecasts are advisory; the range is illustrative, not a calibrated prediction interval.
        </p>
      </div>
      <div className="stats-grid">
        <Metric
          label="Historical requests"
          value={history.reduce((s, r) => s + r.volume, 0).toString()}
          note={`${range}-day selected period`}
          icon={Activity}
        />
        <Metric
          label="Next 7 days"
          value={a.forecast.reduce((s, r) => s + r.volume, 0).toString()}
          note="Weekday-mean baseline forecast"
          icon={BarChart3}
        />
        <Metric
          label="Hold-out MAE"
          value={a.holdout_mae.toFixed(2)}
          note="Previous-week naive · 7-day hold-out"
          icon={ListChecks}
        />
        <Metric
          label="Model complexity"
          value="Baseline"
          note="Interpretable before sophisticated"
          icon={Layers3}
        />
      </div>
      <section className="panel chart-panel analytics-chart">
        <SectionHead title="Historical workload" subtitle={a.source} />
        <div className="big-chart">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={history} margin={{ right: 20, left: -15, bottom: 5, top: 20 }}>
              <defs>
                <linearGradient id="analyticsFill" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#263f64" stopOpacity={0.23} />
                  <stop offset="100%" stopColor="#263f64" stopOpacity={0.01} />
                </linearGradient>
              </defs>
              <CartesianGrid stroke="#ebefed" vertical={false} strokeDasharray="4 4" />
              <XAxis
                dataKey="label"
                axisLine={false}
                tickLine={false}
                minTickGap={35}
                tick={{ fontSize: 11, fill: '#89929b' }}
              />
              <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 11, fill: '#89929b' }} />
              <Tooltip contentStyle={{ borderRadius: 12, borderColor: '#e6ece9', fontSize: 12 }} />
              <Area
                isAnimationActive={false}
                dataKey="volume"
                name="Requests"
                type="monotone"
                stroke="#263f64"
                fill="url(#analyticsFill)"
                strokeWidth={2}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </section>
      <div className="two-col">
        <section className="panel chart-panel">
          <SectionHead
            title="Weekly forecast"
            subtitle="Four-week weekday mean · illustrative workload"
          />
          <div className="forecast-chart">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={a.forecast} margin={{ left: -20, right: 10, top: 20, bottom: 0 }}>
                <CartesianGrid vertical={false} stroke="#edf0ee" />
                <XAxis dataKey="label" axisLine={false} tickLine={false} tick={{ fontSize: 11 }} />
                <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 11 }} />
                <Tooltip contentStyle={{ borderRadius: 12, fontSize: 12 }} />
                <Bar
                  isAnimationActive={false}
                  dataKey="volume"
                  name="Predicted requests"
                  fill="#b49560"
                  radius={[5, 5, 0, 0]}
                  maxBarSize={38}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </section>
        <section className="panel model-card">
          <SectionHead title="Baseline model card" />
          <div className="model-row">
            <span>Serving model</span>
            <strong>{a.model}</strong>
          </div>
          <div className="model-row">
            <span>Evaluated baseline</span>
            <strong>{a.baseline}</strong>
          </div>
          <div className="model-row">
            <span>Training / held-out split</span>
            <strong>49 / 7 chronological days</strong>
          </div>
          <div className="model-row">
            <span>Training input</span>
            <strong>Generated workload observations</strong>
          </div>
          <div className="model-row">
            <span>Decision authority</span>
            <strong>Advisory only</strong>
          </div>
          <p className="muted">
            No claims of real-world forecast accuracy. Add authorised historical data and compare
            advanced models on a held-out temporal set before promotion.
          </p>
        </section>
      </div>
    </>
  )
}
function Metric({
  label,
  value,
  note,
  icon: Icon,
}: {
  label: string
  value: string
  note: string
  icon: typeof Activity
}) {
  return (
    <div className="stat-card">
      <div className="stat-top">
        <span>{label}</span>
        <span className="stat-icon">
          <Icon size={18} />
        </span>
      </div>
      <strong className={value.length > 5 ? 'metric-text' : ''}>{value}</strong>
      <div className="stat-note">{note}</div>
    </div>
  )
}

export function ServiceDesk() {
  const { data, user, refresh, notify } = useWorkspace(),
    { t } = useI18n()
  const [status, setStatus] = useState('all'),
    [search, setSearch] = useState(''),
    [creating, setCreating] = useState(false),
    [busy, setBusy] = useState('')
  const tickets = data.tickets.filter(
    (x) =>
      (status === 'all' || x.status === status) &&
      x.title.toLowerCase().includes(search.toLowerCase()),
  )
  async function update(ticket: Ticket) {
    setBusy(ticket.id)
    try {
      await api(`/api/v1/tickets/${ticket.id}`, {
        method: 'PATCH',
        body: JSON.stringify({
          status:
            ticket.status === 'Open'
              ? 'In progress'
              : ticket.status === 'In progress'
                ? 'Resolved'
                : 'Open',
        }),
      })
      await refresh()
      notify('Service request updated.')
    } catch (e) {
      notify((e as Error).message, true)
    } finally {
      setBusy('')
    }
  }
  return (
    <>
      <PageTitle
        eyebrow="PEOPLE & SUPPORT"
        title="Service desk"
        description="A considered place for questions, access requests and everyday support."
        actions={
          user.role !== 'auditor' && (
            <button className="btn primary" onClick={() => setCreating(true)}>
              <Plus size={17} />
              {t('New request')}
            </button>
          )
        }
      />
      <div className="three-col service-stats">
        {[
          { label: 'Open requests', status: 'Open', icon: MessageSquare },
          { label: 'In progress', status: 'In progress', icon: Clock3 },
          { label: 'Resolved', status: 'Resolved', icon: CheckCircle2 },
        ].map((s, i) => (
          <div className={`panel service-stat tone-${i}`} key={s.status}>
            <span>
              <s.icon size={22} />
            </span>
            <div>
              <strong>{data.tickets.filter((x) => x.status === s.status).length}</strong>
              <p>{t(s.label)}</p>
            </div>
          </div>
        ))}
      </div>
      <section className="panel">
        <div className="list-toolbar">
          <div className="tabs">
            {['all', 'Open', 'In progress', 'Resolved'].map((x) => (
              <button className={status === x ? 'active' : ''} key={x} onClick={() => setStatus(x)}>
                {t(x === 'all' ? 'All requests' : x)}
              </button>
            ))}
          </div>
          <div className="search-input">
            <Search size={16} />
            <input
              aria-label="Search service requests"
              placeholder="Search requests…"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
        </div>
        <div className="table-scroll">
          <table className="data-table">
            <thead>
              <tr>
                <th>Request</th>
                <th>{t('Category')}</th>
                <th>{t('Priority')}</th>
                <th>{t('Status')}</th>
                <th>{t('Actions')}</th>
              </tr>
            </thead>
            <tbody>
              {tickets.map((x, i) => (
                <tr key={x.id}>
                  <td>
                    <div className="table-case">
                      <span className={`case-glyph tone-${i % 4}`}>
                        <MessageSquare size={17} />
                      </span>
                      <span>
                        <strong>{x.title}</strong>
                        <small>{x.created_by}</small>
                      </span>
                    </div>
                  </td>
                  <td className="muted">{t(x.category)}</td>
                  <td>
                    <Badge status={x.priority}>{t(x.priority)}</Badge>
                  </td>
                  <td>
                    <Badge status={x.status}>{t(x.status)}</Badge>
                  </td>
                  <td>
                    {['analyst', 'admin'].includes(user.role) ? (
                      <button
                        className="btn small"
                        disabled={busy === x.id}
                        onClick={() => update(x)}
                      >
                        {busy === x.id
                          ? 'Saving…'
                          : x.status === 'Open'
                            ? 'Start work'
                            : x.status === 'In progress'
                              ? 'Resolve'
                              : 'Reopen'}
                        <ArrowRight size={13} />
                      </button>
                    ) : (
                      <span className="muted">{t('Read-only access')}</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {!tickets.length && <Empty />}
        </div>
      </section>
      <div className="inline-note">
        <ShieldCheck size={15} />
        Requests are handled within your tenant. No outbound messages are sent automatically.
      </div>
      {creating && <NewTicket onClose={() => setCreating(false)} />}
    </>
  )
}
function NewTicket({ onClose }: { onClose: () => void }) {
  const { refresh, notify } = useWorkspace(),
    { t } = useI18n()
  const [busy, setBusy] = useState(false),
    [error, setError] = useState('')
  async function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    const f = new FormData(e.currentTarget)
    setBusy(true)
    try {
      await api('/api/v1/tickets', { method: 'POST', body: JSON.stringify(Object.fromEntries(f)) })
      await refresh()
      notify('Service request created.')
      onClose()
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setBusy(false)
    }
  }
  return (
    <Modal title={t('New request')} onClose={onClose}>
      <form onSubmit={submit}>
        <Field label="Title">
          <input
            name="title"
            required
            minLength={5}
            maxLength={200}
            placeholder="What can we help with?"
          />
        </Field>
        <div className="form-grid">
          <Field label="Category">
            <select name="category">
              {['IT support', 'Access request', 'Facilities', 'HR enquiry'].map((x) => (
                <option key={x}>{x}</option>
              ))}
            </select>
          </Field>
          <Field label="Priority">
            <select name="priority">
              {['Normal', 'High', 'Urgent'].map((x) => (
                <option key={x}>{x}</option>
              ))}
            </select>
          </Field>
        </div>
        {error && (
          <div className="form-error" role="alert">
            {error}
          </div>
        )}
        <div className="modal-actions">
          <button className="btn" type="button" onClick={onClose}>
            {t('Cancel')}
          </button>
          <button className="btn primary" disabled={busy}>
            {busy ? 'Creating…' : t('New request')}
          </button>
        </div>
      </form>
    </Modal>
  )
}

export function Security() {
  const { data } = useWorkspace(),
    { t } = useI18n()
  const controls = [
    {
      title: 'Server-side tenant checks',
      note: 'All workspace queries and mutations resolve verified tenant scope.',
      ok: true,
      icon: Users,
    },
    {
      title: 'Document access policies',
      note: 'Role-based evidence access, scoped downloads and deletion.',
      ok: true,
      icon: FileCheck2,
    },
    {
      title: 'Human approval integrity',
      note: 'Revision-bound evidence snapshots and independent reviewer checks.',
      ok: true,
      icon: UserCheck,
    },
    {
      title: 'CSRF & session controls',
      note: 'Opaque HttpOnly sessions, CSRF verification and exact origin checks.',
      ok: true,
      icon: KeyRound,
    },
    {
      title: 'Bounded workflow execution',
      note: 'Typed validation, graph step limit and deterministic calculations.',
      ok: true,
      icon: Workflow,
    },
    {
      title: 'Verified production identity',
      note:
        data.config.auth_mode === 'oidc'
          ? 'OIDC mode selected; deployment integration still needs validation.'
          : 'Local demo identities are enabled. Configure OIDC before deployment.',
      ok: false,
      icon: LockKeyhole,
    },
    {
      title: 'Encryption & private infrastructure',
      note: 'TLS, database/storage encryption and managed keys require deployment configuration.',
      ok: false,
      icon: Cloud,
    },
    {
      title: 'Independent audit integrity',
      note: 'Database audit history is implemented; immutable external protection is not configured.',
      ok: false,
      icon: Shield,
    },
    {
      title: 'Restore & operational readiness',
      note: 'Run a verified backup/restore, security assessment and incident exercise before real-data use.',
      ok: false,
      icon: Database,
    },
  ]
  function download() {
    const blob = new Blob(
      [
        JSON.stringify(
          {
            generated: new Date().toISOString(),
            notice: 'Implementation summary, not a compliance certification',
            environment: data.config,
            controls: controls.map(({ icon, ...c }) => c),
          },
          null,
          2,
        ),
      ],
      { type: 'application/json' },
    )
    const url = URL.createObjectURL(blob),
      a = document.createElement('a')
    a.href = url
    a.download = 'nawa-control-summary.json'
    a.click()
    URL.revokeObjectURL(url)
  }
  return (
    <>
      <PageTitle
        eyebrow="GOVERNANCE"
        title="Security center"
        description="Understand your controls. Distinguish implemented safeguards from deployment work."
        actions={
          <button className="btn" onClick={download}>
            <ArrowDownToLine size={16} />
            Export control summary
          </button>
        }
      />
      <section className="security-hero">
        <div className="security-shield">
          <ShieldCheck size={43} />
        </div>
        <div>
          <span className="eyebrow">TRANSPARENT BY DESIGN</span>
          <h2>Security is a practice, not a badge.</h2>
          <p>
            {controls.filter((x) => x.ok).length} application controls implemented ·{' '}
            {controls.filter((x) => !x.ok).length} deployment controls require verification.
          </p>
        </div>
        <span className="security-profile">
          <span className="tiny-dot amber" />
          Synthetic sandbox
        </span>
      </section>
      <div className="security-grid">
        {controls.map((c) => (
          <section className="panel control-card" key={c.title}>
            <span className={`control-icon ${c.ok ? 'implemented' : 'pending'}`}>
              <c.icon size={22} />
            </span>
            <div>
              <h3>{c.title}</h3>
              <p>{c.note}</p>
              <Badge status={c.ok ? 'ready' : 'needs_information'}>
                {t(c.ok ? 'Implemented' : 'Deployment required')}
              </Badge>
            </div>
          </section>
        ))}
      </div>
      <div className="callout">
        <Info size={19} />
        <p>
          <strong>No sovereignty or compliance certification is implied.</strong> Data location,
          inference, OCR, telemetry, backups, support access and applicable policies need
          deployment-specific review. Application controls alone are not proof of complete
          protection.
        </p>
      </div>
    </>
  )
}

export function AuditTrail() {
  const { data } = useWorkspace(),
    { t, locale } = useI18n()
  const [search, setSearch] = useState(''),
    [event, setEvent] = useState<(typeof data.events)[number] | null>(null)
  const events = data.events.filter((x) =>
    (x.action + x.actor + x.resource).toLowerCase().includes(search.toLowerCase()),
  )
  return (
    <>
      <PageTitle
        eyebrow="ACCOUNTABILITY"
        title="Audit trail"
        description="A readable record of who did what, against which resource and when."
      />
      <section className="panel">
        <div className="list-toolbar">
          <div className="audit-live">
            <span className="pulse-dot" />
            Tenant-scoped business events <span className="count-chip">{data.events.length}</span>
          </div>
          <div className="search-input">
            <Search size={16} />
            <input
              placeholder="Search activity…"
              aria-label="Search audit events"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
        </div>
        <div className="table-scroll">
          <table className="data-table">
            <thead>
              <tr>
                <th>{t('Action')}</th>
                <th>{t('Actor')}</th>
                <th>{t('Resource')}</th>
                <th>{t('Time')}</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {events.map((e) => (
                <tr key={e.id}>
                  <td>
                    <div className="table-case">
                      <span className="case-glyph tone-0">
                        <Activity size={16} />
                      </span>
                      <strong>{e.action}</strong>
                    </div>
                  </td>
                  <td>
                    <div className="actor-cell">
                      <Avatar name={e.actor} size="small" />
                      <span>
                        {e.actor}
                        <small>{e.role}</small>
                      </span>
                    </div>
                  </td>
                  <td className="muted resource-cell">{e.resource}</td>
                  <td className="muted nowrap">
                    {humanDate(e.created_at, locale, true)}
                    <small className="time-sub">
                      {new Date(e.created_at).toLocaleTimeString('en-GB', {
                        hour: '2-digit',
                        minute: '2-digit',
                        timeZone: 'Asia/Dubai',
                      })}{' '}
                      GST
                    </small>
                  </td>
                  <td>
                    <button
                      className="icon-btn"
                      aria-label="Inspect audit event"
                      onClick={() => setEvent(e)}
                    >
                      <ArrowUpRight size={17} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {!events.length && <Empty />}
        </div>
        <div className="table-foot">
          <span>Showing {events.length} most recent permitted events</span>
          <span>Raw document content is not recorded here</span>
        </div>
      </section>
      {event && (
        <Modal title="Audit event" onClose={() => setEvent(null)}>
          <div className="model-row">
            <span>Action</span>
            <strong>{event.action}</strong>
          </div>
          <div className="model-row">
            <span>Actor</span>
            <strong>{event.actor}</strong>
          </div>
          <div className="model-row">
            <span>Role</span>
            <strong>{event.role}</strong>
          </div>
          <div className="model-row">
            <span>Resource</span>
            <strong>{event.resource}</strong>
          </div>
          <div className="model-row">
            <span>Time (UTC)</span>
            <strong>{event.created_at}</strong>
          </div>
          <h3>Recorded metadata</h3>
          <pre className="json-view">{JSON.stringify(event.details, null, 2)}</pre>
          <p className="muted">
            Business audit is stored in the application database. Separately protected immutable
            audit storage remains deployment work.
          </p>
        </Modal>
      )}
    </>
  )
}

export function Settings() {
  const { data, user, notify } = useWorkspace(),
    { locale, setLocale, t } = useI18n()
  const [digest, setDigest] = useState(user.preferences.digest ?? true),
    [busy, setBusy] = useState(false)
  async function save() {
    setBusy(true)
    try {
      const prefs = await api<UserPreferences>('/api/v1/preferences', {
        method: 'PUT',
        body: JSON.stringify({ language: locale, digest }),
      })
      user.preferences = prefs
      notify('Workspace preferences saved.')
    } catch (e) {
      notify((e as Error).message, true)
    } finally {
      setBusy(false)
    }
  }
  return (
    <>
      <PageTitle
        eyebrow="MAKE IT YOURS"
        title="Workspace preferences"
        description="A few thoughtful settings for the way you work."
      />
      <div className="settings-layout">
        <section className="panel settings-profile">
          <div className="profile-cover" />
          <div className="profile-identity">
            <Avatar name={user.name} />
            <h2>{user.name}</h2>
            <p>{user.email}</p>
            <span className="role-label">{user.role}</span>
          </div>
          <div className="model-row">
            <span>Organisation</span>
            <strong>{data.tenant.name}</strong>
          </div>
          <div className="model-row">
            <span>Authentication</span>
            <strong>
              {data.config.auth_mode === 'demo' ? 'Local demo session' : 'OIDC session'}
            </strong>
          </div>
          <p className="muted">
            Switch roles or tenants by signing out and selecting another synthetic demo identity.
          </p>
        </section>
        <div>
          <section className="panel settings-section">
            <SectionHead
              title="Workspace preferences"
              subtitle="Your language and review preferences."
            />
            <div className="setting-row">
              <div>
                <strong>{t('Language')}</strong>
                <p>Choose your interface language and reading direction.</p>
              </div>
              <select
                aria-label="Interface language"
                value={locale}
                onChange={(e) => setLocale(e.target.value as 'en' | 'ar')}
              >
                <option value="en">English</option>
                <option value="ar">العربية</option>
              </select>
            </div>
            <div className="setting-row">
              <div>
                <strong>Review digest preference</strong>
                <p>Save your preference. Email delivery is not configured in this sandbox.</p>
              </div>
              <button
                className={`toggle ${digest ? 'on' : ''}`}
                role="switch"
                aria-checked={digest}
                aria-label="Review digest preference"
                onClick={() => setDigest(!digest)}
              >
                <span />
              </button>
            </div>
            <div className="settings-actions">
              <button className="btn primary" disabled={busy} onClick={save}>
                {busy ? 'Saving…' : t('Save preferences')}
                <Check size={15} />
              </button>
            </div>
          </section>
          <section className="panel settings-section">
            <SectionHead
              title="Application settings"
              subtitle="Runtime configuration is managed by the environment, not browser inputs."
            />
            {[
              ['Environment', data.config.environment],
              ['Database', data.config.database],
              ['Knowledge mode', data.config.model_mode],
              [
                'Retrieval',
                data.config.retrieval_mode === 'hybrid' ? 'BM25 + local embeddings' : 'Local BM25',
              ],
              [
                'Local OCR',
                data.config.ocr_mode === 'auto' ? 'Automatic when tools are installed' : 'Disabled',
              ],
              ['Data profile', 'Synthetic sandbox'],
              ['External purchasing actions', 'Disabled'],
            ].map(([a, b]) => (
              <div className="model-row" key={a}>
                <span>{a}</span>
                <strong>{b}</strong>
              </div>
            ))}
            <div className="inline-note">
              <LockKeyhole size={15} />
              Provider credentials and deployment controls are never edited in this browser.
            </div>
          </section>
        </div>
      </div>
    </>
  )
}
interface UserPreferences {
  language: 'en' | 'ar'
  digest: boolean
}
