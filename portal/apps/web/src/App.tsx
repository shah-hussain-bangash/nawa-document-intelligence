import { useCallback, useEffect, useRef, useState } from 'react'
import { version as appVersion } from '../package.json'
import { Link, NavLink, Route, Routes, useLocation, useNavigate } from 'react-router-dom'
import {
  Activity,
  ArrowDownToLine,
  ArrowRight,
  ArrowUpRight,
  BarChart3,
  Bell,
  BookOpen,
  Bot,
  Check,
  ChevronDown,
  Command,
  FileText,
  Globe2,
  HelpCircle,
  LayoutDashboard,
  LifeBuoy,
  LogOut,
  Menu,
  Plus,
  Search,
  Settings as SettingsIcon,
  ShieldCheck,
  ShoppingBag,
  Sparkles,
  X,
} from 'lucide-react'
import { api, ApiError, setCsrf } from './api'
import type { User, Workspace } from './types'
import { WorkspaceContext } from './context'
import { LocaleContext, useI18n } from './i18n'
import { Avatar, Empty, Logo, Modal } from './ui'
import {
  Dashboard,
  Procurement,
  Documents,
  Knowledge,
  Agents,
  Analytics,
  ServiceDesk,
  Security,
  AuditTrail,
  Settings,
} from './pages'
import { CaseDetail, NewCase, DocumentDetail } from './workflows'

const navigation = [
  { path: '/', label: 'Overview', icon: LayoutDashboard },
  { path: '/procurement', label: 'Procurement', icon: ShoppingBag },
  { path: '/documents', label: 'Documents', icon: FileText },
  { path: '/knowledge', label: 'Knowledge assistant', icon: Sparkles },
  { path: '/agents', label: 'Agent workflows', icon: Bot },
  { path: '/analytics', label: 'Analytics', icon: BarChart3 },
  { path: '/service', label: 'Service desk', icon: LifeBuoy },
  { path: '/security', label: 'Security center', icon: ShieldCheck },
  { path: '/audit', label: 'Audit trail', icon: Activity },
  { path: '/settings', label: 'Settings', icon: SettingsIcon },
]

