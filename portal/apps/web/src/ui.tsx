import { cloneElement, isValidElement, useEffect, useId, useRef } from 'react'
import type { ReactElement, ReactNode } from 'react'
import { ArrowUpRight, Check, ChevronDown, FileSearch, X } from 'lucide-react'
import { useI18n } from './i18n'

export function Logo({ small = false }: { small?: boolean }) {
  return (
    <div className={`brand ${small ? 'small' : ''}`}>
      <img className="brand-mark" src="/uae-ai-mark.svg" width="52" height="58" alt="" />
      {!small && (
        <span className="brand-wordmark">
          UAE<span className="brand-dot"> AI</span>
          <small>SOVEREIGN AGENTIC AI</small>
        </span>
      )}
    </div>
  )
}
export function Badge({ status, children }: { status?: string; children?: ReactNode }) {
  const { t } = useI18n()
  const labels: Record<string, string> = {
    awaiting_review: 'In review',
    draft: 'Draft',
    approved_simulation: 'Approved',
    rejected: 'Rejected',
    needs_information: 'Needs information',
    processing: 'Processing',
    cancelled: 'Cancelled',
    failed: 'Failed',
    ready: 'Ready',
    queued: 'Queued',
    needs_ocr: 'Needs OCR',
    pending: 'In review',
  }
  const s = status || 'neutral'
  return (
    <span className={`badge ${s.toLowerCase().replaceAll(' ', '_')}`}>
      <span className="status-dot" />
      {children || t(labels[s] || s)}
    </span>
  )
}
export function Avatar({ name, size = 'normal' }: { name: string; size?: 'normal' | 'small' }) {
  return (
    <span className={`avatar ${size}`} aria-label={name}>
      {name
        .split(' ')
        .filter(Boolean)
        .slice(0, 2)
        .map((n) => n[0])
        .join('')}
    </span>
  )
}
export function Modal({
  title,
  children,
  onClose,
  wide = false,
}: {
  title: string
  children: ReactNode
  onClose: () => void
  wide?: boolean
}) {
  const id = useId(),
    ref = useRef<HTMLDivElement>(null),
    callback = useRef(onClose)
  callback.current = onClose
  useEffect(() => {
    const previous = document.activeElement as HTMLElement
    const old = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    const el = ref.current
    const timer = setTimeout(
      () => el?.querySelector<HTMLElement>('input, select, textarea, button, a[href]')?.focus(),
      20,
    )
    const key = (event: KeyboardEvent) => {
      const dialogs = document.querySelectorAll('[role="dialog"]')
      if (dialogs[dialogs.length - 1] !== el) return
      if (event.key === 'Escape') {
        event.stopPropagation()
        callback.current()
      }
      if (event.key === 'Tab' && el) {
        const nodes = [
          ...el.querySelectorAll<HTMLElement>(
            'button:not(:disabled),a[href],input:not(:disabled),select:not(:disabled),textarea:not(:disabled),[tabindex="0"]',
          ),
        ].filter((n) => n.offsetParent !== null)
        const first = nodes[0],
          last = nodes[nodes.length - 1]
        if (event.shiftKey && document.activeElement === first) {
          event.preventDefault()
          last?.focus()
        } else if (!event.shiftKey && document.activeElement === last) {
          event.preventDefault()
          first?.focus()
        }
      }
    }
    document.addEventListener('keydown', key)
    return () => {
      clearTimeout(timer)
      document.body.style.overflow = old
      document.removeEventListener('keydown', key)
      previous?.focus()
    }
  }, [])
  return (
    <div
      className="modal-backdrop"
      onMouseDown={(e) => {
        if (e.target === e.currentTarget) onClose()
      }}
    >
      <div
        ref={ref}
        className={`modal ${wide ? 'wide' : ''}`}
        role="dialog"
        aria-modal="true"
        aria-labelledby={id}
      >
        <header className="modal-head">
          <h2 id={id}>{title}</h2>
          <button type="button" className="icon-btn" aria-label="Close dialog" onClick={onClose}>
            <X size={20} />
          </button>
        </header>
        <div className="modal-content">{children}</div>
      </div>
    </div>
  )
}
export function Empty({
  title = 'No results found',
  text = 'Try another search or change your filters.',
  action,
}: {
  title?: string
  text?: string
  action?: ReactNode
}) {
  const { t } = useI18n()
  return (
    <div className="empty">
      <div className="empty-icon">
        <FileSearch size={27} />
      </div>
      <h3>{t(title)}</h3>
      <p>{t(text)}</p>
      {action}
    </div>
  )
}
export function PageTitle({
  eyebrow,
  title,
  description,
  actions,
}: {
  eyebrow: string
  title: string
  description: string
  actions?: ReactNode
}) {
  const { t } = useI18n()
  return (
    <div className="page-title">
      <div>
        <div className="eyebrow">{t(eyebrow)}</div>
        <h1>{t(title)}</h1>
        <p>{description}</p>
      </div>
      <div className="page-actions">{actions}</div>
    </div>
  )
}
export function money(value: string | number, currency = 'AED', compact = false) {
  return new Intl.NumberFormat('en-AE', {
    style: 'currency',
    currency,
    maximumFractionDigits: compact ? 0 : 2,
    ...(compact ? { notation: 'compact' as const } : {}),
  }).format(Number(value))
}
export function humanDate(value: string, locale = 'en', short = false) {
  return new Intl.DateTimeFormat(locale === 'ar' ? 'ar-AE' : 'en-GB', {
    day: 'numeric',
    month: 'short',
    ...(short ? {} : { year: 'numeric' }),
    timeZone: 'Asia/Dubai',
  }).format(new Date(value))
}
export function SectionHead({
  title,
  subtitle,
  action,
}: {
  title: string
  subtitle?: string
  action?: ReactNode
}) {
  const { t } = useI18n()
  return (
    <header className="section-head">
      <div>
        <h2>{t(title)}</h2>
        {subtitle && <p>{subtitle}</p>}
      </div>
      {action}
    </header>
  )
}
export function Field({
  label,
  children,
  hint,
}: {
  label: string
  children: ReactNode
  hint?: string
}) {
  const { t } = useI18n(),
    id = useId()
  return (
    <div className="field">
      <label htmlFor={id}>{t(label)}</label>
      {isValidElement(children)
        ? cloneElement(children as ReactElement<{ id?: string }>, { id })
        : children}
      {hint && <small>{hint}</small>}
    </div>
  )
}
export function SuccessLine({ children }: { children: ReactNode }) {
  return (
    <div className="success-line">
      <Check size={15} />
      {children}
    </div>
  )
}
export function LinkButton({ children, onClick }: { children: ReactNode; onClick: () => void }) {
  return (
    <button className="text-btn" onClick={onClick}>
      {children}
      <ArrowUpRight size={15} />
    </button>
  )
}
export function Select({
  value,
  onChange,
  options,
  label,
}: {
  value: string
  onChange: (v: string) => void
  options: { value: string; label: string }[]
  label: string
}) {
  return (
    <div className="select-wrap">
      <select value={value} onChange={(e) => onChange(e.target.value)} aria-label={label}>
        {options.map((x) => (
          <option key={x.value} value={x.value}>
            {x.label}
          </option>
        ))}
      </select>
      <ChevronDown size={14} />
    </div>
  )
}
