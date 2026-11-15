import {useMemo,useState} from 'react';
import * as API from './api';

const money = n => 'R' + Number(n || 0).toLocaleString('en-ZA', {minimumFractionDigits:2,maximumFractionDigits:2});

/** CFO bulk allocation workflow. This is live UI, not a demo. */
export default function FinanceEnhancements({token, sponsors, onAllocated, selectedStudent}) {
  const [modernInvoices, setModernInvoices] = useState([]);
  const [invoiceMessage, setInvoiceMessage] = useState('');
  const [invoiceError, setInvoiceError] = useState('');
  const [invoiceLoading, setInvoiceLoading] = useState(false);
  const [sponsorId, setSponsorId] = useState('');
  const [query, setQuery] = useState('');
  const [students, setStudents] = useState([]);
  const [selected, setSelected] = useState({});
  const [reference, setReference] = useState('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const activeSponsors = (sponsors || []).filter(x => x.status === 'Active');
  const sponsor = activeSponsors.find(x => String(x.sponsor_id) === sponsorId);
  const due = row => Math.max(0, Number(row.effective_due || 0));
  const chosen = useMemo(() => students.filter(x => selected[x.student_number] !== undefined), [students,selected]);
  const allocation = chosen.map(x => ({student_number:x.student_number, amount_covered:Number(selected[x.student_number])}));
  const total = allocation.reduce((v,x) => v + (Number.isFinite(x.amount_covered) ? x.amount_covered : 0),0);
  const load = async () => {
    setLoading(true); setError(''); setMessage('');
    try {
      const r = await API.request('/api/staff/finance/sponsors/eligible-students?limit=500&search='+encodeURIComponent(query), {}, token);
      setStudents((r.students || []).filter(x => x.student_number));
      setSelected({});
    } catch(e) {setError(e.message);} finally {setLoading(false);}
  };
  const toggle = row => {
    setSelected(old => {
      const next = {...old};
      if (next[row.student_number] !== undefined) delete next[row.student_number];
      else if (due(row) > 0) next[row.student_number] = due(row).toFixed(2);
      return next;
    });
  };
  const all = () => setSelected(Object.fromEntries(students.filter(x => due(x) > 0).map(x => [x.student_number,due(x).toFixed(2)])));
  const submit = async () => {
    if (!sponsorId) return setError('Select a sponsor first.');
    if (!allocation.length) return setError('Select at least one learner.');
    for (const a of allocation) {
      const row = chosen.find(x => x.student_number===a.student_number);
      if (!Number.isFinite(a.amount_covered) || a.amount_covered<=0 || a.amount_covered>due(row))
        return setError(`Invalid allocation for ${a.student_number}; maximum ${money(due(row))}.`);
    }
    if (total > Number(sponsor?.remaining_amount || 0)) return setError('Insufficient sponsor budget.');
    if (!window.confirm(`Allocate ${money(total)} to ${allocation.length} students from ${sponsor?.sponsor_name}? This changes financial records.`)) return;
    setLoading(true); setError(''); setMessage('');
    try {
      const r = await API.request('/api/staff/finance/sponsors/bulk-assign', {
        method:'POST',body:JSON.stringify({sponsor_id:sponsorId,allocations:allocation,reference:reference||null})
      },token);
      const result=r.data || {};
      setMessage(`${result.student_count || allocation.length} students allocated ${money(result.total_allocated || total)}. Reload learners to see updated amounts.`);
      setSelected({}); setStudents([]);
      onAllocated?.();
    } catch(e) {setError(e.message);} finally {setLoading(false);}
  };
  const loadModernInvoices = async () => {
    if (!selectedStudent) return;
    setInvoiceLoading(true); setInvoiceError('');
    try {
      const result = await API.request(`/api/staff/finance/students/${encodeURIComponent(selectedStudent)}/modern-invoices`, {}, token);
      setModernInvoices(result.invoices || []);
    } catch(e) {setInvoiceError(e.message);} finally {setInvoiceLoading(false);}
  };
  const cancelModern = async invoice => {
    const reason = window.prompt(`Explain why invoice ${invoice.invoice_number} must be cancelled:`);
    if (!reason || reason.trim().length < 5) return setInvoiceError('A reason of at least five characters is required.');
    if (!window.confirm(`Cancel invoice ${invoice.invoice_number}? This will retain the record and cannot be undone here.`)) return;
    setInvoiceLoading(true); setInvoiceError(''); setInvoiceMessage('');
    try {
      await API.request(`/api/staff/finance/students/${encodeURIComponent(selectedStudent)}/modern-invoices/${encodeURIComponent(invoice.invoice_number)}/cancel`,
        {method:'POST',body:JSON.stringify({reason:reason.trim()})},token);
      setInvoiceMessage(`Invoice ${invoice.invoice_number} cancelled. Tuition fees have not been changed.`);
      await loadModernInvoices();
    } catch(e) {setInvoiceError(e.message);} finally {setInvoiceLoading(false);}
  };
  return <> <section className="panel">
    <div className="panel-head"><h2>Bulk Assign Sponsor</h2><p>Choose learners, review their amount due and allocate partial or full funding.</p></div>
    <div className="panel-body">
      {error && <div className="alert error">{error}</div>}
      {message && <div className="alert success">{message}</div>}
      <div className="form-grid three">
        <label><span>Sponsor</span><select value={sponsorId} onChange={e=>setSponsorId(e.target.value)}>
          <option value="">Select an active sponsor</option>
          {activeSponsors.map(s=><option key={s.sponsor_id} value={s.sponsor_id}>{s.sponsor_name} — available {money(s.remaining_amount)}</option>)}
        </select></label>
        <label><span>Search learners</span><input value={query} onChange={e=>setQuery(e.target.value)} placeholder="Student number, name, qualification"/></label>
        <label><span>Sponsorship reference</span><input value={reference} onChange={e=>setReference(e.target.value)}/></label>
      </div>
      <div className="button-row" style={{margin:'12px 0'}}>
        <button className="button light" onClick={load} disabled={loading}>Load learners (up to 500)</button>
        <button className="button light" onClick={all} disabled={loading||!students.length}>Select all eligible on this list</button>
        <button className="button light" onClick={()=>setSelected({})}>Clear selection</button>
      </div>
      <div className="table-wrap"><table><thead><tr><th>Select</th><th>Student</th><th>Course</th><th>Amount due</th><th>Source</th><th>Sponsor amount</th></tr></thead><tbody>
        {students.map(row=><tr key={row.student_number}>
          <td><input type="checkbox" disabled={due(row)<=0} checked={selected[row.student_number]!==undefined} onChange={()=>toggle(row)}/></td>
          <td>{row.student_number} — {[row.first_name,row.last_name].filter(Boolean).join(' ')}</td>
          <td>{row.course_name||'—'}</td>
          <td>{money(due(row))}</td><td title={row.balance_error||""}>{row.balance_source||"—"}</td>
          <td><input style={{maxWidth:145}} type="number" min="0.01" step="0.01" max={due(row)} disabled={selected[row.student_number]===undefined}
            value={selected[row.student_number]??''} onChange={e=>setSelected(v=>({...v,[row.student_number]:e.target.value}))}/></td>
        </tr>)}
      </tbody></table></div>
      <p><strong>{allocation.length}</strong> selected · To allocate <strong>{money(total)}</strong> · Sponsor remaining after <strong>{money(Number(sponsor?.remaining_amount||0)-total)}</strong></p>
      <button className="button gold" disabled={loading||!sponsorId||!allocation.length} onClick={submit}>Confirm Bulk Sponsor Allocation</button>
      <p style={{marginTop:8,fontSize:12}}>Amount due = active Finance account tuition and other fees, less completed unreversed payments and existing sponsorships. Legacy account is used only where no active Finance account exists. Cancelled invoices do not automatically waive course fees. The backend rechecks all amounts before funding is committed.</p>
    </div>
  </section>
  {selectedStudent && <section className="panel">
    <div className="panel-head"><h2>Modern Finance Invoices — {selectedStudent}</h2><p>Invoices from the finance_invoices ledger. Cancellation preserves invoice history and does not change contracted tuition.</p></div>
    <div className="panel-body">
      {invoiceError && <div className="alert error">{invoiceError}</div>}
      {invoiceMessage && <div className="alert success">{invoiceMessage}</div>}
      <button className="button light" disabled={invoiceLoading} onClick={loadModernInvoices}>Load modern invoices</button>
      <div className="table-wrap"><table><thead><tr><th>Invoice</th><th>Status</th><th>Amount</th><th>Actions</th></tr></thead><tbody>
        {modernInvoices.map(inv=><tr key={inv.invoice_number}><td>{inv.invoice_number}</td><td>{inv.status}</td><td>{money(inv.total_amount)}</td><td>
          {['Draft','Issued'].includes(inv.status) && <button className="button danger" disabled={invoiceLoading} onClick={()=>cancelModern(inv)}>Cancel unpaid</button>}
        </td></tr>)}
      </tbody></table></div>
    </div>
  </section>}
  </>;
}
