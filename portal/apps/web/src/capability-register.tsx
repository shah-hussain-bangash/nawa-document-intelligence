import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useI18n } from './i18n'
import './capability-register.css'

type Entry = [string, string]
type Group = { title: Entry; path: string; items: Entry[] }
const groups: Group[] = [
  { title: ['Quotation and document workflow', 'سير عروض الأسعار والمستندات'], path: '/procurement', items: [
    ['Upload English and Arabic quotations', 'رفع عروض الأسعار العربية والإنجليزية'],
    ['Extract fields from digital and scanned documents', 'استخراج الحقول من المستندات الرقمية والممسوحة'],
    ['Show processing progress, errors and retry options', 'عرض تقدم المعالجة والأخطاء وإعادة المحاولة'],
    ['Show values with source, version and page or line', 'عرض القيم مع المصدر والإصدار والصفحة أو السطر'],
    ['Allow Analyst correction with a reason and save', 'السماح للمحلل بالتصحيح مع ذكر السبب والحفظ'],
    ['Reopen and confirm the saved correction and revision', 'إعادة الفتح والتحقق من التصحيح والإصدار المحفوظ'],
    ['Compare quotations and check totals, currency and VAT', 'مقارنة العروض والتحقق من الإجماليات والعملة والضريبة'],
    ['Allow a separate Reviewer to approve, reject or request changes', 'موافقة مراجع مستقل أو رفضه أو طلبه للتعديلات'],
    ['Preserve decisions, corrections and history', 'حفظ القرارات والتصحيحات والسجل'],
    ['Test the complete workflow in the running portal', 'اختبار سير العمل كاملاً في البوابة الفعلية'],
  ] },
  { title: ['Identity and security', 'الهوية والأمن'], path: '/security', items: [
    ['Company-approved sign-in and trusted HTTPS certificate', 'تسجيل دخول مؤسسي وشهادة HTTPS موثوقة'],
    ['Multi-factor authentication and account recovery', 'المصادقة متعددة العوامل واسترداد الحساب'],
    ['Provision users, change roles, deactivate and review access', 'إنشاء المستخدمين وتعديل الأدوار وإلغاء التفعيل ومراجعة الوصول'],
    ['Server-enforced permissions and separation of duties', 'صلاحيات يفرضها الخادم وفصل المهام'],
    ['Organisation and workspace isolation', 'عزل المؤسسات ومساحات العمل'],
    ['Secure session expiry and logout', 'انتهاء الجلسات وتسجيل الخروج بأمان'],
    ['Secure uploads, secrets and dependency management', 'تأمين الرفع والأسرار وإدارة التبعيات'],
    ['Security testing and remediation', 'اختبار الأمان ومعالجة النتائج'],
  ] },
  { title: ['AI, OCR and governance', 'الذكاء الاصطناعي والتعرف الضوئي والحوكمة'], path: '/knowledge', items: [
    ['Measure Arabic and English OCR and extraction accuracy', 'قياس دقة التعرف الضوئي والاستخراج باللغتين'],
    ['Evaluate answers and citations against reviewed examples', 'تقييم الإجابات والاستشهادات مقابل أمثلة مراجعة'],
    ['Identify insufficient evidence and avoid unsupported answers', 'تحديد الأدلة غير الكافية وتجنب الإجابات غير المدعومة'],
    ['Protect against malicious instructions in documents', 'الحماية من التعليمات الضارة في المستندات'],
    ['Record model, prompt and configuration versions', 'تسجيل إصدارات النماذج والتعليمات والإعدادات'],
    ['Set agent limits, permissions and human approval', 'تحديد حدود الوكلاء وصلاحياتهم والموافقة البشرية'],
    ['Monitor AI quality and report incorrect results', 'مراقبة جودة الذكاء الاصطناعي والإبلاغ عن النتائج الخاطئة'],
  ] },
  { title: ['Data, operations and recovery', 'البيانات والتشغيل والاسترداد'], path: '/security', items: [
    ['Configure approved database and document storage', 'إعداد قاعدة البيانات وتخزين المستندات المعتمدين'],
    ['Protect data with encryption, access and retention controls', 'حماية البيانات بالتشفير وضوابط الوصول والاحتفاظ'],
    ['Back up and restore the database and uploaded documents together', 'نسخ قاعدة البيانات والمستندات المرفوعة واستعادتها معاً'],
    ['Monitor health, failures and performance with alerts', 'مراقبة الصحة والأعطال والأداء مع التنبيهات'],
    ['Define incident response, support and recovery procedures', 'تحديد الاستجابة للحوادث والدعم وإجراءات الاسترداد'],
    ['Prepare staging, production deployment, updates and rollback', 'إعداد بيئة الاختبار والنشر والتحديثات والتراجع'],
    ['Test performance, capacity and outage recovery', 'اختبار الأداء والسعة والتعافي من الأعطال'],
  ] },
  { title: ['Dashboard and production acceptance', 'لوحة التحكم وقبول الإنتاج'], path: '/security', items: [
    ['Connect planned screens to working authorized services', 'ربط الشاشات المخططة بالخدمات العاملة والمصرح بها'],
    ['Complete bilingual, mobile, keyboard and accessibility testing', 'إكمال اختبارات اللغتين والهاتف ولوحة المفاتيح وإمكانية الوصول'],
    ['Test loading, empty, permission, error and recovery states', 'اختبار حالات التحميل والفراغ والصلاحيات والأخطاء والاسترداد'],
    ['Run a controlled pilot with authorized users', 'تنفيذ تجربة محدودة مع مستخدمين مخولين'],
    ['Document supported scope, limitations and operating procedures', 'توثيق النطاق المدعوم والقيود وإجراءات التشغيل'],
    ['Obtain business, technical and security approval', 'الحصول على موافقة الأعمال والتقنية والأمن'],
  ] },
]

