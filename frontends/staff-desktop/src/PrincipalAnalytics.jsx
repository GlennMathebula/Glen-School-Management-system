import {useEffect,useMemo,useState} from "react";
import * as API from "./api";
import {useAuth} from "./auth";
import "./principal-analytics.css";

const COLORS=["#285c94","#efa258","#218b82","#a17cc2","#d46c6c","#5ca9c7","#a9b85b","#748397"];
const money=n=>Number(n||0).toLocaleString("en-ZA",{style:"currency",currency:"ZAR"});
const num=n=>Number(n||0).toLocaleString("en-ZA");
const safeDate=s=>{try{return new Date(s).toLocaleString("en-ZA",{timeZone:"Africa/Johannesburg",dateStyle:"medium",timeStyle:"short"});}catch{return String(s||"");}};

function EmptyChart({message="No records have been captured for this measure."}){
 return <div className="pr-empty"><span aria-hidden="true">◌</span><p>{message}</p></div>;
}

function Donut({title,rows=[],note}){
 const data=rows.filter(r=>Number(r.value)>0);
 const total=data.reduce((n,r)=>n+Number(r.value||0),0);
 let cumulative=0;
 const slice=(item,index)=>{
  const value=Number(item.value||0),start=cumulative/total*360-90;
  cumulative+=value;
  const end=cumulative/total*360-90;
  const point=angle=>{const rad=angle*Math.PI/180;return [100+78*Math.cos(rad),100+78*Math.sin(rad)]};
  if(value===total)return <circle key={index} cx="100" cy="100" r="78" fill={COLORS[index%COLORS.length]}/>;
  const a=point(start),b=point(end),large=end-start>180?1:0;
  return <path key={index} d={`M 100 100 L ${a[0]} ${a[1]} A 78 78 0 ${large} 1 ${b[0]} ${b[1]} Z`} fill={COLORS[index%COLORS.length]} stroke="#fff" strokeWidth="2"><title>{item.label}: ${num(item.value)}</title></path>;
 };
 return <section className="pr-panel" aria-label={title}>
  <div className="pr-panel-title"><h3>{title}</h3>{note&&<small>{note}</small>}</div>
  {!total?<EmptyChart/>:<div className="pr-donut-wrap">
   <svg viewBox="0 0 200 200" role="img" aria-label={`${title}, ${total} recorded entries`}>
    {data.map(slice)}<circle cx="100" cy="100" r="42" fill="#fff"/>
    <text x="100" y="102" dominantBaseline="middle" textAnchor="middle" fontSize="20" fill="#102d4c" fontWeight="bold">{num(total)}</text>
    <text x="100" y="124" textAnchor="middle" fontSize="8.5" fill="#6b7d8f">records</text>
   </svg>
   <div className="pr-legend">{data.map((r,i)=><div className="pr-legend-row" key={`${r.label}-${i}`}>
    <i style={{background:COLORS[i%COLORS.length]}}/><span title={r.label}>{r.label}</span><strong>{num(r.value)}</strong><small>{(100*r.value/total).toFixed(1)}%</small>
   </div>)}</div>
  </div>}
 </section>;
}

function BarGraph({title,rows=[],keyA="applications",keyB="registrations",nameA="Applications",nameB="Registrations",note}){
 const values=rows.slice(0,12);
 const max=Math.max(1,...values.flatMap(r=>[Number(r[keyA]||0),Number(r[keyB]||0)]));
 return <section className="pr-panel pr-wide" aria-label={title}>
  <div className="pr-panel-title"><h3>{title}</h3>{note&&<small>{note}</small>}</div>
  {!values.length?<EmptyChart/>:<>
   <div className="pr-bar-legend"><span><i style={{background:COLORS[0]}}/>{nameA}</span><span><i style={{background:COLORS[1]}}/>{nameB}</span></div>
   <div className="pr-bars" role="img" aria-label={`Comparison chart: ${title}`}>
    {values.map((r,i)=><div className="pr-bar-row" key={`${r.code||r.label}-${i}`}>
      <div className="pr-bar-name" title={r.label||r.code}>{r.label||r.code||"Unknown"}</div>
      <div className="pr-bar-tracks">
       {[[keyA,COLORS[0]],[keyB,COLORS[1]]].map(([key,color])=><div className="pr-bar-track" key={key}>
        <div className="pr-bar-fill" style={{width:`${Math.max(0,Number(r[key]||0)/max)*100}%`,background:color}} title={`${key}: ${num(r[key])}`}/>
        <b>{num(r[key])}</b>
       </div>)}
      </div>
     </div>)}
   </div>
  </>}
 </section>;
}