export default function App() {
  const [locale, setLocale] = useState<'en' | 'ar'>(() =>
    localStorage.getItem('nawa-language') === 'ar' ? 'ar' : 'en',
  )
  const [user, setUser] = useState<User | null>(null),
    [data, setData] = useState<Workspace | null>(null),
    [loading, setLoading] = useState(true),
    [failure, setFailure] = useState('')
  const [toast, setToast] = useState<{ text: string; error: boolean } | null>(null),
    [caseId, setCaseId] = useState<string | null>(null),
    [docId, setDocId] = useState<string | null>(null),
    [docVersion, setDocVersion] = useState<number | undefined>(),
    [newCase, setNewCase] = useState(false)
  const [search, setSearch] = useState(false),
    [help, setHelp] = useState(false),
    [sidebar, setSidebar] = useState(false),
    [notifications, setNotifications] = useState(false),
    [account, setAccount] = useState(false)
  const navigate = useNavigate(),
    location = useLocation(),
    timer = useRef<ReturnType<typeof setTimeout> | null>(null)
  const t = (s: string) => (locale === 'ar' ? ({} as Record<string, string>)[s] || s : s)
  const notify = useCallback((text: string, error = false) => {
    if (timer.current) clearTimeout(timer.current)
    setToast({ text, error })
    timer.current = setTimeout(() => setToast(null), 6000)
  }, [])
  const refresh = useCallback(async () => {
    try {
      setData(await api<Workspace>('/api/v1/workspace'))
      setFailure('')
    } catch (e) {
      if (e instanceof ApiError && e.status === 401) {
        setUser(null)
        setData(null)
      }
      throw e
    }
  }, [])
  useEffect(() => {
    api<{ user: User; csrf: string }>('/auth/me')
      .then(async (session) => {
        setCsrf(session.csrf)
        setUser(session.user)
        await refresh()
      })
      .catch((e) => {
        if (!(e instanceof ApiError && e.status === 401)) setFailure(e.message)
      })
      .finally(() => setLoading(false))
    return () => {
      if (timer.current) clearTimeout(timer.current)
    }
  }, [refresh])
  useEffect(() => {
    localStorage.setItem('nawa-language', locale)
    document.documentElement.lang = locale
    document.documentElement.dir = locale === 'ar' ? 'rtl' : 'ltr'
  }, [locale])
  useEffect(() => {
    setSidebar(false)
    setNotifications(false)
    setAccount(false)
  }, [location.pathname])
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault()
        setSearch((s) => !s)
      }
    }
    document.addEventListener('keydown', handler)
    return () => document.removeEventListener('keydown', handler)
  }, [])
  useEffect(() => {
    if (!data?.documents.some((d) => ['queued', 'processing'].includes(d.status))) return
    const interval = setInterval(() => {
      refresh().catch((e) => notify(e.message, true))
    }, 2500)
    return () => clearInterval(interval)
  }, [data, refresh, notify])
  async function signedIn(session: { user: User; csrf: string }) {
    setCsrf(session.csrf)
    setUser(session.user)
    setLocale(session.user.preferences?.language || 'en')
    setLoading(true)
    try {
      await refresh()
      navigate('/')
    } catch (e) {
      setFailure((e as Error).message)
    } finally {
      setLoading(false)
    }
  }
  async function logout() {
    try {
      await api('/auth/logout', { method: 'POST' })
      setUser(null)
      setData(null)
      setCsrf('')
      setAccount(false)
    } catch (e) {
      notify((e as Error).message, true)
    }
  }
  const current = navigation.find((n) => n.path === location.pathname)?.label || 'Workspace'
  return (
    <LocaleContext.Provider value={{ locale, setLocale }}>
      {loading ? (
        <div className="app-loading">
          <Logo />
          <div className="loader" />
          <p>{locale === 'ar' ? 'جارٍ الاتصال بمساحة العمل…' : 'Connecting to your workspace…'}</p>
        </div>
      ) : !user ? (
        <Login onLogin={signedIn} failure={failure} />
      ) : !data ? (
        <div className="fatal">
          <Logo />
          <h1>We couldn’t connect to the workspace.</h1>
          <p>{failure || 'The API may still be starting.'}</p>
          <button
            className="btn primary"
            onClick={() => refresh().catch((e) => setFailure(e.message))}
          >
            Retry connection
          </button>
          <button className="btn" onClick={logout}>
            Sign out
          </button>
        </div>
      ) : (
        <WorkspaceContext.Provider
          value={{
            data,
            user,
            refresh,
            notify,
            openCase: setCaseId,
            openDocument: (id, version) => {
              setDocVersion(version)
              setDocId(id)
            },
          }}
        >
          <div className="app-shell">
            <a className="skip-link" href="#main-content">
              {locale === 'ar' ? 'انتقل إلى المحتوى' : 'Skip to content'}
            </a>
            {sidebar && <div className="sidebar-shade" onClick={() => setSidebar(false)} />}
            <aside className={`sidebar ${sidebar ? 'is-open' : ''}`}>
              <Link to="/" className="brand-link" aria-label="UAE AI overview">
                <Logo />
              </Link>
              <div className="workspace-switch">
                <span className="workspace-icon">EO</span>
                <div>
                  <strong>{data.tenant.name}</strong>
                  <small>{locale === 'ar' ? 'مساحة تجريبية' : 'Demo workspace'}</small>
                </div>
                <ChevronDown size={15} />
              </div>
              <div className="nav-group-label">{locale === 'ar' ? 'مساحة العمل' : 'WORKSPACE'}</div>
              <nav aria-label="Main navigation">
                {navigation.slice(0, 7).map((n) => (
                  <NavigationItem
                    key={n.path}
                    item={n}
                    count={n.path === '/procurement' ? data.stats.pending_reviews : undefined}
                  />
                ))}
              </nav>
              <div className="nav-group-label">{locale === 'ar' ? 'الحوكمة' : 'GOVERNANCE'}</div>
              <nav aria-label="Governance">
                {navigation.slice(7).map((n) => (
                  <NavigationItem key={n.path} item={n} />
                ))}
              </nav>
              <div className="sidebar-bottom">
                <div className="workspace-note">
                  <span className="tiny-spark">
                    <Sparkles size={16} />
                  </span>
                  <strong>
                    {locale === 'ar' ? 'ذكاء بمسؤولية' : 'Intelligence, responsibly.'}
                  </strong>
                  <p>
                    {locale === 'ar'
                      ? 'أدلة واضحة. إشراف بشري.'
                      : 'Grounded in evidence. Guided by people.'}
                  </p>
                  <button onClick={() => setHelp(true)}>
                    {locale === 'ar' ? 'استكشف مساحة العمل' : 'Explore your workspace'}
                    <ArrowUpRight size={14} />
                  </button>
                </div>
                <button className="help-button" onClick={() => setHelp(true)}>
                  <HelpCircle size={17} />
                  {locale === 'ar' ? 'المساعدة والوثائق' : 'Help & documentation'}
                  <ArrowUpRight size={14} />
                </button>
                <div className="sidebar-system">
                  <span className="pulse-dot" />
                  {locale === 'ar' ? 'الخدمة المحلية متصلة' : 'Local service connected'}
                  <span>v{appVersion}</span>
                </div>
              </div>
            </aside>
            <div className="main-shell">
              <header className="topbar">
                <div className="breadcrumb">
                  <button
                    className="icon-btn mobile-menu"
                    aria-label="Open navigation"
                    onClick={() => setSidebar(true)}
                  >
                    <Menu size={21} />
                  </button>
                  <span className="desktop-only">
                    {locale === 'ar' ? 'مساحة العمل' : 'Workspace'}
                  </span>
                  <span className="crumb-divider desktop-only">/</span>
                  <strong>
                    <HeaderText text={current} />
                  </strong>
                </div>
                <div className="topbar-actions">
                  <button className="global-search" onClick={() => setSearch(true)}>
                    <Search size={16} />
                    <span>{locale === 'ar' ? 'ابحث عن أي شيء…' : 'Search anything…'}</span>
                    <kbd>⌘ K</kbd>
                  </button>
                  <button
                    className="language-btn"
                    onClick={() => setLocale(locale === 'en' ? 'ar' : 'en')}
                    aria-label="Switch language"
                  >
                    <Globe2 size={16} />
                    {locale === 'en' ? 'العربية' : 'English'}
                  </button>
                  <span className="topbar-divider" />
                  <div className="popover-wrap">
                    <button
                      className="icon-btn notification-button"
                      aria-label="Notifications"
                      aria-expanded={notifications}
                      onClick={() => {
                        setNotifications(!notifications)
                        setAccount(false)
                      }}
                    >
                      <Bell size={19} />
                      {data.stats.pending_reviews > 0 && <i />}
                    </button>
                    {notifications && (
                      <div className="popover notifications">
                        <strong>
                          <HeaderText text="Notifications" />
                        </strong>
                        <p>{data.stats.pending_reviews} cases waiting for independent review.</p>
                        <button
                          onClick={() => {
                            navigate('/procurement?status=awaiting_review')
                            setNotifications(false)
                          }}
                        >
                          Open review queue <ArrowRight size={14} />
                        </button>
                      </div>
                    )}
                  </div>
                  <div className="popover-wrap">
                    <button
                      className="profile-button"
                      aria-label="Account menu"
                      aria-expanded={account}
                      onClick={() => {
                        setAccount(!account)
                        setNotifications(false)
                      }}
                    >
                      <Avatar name={user.name} />
                      <ChevronDown size={13} />
                    </button>
                    {account && (
                      <div className="popover account">
                        <strong>{user.name}</strong>
                        <small>{user.email}</small>
                        <span className="role-label">{user.role}</span>
                        <button onClick={() => navigate('/settings')}>
                          <SettingsIcon size={15} />
                          <HeaderText text="Settings" />
                        </button>
                        <button onClick={logout}>
                          <LogOut size={15} />
                          <HeaderText text="Sign out" />
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              </header>
              <div className="environment-strip">
                <span>
                  <span className="sandbox-dot" />
                  <strong>{locale === 'ar' ? 'مساحة تجريبية' : 'Sandbox workspace'}</strong>
                  <span className="strip-divider">·</span>
                  {locale === 'ar'
                    ? 'بيانات اصطناعية. قرارات المشتريات محاكاة.'
                    : 'Synthetic demonstration data. Procurement outcomes are simulated.'}
                </span>
                <span className="model-indicator">
                  <ShieldCheck size={13} />
                  {data.config.model_mode === 'extractive'
                    ? locale === 'ar'
                      ? 'معالجة محلية'
                      : 'Local processing'
                    : data.config.model_mode === 'ollama'
                      ? locale === 'ar'
                        ? 'نموذج محلي'
                        : 'Local model'
                      : 'Approved hosted route'}
                </span>
              </div>
              <main id="main-content" className="main-content" tabIndex={-1}>
                <Routes>
                  <Route path="/" element={<Dashboard onNewCase={() => setNewCase(true)} />} />
                  <Route
                    path="/procurement"
                    element={<Procurement onNewCase={() => setNewCase(true)} />}
                  />
                  <Route path="/documents" element={<Documents />} />
                  <Route path="/knowledge" element={<Knowledge />} />
                  <Route path="/agents" element={<Agents />} />
                  <Route path="/analytics" element={<Analytics />} />
                  <Route path="/service" element={<ServiceDesk />} />
                  <Route path="/security" element={<Security />} />
                  <Route path="/audit" element={<AuditTrail />} />
                  <Route path="/settings" element={<Settings />} />
                  <Route
                    path="*"
                    element={
                      <Empty
                        title="Page not found"
                        text="Choose a workspace page from the navigation."
                        action={
                          <Link className="btn primary" to="/">
                            Back to overview
                          </Link>
                        }
                      />
                    }
                  />
                </Routes>
              </main>
              <footer className="app-footer">
                <span>
                  UAE<span className="brand-dot"> AI</span> <span>Evidence-led intelligence.</span>
                </span>
                <span>
                  Independent learning platform <span className="footer-dot">·</span> No government
                  affiliation
                </span>
              </footer>
            </div>
          </div>
          {caseId && <CaseDetail id={caseId} onClose={() => setCaseId(null)} />}
          {docId && (
            <DocumentDetail id={docId} initialVersion={docVersion} onClose={() => setDocId(null)} />
          )}
          {newCase && <NewCase onClose={() => setNewCase(false)} />}
          {search && (
            <CommandPalette
              onClose={() => setSearch(false)}
              onCase={(id) => {
                setSearch(false)
                setCaseId(id)
              }}
              onDocument={(id) => {
                setSearch(false)
                setDocVersion(undefined)
                setDocId(id)
              }}
              data={data}
            />
          )}
          {help && (
            <Modal title="Your workspace, explained" onClose={() => setHelp(false)}>
              <div className="help-content">
                <div className="callout">
                  <BookOpen size={22} />
                  <p>
                    Start with a procurement case. Inspect its evidence, run a comparison, then sign
                    in as an independent reviewer to approve the simulation.
                  </p>
                </div>
                <h3>Four things to try</h3>
                <ol>
                  <li>Create a case with two source-linked quotations.</li>
                  <li>Upload a text-based PDF or UTF-8 text file to the evidence library.</li>
                  <li>
                    Ask “What does the procurement policy require?” in the knowledge assistant.
                  </li>
                  <li>Switch to the reviewer demo account to complete the human approval step.</li>
                </ol>
                <h3>Useful shortcuts</h3>
                <p>
                  <kbd>Ctrl / ⌘ K</kbd> Search pages, cases and documents. <kbd>Esc</kbd> Close a
                  dialog.
                </p>
                <p className="muted">
                  Image-only PDFs need OCR outside this reference build. The default assistant
                  returns source passages locally; it does not call a language model. Full source
                  and sequential setup instructions are included in the repository README and
                  docs/implementation/.
                </p>
              </div>
            </Modal>
          )}
        </WorkspaceContext.Provider>
      )}
      {toast && (
        <div
          className={`toast ${toast.error ? 'error' : ''}`}
          role={toast.error ? 'alert' : 'status'}
        >
          <span>{toast.error ? <X size={18} /> : <Check size={18} />}</span>
          {toast.text}
          <button
            className="icon-btn"
            aria-label="Dismiss notification"
            onClick={() => setToast(null)}
          >
            <X size={15} />
          </button>
        </div>
      )}
    </LocaleContext.Provider>
  )
}

function HeaderText({ text }: { text: string }) {
  const { t } = useI18n()
  return <>{t(text)}</>
}
function NavigationItem({ item, count }: { item: (typeof navigation)[number]; count?: number }) {
  const { t } = useI18n()
  return (
    <NavLink
      to={item.path}
      end={item.path === '/'}
      className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
    >
      <item.icon size={18} />
      <span>{t(item.label)}</span>
      {!!count && <span className="nav-count">{count}</span>}
    </NavLink>
  )
}

function Login({
  onLogin,
  failure,
}: {
  onLogin: (s: { user: User; csrf: string }) => Promise<void>
  failure: string
}) {
  const { locale, setLocale, t } = useI18n()
  const [role, setRole] = useState('analyst'),
    [tenant, setTenant] = useState('operations'),
    [busy, setBusy] = useState(false),
    [error, setError] = useState(failure),
    [mode, setMode] = useState('demo')
  useEffect(() => {
    api<{ mode: string }>('/auth/config')
      .then((x) => setMode(x.mode))
      .catch((e) => setError(e.message))
  }, [])
  async function enter(e: React.FormEvent) {
    e.preventDefault()
    setBusy(true)
    setError('')
    try {
      await onLogin(
        await api('/auth/demo', { method: 'POST', body: JSON.stringify({ role, tenant }) }),
      )
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setBusy(false)
    }
  }
  return (
    <div className="login-page">
      <section className="login-story">
        <Logo />
        <div className="login-story-body">
          <div className="login-eyebrow">
            <span />
            UAE SOVEREIGN AGENTIC AI
          </div>
          <h1>
            Intelligence with
            <br />
            purpose<span>.</span>
          </h1>
          <p>
            Built around your evidence. Designed for your people. A unified workspace for
            procurement, knowledge and accountable decisions.
          </p>
          <figure className="login-landmark">
            <img
              src="/uae-login-architecture.png"
              width="1536"
              height="1024"
              alt={
                locale === 'ar'
                  ? 'تصوّر فني لمعمار إماراتي مستوحى من جامع الشيخ زايد عند الغروب'
                  : 'Artistic UAE architectural scene inspired by Sheikh Zayed Grand Mosque at sunset'
              }
              fetchPriority="high"
            />
            <figcaption>
              {locale === 'ar'
                ? 'تراث يلهم المستقبل · تصوّر فني'
                : 'Heritage that inspires tomorrow · AI-created artwork'}
            </figcaption>
          </figure>
          <div className="login-proof">
            <span>
              <ShieldCheck size={17} />
              Permission-scoped
            </span>
            <span>
              <Globe2 size={17} />
              Arabic & English
            </span>
            <span>
              <BookOpen size={17} />
              Source-linked
            </span>
          </div>
        </div>
        <small>Independent learning platform · No government affiliation</small>
      </section>
      <section className="login-form-panel">
        <button
          className="language-btn login-language"
          onClick={() => setLocale(locale === 'en' ? 'ar' : 'en')}
        >
          <Globe2 size={16} />
          {locale === 'en' ? 'العربية' : 'English'}
        </button>
        <div className="login-form">
          <div className="mobile-login-identity">
            <Logo />
            <img
              className="mobile-login-image"
              src="/uae-login-architecture.png"
              width="1536"
              height="1024"
              alt={
                locale === 'ar'
                  ? 'تصوّر فني لمعمار إماراتي عند الغروب'
                  : 'AI-created Emirati architecture at sunset'
              }
            />
          </div>
          <div className="eyebrow">{t('Professional workspace')}</div>
          <h2>
            {t('Welcome back')}
            <span>.</span>
          </h2>
          <p>Explore a working, evidence-led operations platform.</p>
          {mode === 'demo' ? (
            <form onSubmit={enter}>
              <label className="field">
                <span>{t('Organisation')}</span>
                <select value={tenant} onChange={(e) => setTenant(e.target.value)}>
                  <option value="operations">Emirates Operations</option>
                  <option value="research">Research Lab · separate tenant</option>
                </select>
              </label>
              <label className="field">
                <span>{t('Workspace role')}</span>
                <select value={role} onChange={(e) => setRole(e.target.value)}>
                  <option value="analyst">Analyst · prepare & compare</option>
                  <option value="reviewer">Reviewer · independent decisions</option>
                  <option value="requester">Requester · create cases</option>
                  <option value="auditor">Auditor · read-only evidence</option>
                  <option value="admin">Tenant admin · manage workspace</option>
                </select>
              </label>
              {error && (
                <div className="form-error" role="alert">
                  {error}
                </div>
              )}
              <button className="btn primary login-submit" disabled={busy}>
                {busy ? 'Connecting…' : t('Enter workspace')}
                <ArrowRight size={17} />
              </button>
              <div className="login-notice">
                <ShieldCheck size={19} />
                <span>
                  <strong>Local sandbox sign-in</strong>No password is required for these synthetic
                  demo identities. Demo sign-in is disabled in production mode.
                </span>
              </div>
            </form>
          ) : (
            <a className="btn primary login-submit" href="/auth/login">
              {t('Continue with SSO')}
              <ArrowRight size={17} />
            </a>
          )}
          <p className="login-bottom">
            Thoughtfully designed for people.
            <br />
            <strong>Governed by evidence.</strong>
          </p>
        </div>
      </section>
    </div>
  )
}

function CommandPalette({
  onClose,
  onCase,
  onDocument,
  data,
}: {
  onClose: () => void
  onCase: (id: string) => void
  onDocument: (id: string) => void
  data: Workspace
}) {
  const [query, setQuery] = useState(''),
    { t } = useI18n(),
    navigate = useNavigate()
  const q = query.toLowerCase()
  const pages = navigation.filter((n) => n.label.toLowerCase().includes(q)),
    cases = data.cases.filter((c) => (c.title + c.reference).toLowerCase().includes(q)).slice(0, 5),
    docs = data.documents.filter((d) => d.title.toLowerCase().includes(q)).slice(0, 5)
  return (
    <Modal title={t('Search workspace')} onClose={onClose}>
      <div className="search-input large">
        <Search size={19} />
        <input
          autoFocus
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search pages, case references, documents…"
        />
      </div>
      <div className="command-results">
        {pages.length > 0 && (
          <>
            <h4>Pages</h4>
            {pages.map((n) => (
              <button
                key={n.path}
                onClick={() => {
                  navigate(n.path)
                  onClose()
                }}
              >
                <n.icon size={18} />
                <span>{t(n.label)}</span>
                <ArrowUpRight size={14} />
              </button>
            ))}
          </>
        )}
        {cases.length > 0 && (
          <>
            <h4>Procurement cases</h4>
            {cases.map((c) => (
              <button key={c.id} onClick={() => onCase(c.id)}>
                <ShoppingBag size={18} />
                <span>
                  {c.title}
                  <small>{c.reference}</small>
                </span>
                <ArrowUpRight size={14} />
              </button>
            ))}
          </>
        )}
        {docs.length > 0 && (
          <>
            <h4>Evidence library</h4>
            {docs.map((d) => (
              <button key={d.id} onClick={() => onDocument(d.id)}>
                <FileText size={18} />
                <span>{d.title}</span>
                <ArrowUpRight size={14} />
              </button>
            ))}
          </>
        )}
        {!pages.length && !cases.length && !docs.length && <Empty />}
      </div>
    </Modal>
  )
}