export function CapabilityRegister() {
  const { locale } = useI18n()
  const ar = locale === 'ar'
  const [query, setQuery] = useState('')
  const term = query.trim().toLocaleLowerCase()
  let number = 0
  const numbered = groups.map(group => ({ ...group, items: group.items.map(item => ({ item, number: ++number })) }))
  const visible = numbered.map(group => ({ ...group, items: group.items.filter(({ item }) => !term || [...item, ...group.title].some(text => text.toLocaleLowerCase().includes(term))) })).filter(group => group.items.length)
  const count = visible.reduce((total, group) => total + group.items.length, 0)
  return <section className="capability-register" aria-labelledby="capability-register-title">
    <div className="capability-register-heading"><div>
      <span className="readiness-workbench-eyebrow">{ar ? 'سجل قدرات الإنتاج' : 'PRODUCTION CAPABILITY REGISTER'}</span>
      <h2 id="capability-register-title">{ar ? '٣٨ قدرة للتنفيذ والتحقق' : '38 capabilities to build and verify'}</h2>
      <p>{ar ? 'قائمة عمل؛ قد تكون بعض القدرات موجودة جزئياً. يتطلب وضع كل بند تدقيقاً وأدلة في بيئة النشر.' : 'A working register. Some capabilities may already be partly implemented; each needs an evidence-based review in the intended deployment.'}</p>
    </div><label className="readiness-workbench-search"><span>{ar ? 'بحث في السجل' : 'Search the register'}</span><input type="search" value={query} onChange={e => setQuery(e.target.value)} placeholder={ar ? 'مثال: الاسترداد' : 'For example: recovery'} /></label></div>
    <p className="capability-register-count" role="status">{ar ? `${count} من ٣٨ بنداً` : `${count} of 38 items`}</p>
    {visible.map(group => <article className="capability-register-group" key={group.title[0]}><div className="capability-register-group-heading"><h3>{group.title[ar ? 1 : 0]}</h3><Link to={group.path}>{ar ? 'افتح القسم المرتبط' : 'Open related area'} →</Link></div>
      <ol>{group.items.map(({item, number: itemNumber}) => <li key={itemNumber}><span className="capability-register-number">{String(itemNumber).padStart(2, '0')}</span><span>{item[ar ? 1 : 0]}</span><span className="capability-register-status">{ar ? 'يحتاج إلى تحقق' : 'NEEDS VERIFICATION'}</span></li>)}</ol></article>)}
    {!count && <p>{ar ? 'لا توجد نتائج. جرّب كلمة أخرى.' : 'No matching items. Try another search.'}</p>}
    <p className="production-areas-foot">{ar ? 'إدراج القدرة لا يعني أنها منفذة أو معتمدة.' : 'Listing a capability does not mean it is implemented or approved.'}</p>
  </section>
}