function Trend({rows=[]}){
 const data=rows.slice(-18);
 const width=760,height=250,left=43,right=21,top=20,bottom=45;
 const max=Math.max(1,...data.flatMap(r=>[Number(r.applications||0),Number(r.registrations||0)]));
 const p=(row,index,key)=>{
  const x=left+(data.length===1?(width-left-right)/2:index/(data.length-1)*(width-left-right));
  const y=height-bottom-Number(row[key]||0)/max*(height-top-bottom);
  return [x,y];
 };
 const path=key=>data.map((r,i)=>`${i?"L":"M"} ${p(r,i,key).join(" ")}`).join(" ");
 return <section className="pr-panel pr-wide">
  <div className="pr-panel-title"><h3>Monthly application & registration trend</h3><small>Recorded creation month, not programme start date</small></div>
  {!data.length?<EmptyChart/>:<div className="pr-trend">
    <svg viewBox={`0 0 ${width} ${height}`} role="img" aria-label="Trend lines for applications and registrations by month">
     {[0,.25,.5,.75,1].map(x=><g key={x}>
       <line x1={left} x2={width-right} y1={height-bottom-(height-top-bottom)*x} y2={height-bottom-(height-top-bottom)*x} stroke="#e3e9ef"/>
       <text x={left-8} y={height-bottom-(height-top-bottom)*x+4} textAnchor="end" fontSize="11" fill="#61768a">{Math.round(max*x)}</text>
      </g>)}
     <path d={path("applications")} stroke={COLORS[0]} strokeWidth="3.5" fill="none" strokeLinejoin="round" strokeLinecap="round"/>
     <path d={path("registrations")} stroke={COLORS[1]} strokeWidth="3.5" fill="none" strokeLinejoin="round" strokeLinecap="round"/>
     {data.map((r,i)=><g key={r.label}>
      <circle cx={p(r,i,"applications")[0]} cy={p(r,i,"applications")[1]} r="4.2" fill={COLORS[0]}><title>{r.label} applications: {r.applications}</title></circle>
      <circle cx={p(r,i,"registrations")[0]} cy={p(r,i,"registrations")[1]} r="4.2" fill={COLORS[1]}><title>{r.label} registrations: {r.registrations}</title></circle>
      {(data.length<10||i%(Math.ceil(data.length/9))===0)&&<text x={p(r,i,"applications")[0]} y={height-17} fontSize="10" textAnchor="middle" fill="#5e7185">{r.label}</text>}
     </g>)}
    </svg>
    <div className="pr-bar-legend"><span><i style={{background:COLORS[0]}}/>Applications</span><span><i style={{background:COLORS[1]}}/>Registrations</span></div>
   </div>}
 </section>;
}

function Stat({label,value,note}){
 return <div className="pr-stat"><span>{label}</span><strong>{value}</strong>{note&&<small>{note}</small>}</div>;
}
function Breakdown({section}){
 const rows=section.rows||[];
 return <details className="pr-details">
  <summary><span>{section.title}</span><small>{rows.length} categories</small></summary>
  <p className="pr-section-note">Unit: {section.unit}</p>
  {rows.length?<div className="pr-table-scroll"><table className="pr-table"><thead><tr><th>Category</th><th>Recorded entries</th>{rows.some(r=>r.amount!==undefined)&&<th>Amount</th>}</tr></thead><tbody>
   {rows.map((r,i)=><tr key={i}><td>{r.label||"Not recorded"}</td><td>{r.value!==undefined?num(r.value):r.applications!==undefined?`${num(r.applications)} applications / ${num(r.registrations)} registrations`:r.active!==undefined?`${num(r.active)} active / ${num(r.total)} total`:num(r.count)}</td>{rows.some(x=>x.amount!==undefined)&&<td>{r.amount!==undefined?money(r.amount):"—"}</td>}</tr>)}
  </tbody></table></div>:<EmptyChart/>}
 </details>;
}

export default function PrincipalAnalytics({token}){
 const auth=useAuth();
 const principal=String(auth.staff?.role_code||"").trim().toUpperCase()==="PRINCIPAL";
 const [cycle,setCycle]=useState("");
 const [refresh,setRefresh]=useState(0);
 const [state,setState]=useState({loading:true,error:"",data:null});
 const [downloading,setDownloading]=useState("");
 const [downloadError,setDownloadError]=useState("");
 useEffect(()=>{
  let live=true;
  if(!principal){setState({loading:false,error:"",data:null});return ()=>{live=false};}
  setState(prev=>({...prev,loading:true,error:""}));
  const params=cycle?`?cycle_code=${encodeURIComponent(cycle)}`:"";
  API.request(`/api/staff/principal/statistics${params}`,{},token)
   .then(data=>{if(live)setState({loading:false,error:"",data:data.data})})
   .catch(error=>{if(live)setState({loading:false,error:error.message||"Statistics could not be loaded.",data:null})});
  return ()=>{live=false};
 },[token,cycle,refresh,principal]);
 const stats=state.data, s=stats?.summary||{}, c=stats?.charts||{};
 const download=async format=>{
  setDownloadError("");setDownloading(format);
  try{
   const q=cycle?`?cycle_code=${encodeURIComponent(cycle)}`:"";
   const safe=cycle?cycle.replace(/[^a-zA-Z0-9-]/g,"_"):"Overall";
   await API.downloadFile(`/api/staff/principal/statistics/${format}${q}`,token,`Glen_Moniques_Principal_${safe}_Report.${format}`);
  }catch(error){setDownloadError(error.message||"The report could not be downloaded.");}
  finally{setDownloading("");}
 };
 if(!principal)return null;
 return <div className="pr-root">
  <div className="pr-hero">
   <div><span className="pr-eyebrow">GLEN MONIQUES | PRINCIPAL ACCESS</span><h2>Institutional Intelligence</h2>
    <p>Decision-ready statistics and confidential, factual management reports.</p></div>
   <div className="pr-controls">
    <label><span>Reporting scope</span><select value={cycle} onChange={e=>setCycle(e.target.value)}>
     <option value="">Overall institution — all cycles</option>
     {(stats?.cycles||[]).map(x=><option key={x.cycle_code} value={x.cycle_code}>{x.cycle_code}{x.cycle_name!==x.cycle_code?` · ${x.cycle_name}`:""}</option>)}
    </select></label>
    <button className="button light" type="button" onClick={()=>setRefresh(n=>n+1)} disabled={state.loading}>Refresh</button>
   </div>
  </div>
  {state.error&&<p className="alert error" role="alert">{state.error}</p>}
  {state.loading&&<p className="pr-loading" role="status">Loading verified institutional statistics…</p>}
  {stats&&!state.loading&&<>
   <div className="pr-reportbar"><div><b>{stats.scope.title}</b><small>Live database snapshot · Updated {safeDate(stats.scope.generated_at)}</small></div>
    <div className="pr-export">
      <button className="button gold" type="button" onClick={()=>download("pdf")} disabled={!!downloading}>{downloading==="pdf"?"Generating PDF…":"Download Full PDF"}</button>
      <button className="button light" type="button" onClick={()=>download("docx")} disabled={!!downloading}>{downloading==="docx"?"Generating Word…":"Download Word Report"}</button>
    </div>
   </div>
   {downloadError&&<p role="alert" className="alert error">{downloadError}</p>}
   <div className="pr-stats">
    <Stat label="Applications received" value={num(s.applications)} note="Application records"/>
    <Stat label="Applications accepted" value={num(s.accepted_applications)} note="Acceptance is not registration"/>
    <Stat label="Registered learners" value={num(s.registrations)} note="Registration records"/>
    <Stat label="Programmes represented" value={num(s.programmes)} note="With applications or registrations"/>
    <Stat label="Active classes & delivery" value={num(s.classes)} note="All recorded class statuses"/>
    <Stat label="Published FISA outcomes" value={num(s.published_fisa_outcomes)} note="Officially published only"/>
    <Stat label="Non-cancelled invoiced" value={money(s.billable_invoice_value)} note="Not an audited receivable"/>
    <Stat label="Unreversed payments" value={money(s.unreversed_payment_value)} note="Recorded payments, not cashbook"/>
   </div>
   <div className="pr-grid">
    <Donut title="Application decisions" rows={c.application_status} note="Applications by decision status"/>
    <Donut title="Applicant gender" rows={c.gender} note="Applicant records, not distinct persons"/>
    <Donut title="Registration status" rows={c.registration_status} note="Actual enrolments only"/>
    <BarGraph title={cycle?"Programmes in this cycle":"Applications and registrations by cycle"}
      rows={cycle?c.courses:c.cycles} note="Separate record counts; do not add together"/>
    {cycle&&<BarGraph title="Programme comparison" rows={c.courses} note="Per programme, selected cycle"/>}
    <Trend rows={c.monthly_trend}/>
    <Donut title="Digital attendance" rows={c.attendance} note="Separate from paper attendance"/>
    <Donut title="Published digital FISA results" rows={c.published_fisa} note="Unpublished outcomes excluded"/>
   </div>
   <div className="pr-reportbar pr-compact"><div><h3>Full institutional fact register</h3><p>Expand each area to inspect the actual recorded breakdown, then download the complete report above.</p></div></div>
   <div className="pr-detail-list">{(stats.sections||[]).map(section=><Breakdown key={section.key} section={section}/>)}</div>
   <section className="pr-method"><h3>How to interpret these facts</h3><ol>{(stats.notes||[]).map((note,i)=><li key={i}>{note}</li>)}</ol></section>
  </>}
 </div>;
}
