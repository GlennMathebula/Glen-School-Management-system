import {useEffect,useMemo,useState} from "react";
import * as API from "./api";

const q=(o={})=>{
 const p=new URLSearchParams();
 Object.entries(o).forEach(([k,v])=>{
  if(v!==""&&v!==null&&v!==undefined)p.set(k,v);
 });
 const s=p.toString();
 return s?`?${s}`:"";
};

const h=s=>String(s??"")
 .replace(/_/g," ")
 .replace(/\b\w/g,c=>c.toUpperCase());

const v=x=>{
 if(x===null||x===undefined||x==="")return "—";
 if(typeof x==="boolean")return x?"Yes":"No";
 if(typeof x==="object")return JSON.stringify(x);
 return String(x);
};

function Alert({e,m}){
 return e||m?<div className={`alert ${e?"error":"success"}`}>{e||m}</div>:null;
}

function Panel({title,text,children,actions}){
 return <section className="panel">
  <div className="panel-head">
   <div><h2>{title}</h2>{text&&<p>{text}</p>}</div>
   {actions&&<div className="panel-actions">{actions}</div>}
  </div>
  <div className="panel-body">{children}</div>
 </section>;
}

function Tbl({rows=[],cols,act,onRow}){
 const[f,setF]=useState("");
 const rr=useMemo(
  ()=>rows.filter(r=>JSON.stringify(r).toLowerCase().includes(f.toLowerCase())),
  [rows,f]
 );
 if(!rows.length)return <div className="empty">No records available.</div>;
 const kk=cols||Object.keys(rows[0]).filter(k=>typeof rows[0][k]!=="object").slice(0,9);
 return <>
  <div className="table-tools">
   <input placeholder="Filter records..." value={f} onChange={e=>setF(e.target.value)}/>
   <span>{rr.length} of {rows.length}</span>
  </div>
  <div className="table-wrap">
   <table>
    <thead><tr>{kk.map(k=><th key={k}>{h(k)}</th>)}{act&&<th>Actions</th>}</tr></thead>
    <tbody>{rr.map((r,i)=><tr
      key={r.id||r.student_number||r.ticket_number||r.class_code||r.course_code||r.staff_code||i}
      className={onRow?"clickable":""}
      onClick={()=>onRow?.(r)}
    >
     {kk.map(k=><td key={k}>{k.toLowerCase().includes("status")?<span className="badge">{v(r[k])}</span>:v(r[k])}</td>)}
     {act&&<td onClick={e=>e.stopPropagation()}>{act(r)}</td>}
    </tr>)}</tbody>
   </table>
  </div>
 </>;
}

function useGet(path,token){
 const[s,setS]=useState({data:null,e:"",loading:false,n:0});
 useEffect(()=>{
  let on=true;
  if(!path)return;
  setS(x=>({...x,loading:true,e:""}));
  API.request(path,{},token)
   .then(data=>on&&setS(x=>({...x,data,loading:false})))
   .catch(e=>on&&setS(x=>({...x,e:e.message,loading:false})));
  return()=>{on=false};
 },[path,token,s.n]);
 return {...s,refresh:()=>setS(x=>({...x,n:x.n+1}))};
}

async function send(token,path,method,body){
 return API.request(
  path,
  {
   method,
   ...(body===undefined?{}:{body:body instanceof FormData?body:JSON.stringify(body)})
  },
  token
 );
}

const Button=({children,onClick,danger=false,disabled=false})=>
 <button disabled={disabled} className={`button ${danger?"danger":"light"}`} onClick={onClick}>{children}</button>;

const GUIDE_FEES={
 "99573":27500,
 "121792":32500,
 "99669":15000,
 "118728":10500,
 "121164":27500,
 "SP-210401":7500,
 "118741":35000,
 "111142":31500,
 "SP-230801":1250,
 "118709":15500,
 "97542":22500
};


// ============================================================
// QA / WORKPLACE / APPEALS
// ============================================================

export function Compliance({token}){
 const regs=useGet("/api/staff/desktop-v5/registration-options",token);
 const placements=useGet("/api/staff/compliance-records/workplace/placements",token);
 const appeals=useGet("/api/staff/compliance-records/appeals",token);
 const qa=useGet("/api/staff/compliance-records/qa/corrective-actions",token);

 const[st,setSt]=useState({e:"",m:""});
 const[selectedPlacement,setSelectedPlacement]=useState(null);
 const[attendance,setAttendance]=useState([]);
 const[weekly,setWeekly]=useState([]);
 const[supervisorReports,setSupervisorReports]=useState([]);
 const[assessmentOptions,setAssessmentOptions]=useState({marks:[],summatives:[]});

 const[pf,setPf]=useState({
  registration_id:"",
  employer_name:"",
  employer_reg_no:"",
  workplace_address:"",
  supervisor_name:"",
  supervisor_contact:"",
  supervisor_email:"",
  placement_start_date:"",
  placement_end_date:"",
  hours_required:"",
  status:"Planned",
  notes:""
 });

 const[af,setAf]=useState({
  registration_id:"",
  assessment_scope:"Module",
  assessment_id:"",
  lodged_date:"",
  reason:""
 });

 const[qf,setQf]=useState({
  source_type:"Compliance",
  source_reference:"",
  cycle_code:"",
  course_code:"",
  class_code:"",
  finding:"",
  root_cause:"",
  corrective_action:"",
  owner_staff_code:"",
  due_date:"",
  status:"Open",
  evidence_reference:""
 });

 const registrations=regs.data?.registrations||[];

 const change=(setter,key,value)=>setter(x=>({...x,[key]:value}));

 const createPlacement=async()=>{
  try{
   await send(token,"/api/staff/compliance-records/workplace/placements","POST",{
    ...pf,
    employer_reg_no:pf.employer_reg_no||null,
    workplace_address:pf.workplace_address||null,
    supervisor_contact:pf.supervisor_contact||null,
    supervisor_email:pf.supervisor_email||null,
    placement_end_date:pf.placement_end_date||null,
    hours_required:pf.hours_required?Number(pf.hours_required):null,
    notes:pf.notes||null
   });
   setSt({e:"",m:"Workplace placement created."});
   placements.refresh();
  }catch(e){setSt({e:e.message,m:""});}
 };

 const openPlacement=async row=>{
  setSelectedPlacement(row);
  try{
   const[a,b,c]=await Promise.all([
    API.request(`/api/staff/compliance-records/workplace/placements/${row.id}/attendance`,{},token),
    API.request(`/api/staff/compliance-records/workplace/placements/${row.id}/weekly-submissions`,{},token),
    API.request(`/api/staff/compliance-records/workplace/placements/${row.id}/supervisor-reports`,{},token)
   ]);
   setAttendance(a.attendance||[]);
   setWeekly(b.submissions||[]);
   setSupervisorReports(c.reports||[]);
  }catch(e){setSt({e:e.message,m:""});}
 };

 const updatePlacementStatus=async(status)=>{
  if(!selectedPlacement)return;
  try{
   await send(token,`/api/staff/compliance-records/workplace/placements/${selectedPlacement.id}`,"PATCH",{status});
   setSt({e:"",m:`Placement status updated to ${status}.`});
   placements.refresh();
   setSelectedPlacement(x=>x?{...x,status}:x);
  }catch(e){setSt({e:e.message,m:""});}
 };

 const captureWorkplaceAttendance=async()=>{
  if(!selectedPlacement)return;
  const attendance_date=document.getElementById("v5-wa-date")?.value;
  const attendance_status=document.getElementById("v5-wa-status")?.value;
  const sign_in_time=document.getElementById("v5-wa-in")?.value;
  const sign_out_time=document.getElementById("v5-wa-out")?.value;
  const hours=document.getElementById("v5-wa-hours")?.value;
  try{
   await send(token,`/api/staff/compliance-records/workplace/placements/${selectedPlacement.id}/attendance`,"POST",{
    attendance_date,
    attendance_status,
    sign_in_time:sign_in_time||null,
    sign_out_time:sign_out_time||null,
    hours_worked:hours?Number(hours):null,
    supervisor_confirmed:true,
    notes:null
   });
   await openPlacement(selectedPlacement);
   setSt({e:"",m:"Workplace attendance captured."});
  }catch(e){setSt({e:e.message,m:""});}
 };

 const addWeekly=async()=>{
  if(!selectedPlacement)return;
  const start=document.getElementById("v5-week-start")?.value;
  const end=document.getElementById("v5-week-end")?.value;
  const title=document.getElementById("v5-week-title")?.value;
  try{
   await send(token,`/api/staff/compliance-records/workplace/placements/${selectedPlacement.id}/weekly-submissions`,"POST",{
    week_start:start,
    week_end:end,
    submission_type:"Weekly Evidence",
    title,
    evidence_reference:null,
    learner_comment:null,
    status:"Submitted"
   });
   await openPlacement(selectedPlacement);
   setSt({e:"",m:"Weekly workplace evidence recorded."});
  }catch(e){setSt({e:e.message,m:""});}
 };

 const addSupervisorReport=async()=>{
  if(!selectedPlacement)return;
  const name=document.getElementById("v5-supervisor-name")?.value;
  const rating=document.getElementById("v5-supervisor-rating")?.value;
  const comment=document.getElementById("v5-supervisor-comment")?.value;
  try{
   await send(token,`/api/staff/compliance-records/workplace/placements/${selectedPlacement.id}/supervisor-reports`,"POST",{
    report_date:null,
    period_start:null,
    period_end:null,
    overall_rating:rating?Number(rating):null,
    attendance_comment:null,
    performance_comment:comment||null,
    conduct_comment:null,
    competencies_comment:null,
    recommendation:null,
    supervisor_name:name,
    status:"Submitted"
   });
   await openPlacement(selectedPlacement);
   setSt({e:"",m:"Supervisor report recorded."});
  }catch(e){setSt({e:e.message,m:""});}
 };

 const loadAssessmentOptions=async(registration_id)=>{
  change(setAf,"registration_id",registration_id);
  change(setAf,"assessment_id","");
  if(!registration_id){
   setAssessmentOptions({marks:[],summatives:[]});
   return;
  }
  try{
   const x=await API.request(`/api/staff/desktop-v5/assessment-options/${registration_id}`,{},token);
   setAssessmentOptions({marks:x.marks||[],summatives:x.summatives||[]});
  }catch(e){setSt({e:e.message,m:""});}
 };

 const createAppeal=async()=>{
  const body={
   registration_id:af.registration_id,
   assessment_scope:af.assessment_scope,
   mark_id:af.assessment_scope==="Module"?af.assessment_id:null,
   summative_assessment_id:af.assessment_scope==="Module"?null:af.assessment_id,
   lodged_date:af.lodged_date||null,
   reason:af.reason
  };
  try{
   await send(token,"/api/staff/compliance-records/appeals","POST",body);
   appeals.refresh();
   setSt({e:"",m:"Assessment appeal created."});
  }catch(e){setSt({e:e.message,m:""});}
 };

 const updateAppeal=async(row,status)=>{
  try{
   await send(token,`/api/staff/compliance-records/appeals/${row.id}`,"PATCH",{status,outcome:null});
   appeals.refresh();
  }catch(e){setSt({e:e.message,m:""});}
 };

 const createQa=async()=>{
  try{
   await send(token,"/api/staff/compliance-records/qa/corrective-actions","POST",{
    ...qf,
    source_reference:qf.source_reference||null,
    cycle_code:qf.cycle_code||null,
    course_code:qf.course_code||null,
    class_code:qf.class_code||null,
    root_cause:qf.root_cause||null,
    owner_staff_code:qf.owner_staff_code||null,
    due_date:qf.due_date||null,
    evidence_reference:qf.evidence_reference||null
   });
   qa.refresh();
   setSt({e:"",m:"QA corrective action created."});
  }catch(e){setSt({e:e.message,m:""});}
 };

 return <>
  <div className="page-title"><div><span className="eyebrow">QA & Compliance</span><h1>Workplace Experience, Appeals & Corrective Actions</h1><p>Assign learners to workplaces and manage the workplace evidence, appeal and QA workflows.</p></div></div>
  <Alert {...st}/>

  <Panel title="Assign Learner to Workplace">
   <div className="form-grid three">
    <label><span>Learner</span><select value={pf.registration_id} onChange={e=>change(setPf,"registration_id",e.target.value)}><option value="">Select learner</option>{registrations.map(r=><option key={r.registration_id} value={r.registration_id}>{r.student_number} — {r.learner_name} — {r.course_code}</option>)}</select></label>
    <label><span>Employer</span><input value={pf.employer_name} onChange={e=>change(setPf,"employer_name",e.target.value)}/></label>
    <label><span>Employer Reg No.</span><input value={pf.employer_reg_no} onChange={e=>change(setPf,"employer_reg_no",e.target.value)}/></label>
    <label><span>Workplace Address</span><input value={pf.workplace_address} onChange={e=>change(setPf,"workplace_address",e.target.value)}/></label>
    <label><span>Supervisor</span><input value={pf.supervisor_name} onChange={e=>change(setPf,"supervisor_name",e.target.value)}/></label>
    <label><span>Supervisor Contact</span><input value={pf.supervisor_contact} onChange={e=>change(setPf,"supervisor_contact",e.target.value)}/></label>
    <label><span>Supervisor Email</span><input value={pf.supervisor_email} onChange={e=>change(setPf,"supervisor_email",e.target.value)}/></label>
    <label><span>Start Date</span><input type="date" value={pf.placement_start_date} onChange={e=>change(setPf,"placement_start_date",e.target.value)}/></label>
    <label><span>End Date</span><input type="date" value={pf.placement_end_date} onChange={e=>change(setPf,"placement_end_date",e.target.value)}/></label>
    <label><span>Required Hours</span><input type="number" value={pf.hours_required} onChange={e=>change(setPf,"hours_required",e.target.value)}/></label>
    <label><span>Status</span><select value={pf.status} onChange={e=>change(setPf,"status",e.target.value)}>{["Planned","Active","Completed","Terminated","Cancelled"].map(x=><option key={x}>{x}</option>)}</select></label>
    <label><span>Notes</span><input value={pf.notes} onChange={e=>change(setPf,"notes",e.target.value)}/></label>
   </div>
   <button className="button gold" onClick={createPlacement}>Assign Workplace</button>
  </Panel>

  <Panel title="Workplace Placements"><Tbl rows={placements.data?.placements||[]} cols={["student_number","learner_name","course_code","cycle_code","employer_name","supervisor_name","placement_start_date","placement_end_date","status"]} act={r=><Button onClick={()=>openPlacement(r)}>Manage</Button>}/></Panel>

  {selectedPlacement&&<>
   <Panel title={`Placement — ${selectedPlacement.student_number}`} actions={<div className="button-row">{["Planned","Active","Completed","Terminated","Cancelled"].map(x=><Button key={x} onClick={()=>updatePlacementStatus(x)}>{x}</Button>)}</div>}><Tbl rows={[selectedPlacement]}/></Panel>

   <div className="two-col">
    <Panel title="Workplace Attendance">
     <div className="form-grid"><label><span>Date</span><input id="v5-wa-date" type="date"/></label><label><span>Status</span><select id="v5-wa-status">{["Present","Absent","Late","Excused"].map(x=><option key={x}>{x}</option>)}</select></label><label><span>Sign In</span><input id="v5-wa-in" type="time"/></label><label><span>Sign Out</span><input id="v5-wa-out" type="time"/></label><label><span>Hours</span><input id="v5-wa-hours" type="number" step="0.25"/></label></div>
     <button className="button gold" onClick={captureWorkplaceAttendance}>Capture Attendance</button>
     <Tbl rows={attendance}/>
    </Panel>
    <Panel title="Weekly Evidence">
     <div className="form-grid"><label><span>Week Start</span><input id="v5-week-start" type="date"/></label><label><span>Week End</span><input id="v5-week-end" type="date"/></label><label><span>Title</span><input id="v5-week-title"/></label></div>
     <button className="button gold" onClick={addWeekly}>Add Weekly Submission</button>
     <Tbl rows={weekly}/>
    </Panel>
   </div>

   <Panel title="Supervisor Reports">
    <div className="form-grid three"><label><span>Supervisor Name</span><input id="v5-supervisor-name"/></label><label><span>Overall Rating (1–5)</span><input id="v5-supervisor-rating" type="number" min="1" max="5"/></label><label><span>Performance Comment</span><input id="v5-supervisor-comment"/></label></div>
    <button className="button gold" onClick={addSupervisorReport}>Add Supervisor Report</button>
    <Tbl rows={supervisorReports}/>
   </Panel>
  </>}

  <Panel title="Create Assessment Appeal">
   <div className="form-grid three">
    <label><span>Learner</span><select value={af.registration_id} onChange={e=>loadAssessmentOptions(e.target.value)}><option value="">Select learner</option>{registrations.map(r=><option key={r.registration_id} value={r.registration_id}>{r.student_number} — {r.learner_name}</option>)}</select></label>
    <label><span>Assessment Scope</span><select value={af.assessment_scope} onChange={e=>setAf(x=>({...x,assessment_scope:e.target.value,assessment_id:""}))}>{["Module","FISA","EISA"].map(x=><option key={x}>{x}</option>)}</select></label>
    <label><span>Assessment</span><select value={af.assessment_id} onChange={e=>change(setAf,"assessment_id",e.target.value)}><option value="">Select assessment</option>{(af.assessment_scope==="Module"?assessmentOptions.marks:assessmentOptions.summatives.filter(x=>x.assessment_type===af.assessment_scope)).map(x=><option key={x.id} value={x.id}>{af.assessment_scope==="Module"?`${x.module_code} — Attempt ${x.attempt_number} — ${x.result||x.mark||""}`:`${x.assessment_type} — Attempt ${x.attempt_number} — ${x.result||x.mark||""}`}</option>)}</select></label>
    <label><span>Lodged Date</span><input type="date" value={af.lodged_date} onChange={e=>change(setAf,"lodged_date",e.target.value)}/></label>
    <label><span>Reason</span><input value={af.reason} onChange={e=>change(setAf,"reason",e.target.value)}/></label>
   </div>
   <button className="button gold" onClick={createAppeal}>Create Appeal</button>
  </Panel>

  <Panel title="Assessment Appeals"><Tbl rows={appeals.data?.appeals||[]} cols={["appeal_reference","student_number","learner_name","assessment_scope","reason","status","outcome","lodged_date"]} act={r=><div className="button-row"><Button onClick={()=>updateAppeal(r,"Under Review")}>Under Review</Button><Button onClick={()=>updateAppeal(r,"Upheld")}>Upheld</Button><Button danger onClick={()=>updateAppeal(r,"Dismissed")}>Dismiss</Button></div>}/></Panel>

  <Panel title="Create QA Corrective Action">
   <div className="form-grid three">
    <label><span>Source</span><select value={qf.source_type} onChange={e=>change(setQf,"source_type",e.target.value)}>{["Compliance","Assessment","Attendance","Internal QA","Other"].map(x=><option key={x}>{x}</option>)}</select></label>
    <label><span>Source Reference</span><input value={qf.source_reference} onChange={e=>change(setQf,"source_reference",e.target.value)}/></label>
    <label><span>Cycle</span><input value={qf.cycle_code} onChange={e=>change(setQf,"cycle_code",e.target.value)}/></label>
    <label><span>Course</span><input value={qf.course_code} onChange={e=>change(setQf,"course_code",e.target.value)}/></label>
    <label><span>Class</span><input value={qf.class_code} onChange={e=>change(setQf,"class_code",e.target.value)}/></label>
    <label><span>Owner Staff Code</span><input value={qf.owner_staff_code} onChange={e=>change(setQf,"owner_staff_code",e.target.value)}/></label>
    <label><span>Due Date</span><input type="date" value={qf.due_date} onChange={e=>change(setQf,"due_date",e.target.value)}/></label>
    <label><span>Finding</span><input value={qf.finding} onChange={e=>change(setQf,"finding",e.target.value)}/></label>
    <label><span>Root Cause</span><input value={qf.root_cause} onChange={e=>change(setQf,"root_cause",e.target.value)}/></label>
    <label><span>Corrective Action</span><input value={qf.corrective_action} onChange={e=>change(setQf,"corrective_action",e.target.value)}/></label>
   </div>
   <button className="button gold" onClick={createQa}>Create Corrective Action</button>
  </Panel>

  <Panel title="QA Corrective Actions"><Tbl rows={qa.data?.actions||[]} cols={["action_reference","source_type","finding","corrective_action","owner_staff_code","due_date","status"]} act={r=><div className="button-row"><Button onClick={async()=>{await send(token,`/api/staff/compliance-records/qa/corrective-actions/${r.id}`,"PATCH",{status:"In Progress"});qa.refresh()}}>Start</Button><Button onClick={async()=>{await send(token,`/api/staff/compliance-records/qa/corrective-actions/${r.id}`,"PATCH",{status:"Completed",completion_notes:"Completed in Staff Desktop"});qa.refresh()}}>Complete</Button></div>}/></Panel>
 </>;
}


// ============================================================
// ACADEMIC CALENDAR
// ============================================================

export function AcademicCalendar({token}){
 const year=new Date().getFullYear();
 const[calendarYear,setCalendarYear]=useState(year);
 const path="/api/staff/desktop-v5/academic-calendar"+q({calendar_year:calendarYear});
 const list=useGet(path,token);

 const[st,setSt]=useState({e:"",m:""});

 const[f,setF]=useState({
  from_date:"",
  to_date:"",
  day_type:"Training Day",
  description:"",
  is_training_day:true,
  weekdays_only:true,
  overwrite_existing:true
 });

 const saveRange=async()=>{
  if(!f.from_date||!f.to_date){
   setSt({
    e:"Select both From Date and To Date.",
    m:""
   });
   return;
  }

  if(f.to_date<f.from_date){
   setSt({
    e:"To Date cannot be earlier than From Date.",
    m:""
   });
   return;
  }

  try{
   const result=await send(
    token,
    "/api/staff/desktop-v5/academic-calendar/range",
    "POST",
    f
   );

   setSt({
    e:"",
    m:
     `Calendar range saved: ${result.inserted} created, `
     +`${result.updated} updated, ${result.skipped} skipped.`
   });

   const startYear=Number(
    f.from_date.slice(0,4)
   );

   if(startYear&&startYear!==calendarYear){
    setCalendarYear(
     startYear
    );
   }else{
    list.refresh();
   }
  }catch(e){
   setSt({
    e:e.message,
    m:""
   });
  }
 };

 const setPreset=(type,training)=>{
  setF(x=>({
   ...x,
   day_type:type,
   is_training_day:training
  }));
 };

 const deleteDate=async row=>{
  if(!window.confirm(
   `Delete calendar setting for ${row.calendar_date}?`
  )){
   return;
  }

  try{
   await send(
    token,
    `/api/staff/desktop-v5/academic-calendar/${row.id}`,
    "DELETE"
   );

   list.refresh();

   setSt({
    e:"",
    m:`${row.calendar_date} removed from the academic calendar.`
   });
  }catch(e){
   setSt({
    e:e.message,
    m:""
   });
  }
 };

 return <>
  <div className="page-title">
   <div>
    <span className="eyebrow">Academic Administration</span>
    <h1>Academic Calendar</h1>
    <p>Configure training periods, holidays, weekends, institution closures and individual date overrides.</p>
   </div>
  </div>

  <Alert {...st}/>

  <Panel
   title="Configure Date Range"
   text="Use the same From and To date for a single-day override. For normal training periods, leave Weekdays Only enabled."
  >
   <div className="form-grid three">
    <label>
     <span>From Date</span>
     <input
      type="date"
      value={f.from_date}
      onChange={e=>setF({
       ...f,
       from_date:e.target.value,
       to_date:
        f.to_date&&f.to_date>=e.target.value
         ?f.to_date
         :e.target.value
      })}
     />
    </label>

    <label>
     <span>To Date</span>
     <input
      type="date"
      min={f.from_date||undefined}
      value={f.to_date}
      onChange={e=>setF({
       ...f,
       to_date:e.target.value
      })}
     />
    </label>

    <label>
     <span>Day Type</span>
     <select
      value={f.day_type}
      onChange={e=>setF({
       ...f,
       day_type:e.target.value
      })}
     >
      {[
       "Training Day",
       "Weekend",
       "Public Holiday",
       "School Holiday",
       "Special School Holiday",
       "Institution Closure",
       "Make-up Day"
      ].map(x=><option key={x}>{x}</option>)}
     </select>
    </label>

    <label>
     <span>Training Day</span>
     <select
      value={f.is_training_day?"Yes":"No"}
      onChange={e=>setF({
       ...f,
       is_training_day:e.target.value==="Yes"
      })}
     >
      <option>Yes</option>
      <option>No</option>
     </select>
    </label>

    <label>
     <span>Apply To</span>
     <select
      value={f.weekdays_only?"Weekdays Only":"Every Date"}
      onChange={e=>setF({
       ...f,
       weekdays_only:e.target.value==="Weekdays Only"
      })}
     >
      <option>Weekdays Only</option>
      <option>Every Date</option>
     </select>
    </label>

    <label>
     <span>Existing Dates</span>
     <select
      value={f.overwrite_existing?"Overwrite":"Keep Existing"}
      onChange={e=>setF({
       ...f,
       overwrite_existing:e.target.value==="Overwrite"
      })}
     >
      <option>Overwrite</option>
      <option>Keep Existing</option>
     </select>
    </label>

    <label style={{gridColumn:"1 / -1"}}>
     <span>Description</span>
     <input
      value={f.description}
      onChange={e=>setF({
       ...f,
       description:e.target.value
      })}
      placeholder="e.g. Semester 1 training period"
     />
    </label>
   </div>

   <div className="button-row" style={{marginBottom:"14px"}}>
    <Button onClick={()=>setPreset("Training Day",true)}>
     Training Days
    </Button>

    <Button onClick={()=>setPreset("School Holiday",false)}>
     School Holiday
    </Button>

    <Button onClick={()=>setPreset("Public Holiday",false)}>
     Public Holiday
    </Button>

    <Button onClick={()=>setPreset("Institution Closure",false)}>
     Institution Closure
    </Button>
   </div>

   <button
    className="button gold"
    onClick={saveRange}
   >
    Save Date Range
   </button>
  </Panel>

  <Panel
   title="Calendar Year"
   text="Choose the year you want to review below."
  >
   <div className="toolbar-grid">
    <input
     type="number"
     min="2020"
     max="2100"
     value={calendarYear}
     onChange={e=>setCalendarYear(
      Number(e.target.value)
     )}
    />

    <Button onClick={list.refresh}>
     Refresh
    </Button>
   </div>
  </Panel>

  <Panel title={`Academic Calendar Dates — ${calendarYear}`}>
   <Alert e={list.e}/>

   <Tbl
    rows={list.data?.dates||[]}
    cols={[
     "calendar_date",
     "day_type",
     "description",
     "is_training_day",
     "source",
     "is_manual_override"
    ]}
    act={r=>
     <Button
      danger
      onClick={()=>deleteDate(r)}
     >
      Delete
     </Button>
    }
   />
  </Panel>
 </>;
}


// ============================================================
// FINANCE SETUP
// ============================================================

export function FinanceSetup({token}){
 const data=useGet("/api/staff/desktop-v5/finance-setup",token);
 const[st,setSt]=useState({e:"",m:""});
 const[selected,setSelected]=useState("");
 const[f,setF]=useState({tuition_fee:"",ppe_required:false,ppe_fee:"0",is_active:true,effective_from:"2027-01-01",effective_to:""});
 const[fee,setFee]=useState({fee_name:"",fee_code:"",amount:"",is_mandatory:false,is_active:true,effective_from:"2027-01-01",effective_to:"",notes:""});

 const courses=data.data?.courses||[];
 const selectedCourse=courses.find(x=>x.course_code===selected);

 const choose=code=>{
  setSelected(code);
  const row=courses.find(x=>x.course_code===code);
  setF({
   tuition_fee:row?.tuition_fee??GUIDE_FEES[code]??"",
   ppe_required:Boolean(row?.ppe_required),
   ppe_fee:row?.ppe_fee??0,
   is_active:row?.finance_active!==false,
   effective_from:row?.effective_from||"2027-01-01",
   effective_to:row?.effective_to||""
  });
 };

 const loadGuide=()=>{
  if(!selected)return;
  setF(x=>({...x,tuition_fee:GUIDE_FEES[selected]??x.tuition_fee,effective_from:"2027-01-01"}));
 };

 const save=async()=>{
  if(!selected)return;
  try{
   await send(token,`/api/staff/desktop-v5/finance-setup/courses/${encodeURIComponent(selected)}`,"PUT",{
    tuition_fee:Number(f.tuition_fee||0),
    ppe_required:f.ppe_required,
    ppe_fee:Number(f.ppe_fee||0),
    is_active:f.is_active,
    effective_from:f.effective_from||null,
    effective_to:f.effective_to||null
   });
   data.refresh();
   setSt({e:"",m:"Course finance configuration saved."});
  }catch(e){setSt({e:e.message,m:""});}
 };

 const addFee=async()=>{
  if(!selected)return;
  try{
   await send(token,`/api/staff/desktop-v5/finance-setup/courses/${encodeURIComponent(selected)}/fees`,"POST",{
    ...fee,
    amount:Number(fee.amount||0),
    effective_from:fee.effective_from||null,
    effective_to:fee.effective_to||null,
    notes:fee.notes||null
   });
   data.refresh();
   setSt({e:"",m:"Additional fee added."});
  }catch(e){setSt({e:e.message,m:""});}
 };

 const updateRule=async(row,changes)=>{
  try{
   await send(token,`/api/staff/desktop-v5/finance-setup/funding-rules/${encodeURIComponent(row.funding_type)}`,"PUT",{
    student_is_payer:changes.student_is_payer??row.student_is_payer,
    allow_pay_later:changes.allow_pay_later??row.allow_pay_later,
    payfast_enabled:changes.payfast_enabled??row.payfast_enabled,
    notes:row.notes||null,
    is_active:row.is_active!==false
   });
   data.refresh();
  }catch(e){setSt({e:e.message,m:""});}
 };

 const registrationDeposit=selectedCourse?.qualification_type==="Occupational Skills Programme"?500:1500;

 return <>
  <div className="page-title"><div><span className="eyebrow">Finance Administration</span><h1>Course Fees & Funding Rules</h1><p>Configure course fees before learner finance accounts are created.</p></div></div>
  <Alert {...st}/>
  <Panel title="Course Finance Configuration" text="The 2027 guide values are available as defaults; saving is still a deliberate action.">
   <div className="form-grid three">
    <label><span>Course</span><select value={selected} onChange={e=>choose(e.target.value)}><option value="">Select course</option>{courses.map(x=><option key={x.course_code} value={x.course_code}>{x.course_code} — {x.course_name}</option>)}</select></label>
    <label><span>Tuition Fee</span><input type="number" value={f.tuition_fee} onChange={e=>setF({...f,tuition_fee:e.target.value})}/></label>
    <label><span>Registration Deposit (guide)</span><input disabled value={selected?`R${registrationDeposit}`:""}/></label>
    <label><span>PPE Required</span><select value={f.ppe_required?"Yes":"No"} onChange={e=>setF({...f,ppe_required:e.target.value==="Yes"})}><option>No</option><option>Yes</option></select></label>
    <label><span>PPE Fee</span><input type="number" value={f.ppe_fee} onChange={e=>setF({...f,ppe_fee:e.target.value})}/></label>
    <label><span>Effective From</span><input type="date" value={f.effective_from} onChange={e=>setF({...f,effective_from:e.target.value})}/></label>
   </div>
   <div className="button-row"><Button onClick={loadGuide}>Load 2027 Fee Guide</Button><button className="button gold" onClick={save}>Save Course Finance</button></div>
  </Panel>

  {selected&&<Panel title={`Additional Fees — ${selected}`}>
   <div className="form-grid three">
    <label><span>Fee Name</span><input value={fee.fee_name} onChange={e=>setFee({...fee,fee_name:e.target.value})}/></label>
    <label><span>Fee Code</span><input value={fee.fee_code} onChange={e=>setFee({...fee,fee_code:e.target.value})}/></label>
    <label><span>Amount</span><input type="number" value={fee.amount} onChange={e=>setFee({...fee,amount:e.target.value})}/></label>
    <label><span>Mandatory</span><select value={fee.is_mandatory?"Yes":"No"} onChange={e=>setFee({...fee,is_mandatory:e.target.value==="Yes"})}><option>No</option><option>Yes</option></select></label>
    <label><span>Notes</span><input value={fee.notes} onChange={e=>setFee({...fee,notes:e.target.value})}/></label>
   </div>
   <button className="button gold" onClick={addFee}>Add Fee</button>
   <Tbl rows={(data.data?.additional_fees||[]).filter(x=>x.course_code===selected)}/>
  </Panel>}

  <Panel title="Funding Rules"><Tbl rows={data.data?.funding_rules||[]} cols={["funding_type","student_is_payer","allow_pay_later","payfast_enabled","is_active","notes"]} act={r=><div className="button-row"><Button onClick={()=>updateRule(r,{student_is_payer:!r.student_is_payer})}>Toggle Payer</Button><Button onClick={()=>updateRule(r,{allow_pay_later:!r.allow_pay_later})}>Toggle Pay Later</Button><Button onClick={()=>updateRule(r,{payfast_enabled:!r.payfast_enabled})}>Toggle PayFast</Button></div>}/></Panel>
 </>;
}


// ============================================================
// ASSESSMENT ADMIN: FISA SITTINGS + EISA OUTCOMES
// ============================================================

export function AssessmentAdmin({token}){
 const courses=useGet("/api/staff/academic-management/courses",token);
 const cycles=useGet("/api/staff/academic-management/cycles",token);
 const regs=useGet("/api/staff/desktop-v5/registration-options",token);
 const fisa=useGet("/api/staff/desktop-v5/fisa-sittings",token);
 const eisaSittings=useGet("/api/staff/compliance-records/eisa/sittings",token);
 const eisa=useGet("/api/staff/desktop-v5/eisa-results",token);

 const[st,setSt]=useState({e:"",m:""});

 const[selectedFisa,setSelectedFisa]=useState(null);
 const[fisaCandidates,setFisaCandidates]=useState([]);

 const[selectedEisa,setSelectedEisa]=useState(null);
 const[eisaCandidates,setEisaCandidates]=useState([]);

 const[sf,setSf]=useState({
  course_code:"",
  cycle_code:"",
  assessment_date:"",
  reporting_time:"",
  start_time:"",
  end_time:"",
  venue:"",
  assessment_centre:"",
  instructions:"",
  status:"Draft"
 });

 const[se,setSe]=useState({
  course_code:"",
  cycle_code:"",
  assessment_date:"",
  reporting_time:"",
  start_time:"",
  end_time:"",
  venue:"",
  assessment_centre:"",
  capacity:"",
  instructions:"",
  status:"Draft"
 });

 const[ef,setEf]=useState({
  student_number:"",
  attempt_number:1,
  mark:"",
  result:"C",
  assessment_date:"",
  status:"Draft"
 });

 const createFisa=async()=>{
  try{
   await send(
    token,
    "/api/staff/desktop-v5/fisa-sittings",
    "POST",
    sf
   );
   fisa.refresh();
   setSt({e:"",m:"FISA sitting created."});
  }catch(e){
   setSt({e:e.message,m:""});
  }
 };

 const openFisa=async row=>{
  setSelectedFisa(row);
  try{
   const x=await API.request(
    `/api/staff/desktop-v5/fisa-sittings/${row.id}/candidates`,
    {},
    token
   );
   setFisaCandidates(x.candidates||[]);
  }catch(e){
   setSt({e:e.message,m:""});
  }
 };

 const fisaStatus=async(row,status)=>{
  try{
   await send(
    token,
    `/api/staff/desktop-v5/fisa-sittings/${row.id}/status`,
    "PATCH",
    {status}
   );
   fisa.refresh();
   if(selectedFisa?.id===row.id){
    setSelectedFisa(x=>x?{...x,status}:x);
   }
   setSt({e:"",m:`FISA sitting updated to ${status}.`});
  }catch(e){
   setSt({e:e.message,m:""});
  }
 };

 const addFisaCandidate=async()=>{
  if(!selectedFisa)return;
  const registration_id=document.getElementById("v5-fisa-reg")?.value;
  const seat=document.getElementById("v5-fisa-seat")?.value;

  if(!registration_id){
   setSt({e:"Select a learner for the FISA sitting.",m:""});
   return;
  }

  try{
   await send(
    token,
    `/api/staff/desktop-v5/fisa-sittings/${selectedFisa.id}/candidates`,
    "POST",
    {
     registration_id,
     seat_number:seat?Number(seat):null,
     admission_status:"Admitted",
     attendance_status:"Pending",
     notes:null
    }
   );
   await openFisa(selectedFisa);
   setSt({e:"",m:"FISA candidate allocated."});
  }catch(e){
   setSt({e:e.message,m:""});
  }
 };

 const updateFisaCandidate=async(row,changes)=>{
  try{
   await send(
    token,
    `/api/staff/desktop-v5/fisa-candidates/${row.id}`,
    "PATCH",
    {
     seat_number:null,
     admission_status:null,
     attendance_status:null,
     notes:null,
     ...changes
    }
   );
   await openFisa(selectedFisa);
  }catch(e){
   setSt({e:e.message,m:""});
  }
 };

 const createEisa=async()=>{
  try{
   await send(
    token,
    "/api/staff/compliance-records/eisa/sittings",
    "POST",
    {
     ...se,
     cycle_code:se.cycle_code||null,
     reporting_time:se.reporting_time||null,
     assessment_centre:se.assessment_centre||null,
     capacity:se.capacity?Number(se.capacity):null,
     instructions:se.instructions||null
    }
   );
   eisaSittings.refresh();
   setSt({e:"",m:"EISA sitting created."});
  }catch(e){
   setSt({e:e.message,m:""});
  }
 };

 const openEisa=async row=>{
  setSelectedEisa(row);
  try{
   const x=await API.request(
    `/api/staff/compliance-records/eisa/sittings/${row.id}/candidates`,
    {},
    token
   );
   setEisaCandidates(x.candidates||[]);
  }catch(e){
   setSt({e:e.message,m:""});
  }
 };

 const eisaStatus=async(row,status)=>{
  try{
   await send(
    token,
    `/api/staff/compliance-records/eisa/sittings/${row.id}`,
    "PATCH",
    {status}
   );
   eisaSittings.refresh();
   if(selectedEisa?.id===row.id){
    setSelectedEisa(x=>x?{...x,status}:x);
   }
   setSt({e:"",m:`EISA sitting updated to ${status}.`});
  }catch(e){
   setSt({e:e.message,m:""});
  }
 };

 const addEisaCandidate=async()=>{
  if(!selectedEisa)return;
  const registration_id=document.getElementById("v5-eisa-reg")?.value;
  const seat=document.getElementById("v5-eisa-seat")?.value;

  if(!registration_id){
   setSt({e:"Select an EISA-eligible learner.",m:""});
   return;
  }

  try{
   await send(
    token,
    `/api/staff/compliance-records/eisa/sittings/${selectedEisa.id}/candidates`,
    "POST",
    {
     registration_id,
     seat_number:seat?Number(seat):null,
     admission_status:"Admitted",
     attendance_status:"Pending",
     notes:null
    }
   );
   await openEisa(selectedEisa);
   setSt({e:"",m:"EISA candidate allocated."});
  }catch(e){
   setSt({e:e.message,m:""});
  }
 };

 const updateEisaCandidate=async(row,changes)=>{
  try{
   await send(
    token,
    `/api/staff/compliance-records/eisa/candidates/${row.id}`,
    "PATCH",
    {
     seat_number:null,
     admission_status:null,
     attendance_status:null,
     notes:null,
     ...changes
    }
   );
   await openEisa(selectedEisa);
  }catch(e){
   setSt({e:e.message,m:""});
  }
 };

 const captureEisa=async()=>{
  if(!ef.student_number){
   setSt({e:"Select a learner for the EISA outcome.",m:""});
   return;
  }

  try{
   await send(
    token,
    `/api/staff/desktop-v5/eisa-results/${ef.student_number}`,
    "POST",
    {
     attempt_number:Number(ef.attempt_number),
     mark:ef.mark===""?null:Number(ef.mark),
     result:ef.result,
     assessment_date:ef.assessment_date,
     status:ef.status
    }
   );
   eisa.refresh();
   setSt({e:"",m:"EISA outcome saved."});
  }catch(e){
   setSt({e:e.message,m:""});
  }
 };

 return <>
  <div className="page-title">
   <div>
    <span className="eyebrow">Assessment Administration</span>
    <h1>FISA & EISA Administration</h1>
    <p>Create sittings, allocate candidates and seats, track attendance and capture official EISA outcomes.</p>
   </div>
  </div>

  <Alert {...st}/>

  <Panel title="Create FISA Sitting">
   <div className="form-grid three">
    <label><span>Course</span><select value={sf.course_code} onChange={e=>setSf({...sf,course_code:e.target.value})}><option value="">Select course</option>{(courses.data?.courses||[]).map(x=><option key={x.course_code} value={x.course_code}>{x.course_code} — {x.course_name}</option>)}</select></label>
    <label><span>Cycle</span><select value={sf.cycle_code} onChange={e=>setSf({...sf,cycle_code:e.target.value})}><option value="">No cycle</option>{(cycles.data?.cycles||[]).map(x=><option key={x.cycle_code} value={x.cycle_code}>{x.cycle_code}</option>)}</select></label>
    <label><span>Assessment Date</span><input type="date" value={sf.assessment_date} onChange={e=>setSf({...sf,assessment_date:e.target.value})}/></label>
    <label><span>Reporting Time</span><input type="time" value={sf.reporting_time} onChange={e=>setSf({...sf,reporting_time:e.target.value})}/></label>
    <label><span>Start</span><input type="time" value={sf.start_time} onChange={e=>setSf({...sf,start_time:e.target.value})}/></label>
    <label><span>End</span><input type="time" value={sf.end_time} onChange={e=>setSf({...sf,end_time:e.target.value})}/></label>
    <label><span>Venue</span><input value={sf.venue} onChange={e=>setSf({...sf,venue:e.target.value})}/></label>
    <label><span>Assessment Centre</span><input value={sf.assessment_centre} onChange={e=>setSf({...sf,assessment_centre:e.target.value})}/></label>
    <label><span>Status</span><select value={sf.status} onChange={e=>setSf({...sf,status:e.target.value})}>{["Draft","Published","Completed","Cancelled"].map(x=><option key={x}>{x}</option>)}</select></label>
   </div>
   <button className="button gold" onClick={createFisa}>Create FISA Sitting</button>
  </Panel>

  <Panel title="FISA Sittings">
   <Tbl
    rows={fisa.data?.sittings||[]}
    cols={["sitting_reference","course_code","cycle_code","assessment_date","start_time","venue","status","candidate_count"]}
    act={r=><div className="button-row">
     <Button onClick={()=>openFisa(r)}>Candidates</Button>
     <Button onClick={()=>fisaStatus(r,"Published")}>Publish</Button>
     <Button onClick={()=>fisaStatus(r,"Completed")}>Complete</Button>
     <Button danger onClick={()=>fisaStatus(r,"Cancelled")}>Cancel</Button>
    </div>}
   />
  </Panel>

  {selectedFisa&&<Panel title={`FISA Candidates — ${selectedFisa.sitting_reference}`}>
   <div className="form-grid">
    <label><span>Learner</span><select id="v5-fisa-reg"><option value="">Select learner</option>{(regs.data?.registrations||[]).filter(x=>x.course_code===selectedFisa.course_code&&(!selectedFisa.cycle_code||x.cycle_code===selectedFisa.cycle_code)).map(x=><option key={x.registration_id} value={x.registration_id}>{x.student_number} — {x.learner_name}</option>)}</select></label>
    <label><span>Seat Number</span><input id="v5-fisa-seat" type="number" min="1"/></label>
   </div>
   <button className="button gold" onClick={addFisaCandidate}>Add / Update Candidate</button>
   <Tbl
    rows={fisaCandidates}
    cols={["seat_number","student_number","learner_name","admission_status","attendance_status","notes"]}
    act={r=><div className="button-row">
     <Button onClick={()=>updateFisaCandidate(r,{attendance_status:"Present"})}>Present</Button>
     <Button onClick={()=>updateFisaCandidate(r,{attendance_status:"Absent"})}>Absent</Button>
     <Button danger onClick={()=>updateFisaCandidate(r,{admission_status:"Withdrawn"})}>Withdraw</Button>
    </div>}
   />
  </Panel>}

  <Panel title="Create EISA Sitting">
   <div className="form-grid three">
    <label><span>Course</span><select value={se.course_code} onChange={e=>setSe({...se,course_code:e.target.value})}><option value="">Select FISA + EISA course</option>{(courses.data?.courses||[]).filter(x=>x.assessment_type==="FISA_PLUS_EISA").map(x=><option key={x.course_code} value={x.course_code}>{x.course_code} — {x.course_name}</option>)}</select></label>
    <label><span>Cycle</span><select value={se.cycle_code} onChange={e=>setSe({...se,cycle_code:e.target.value})}><option value="">No cycle</option>{(cycles.data?.cycles||[]).map(x=><option key={x.cycle_code} value={x.cycle_code}>{x.cycle_code}</option>)}</select></label>
    <label><span>Assessment Date</span><input type="date" value={se.assessment_date} onChange={e=>setSe({...se,assessment_date:e.target.value})}/></label>
    <label><span>Reporting Time</span><input type="time" value={se.reporting_time} onChange={e=>setSe({...se,reporting_time:e.target.value})}/></label>
    <label><span>Start</span><input type="time" value={se.start_time} onChange={e=>setSe({...se,start_time:e.target.value})}/></label>
    <label><span>End</span><input type="time" value={se.end_time} onChange={e=>setSe({...se,end_time:e.target.value})}/></label>
    <label><span>Venue</span><input value={se.venue} onChange={e=>setSe({...se,venue:e.target.value})}/></label>
    <label><span>Assessment Centre</span><input value={se.assessment_centre} onChange={e=>setSe({...se,assessment_centre:e.target.value})}/></label>
    <label><span>Capacity</span><input type="number" min="1" value={se.capacity} onChange={e=>setSe({...se,capacity:e.target.value})}/></label>
    <label><span>Status</span><select value={se.status} onChange={e=>setSe({...se,status:e.target.value})}>{["Draft","Published","Completed","Cancelled"].map(x=><option key={x}>{x}</option>)}</select></label>
   </div>
   <button className="button gold" onClick={createEisa}>Create EISA Sitting</button>
  </Panel>

  <Panel title="EISA Sittings">
   <Tbl
    rows={eisaSittings.data?.sittings||[]}
    cols={["sitting_reference","course_code","cycle_code","assessment_date","start_time","venue","capacity","status","candidate_count"]}
    act={r=><div className="button-row">
     <Button onClick={()=>openEisa(r)}>Candidates</Button>
     <Button onClick={()=>eisaStatus(r,"Published")}>Publish</Button>
     <Button onClick={()=>eisaStatus(r,"Completed")}>Complete</Button>
     <Button danger onClick={()=>eisaStatus(r,"Cancelled")}>Cancel</Button>
    </div>}
   />
  </Panel>

  {selectedEisa&&<Panel title={`EISA Candidates — ${selectedEisa.sitting_reference}`}>
   <div className="form-grid">
    <label><span>EISA-Eligible Learner</span><select id="v5-eisa-reg"><option value="">Select learner</option>{(regs.data?.registrations||[]).filter(x=>x.eisa_eligible&&x.course_code===selectedEisa.course_code&&(!selectedEisa.cycle_code||x.cycle_code===selectedEisa.cycle_code)).map(x=><option key={x.registration_id} value={x.registration_id}>{x.student_number} — {x.learner_name}</option>)}</select></label>
    <label><span>Seat Number</span><input id="v5-eisa-seat" type="number" min="1"/></label>
   </div>
   <button className="button gold" onClick={addEisaCandidate}>Allocate EISA Candidate</button>
   <Tbl
    rows={eisaCandidates}
    cols={["seat_number","student_number","learner_name","admission_status","attendance_status","notes"]}
    act={r=><div className="button-row">
     <Button onClick={()=>updateEisaCandidate(r,{attendance_status:"Present"})}>Present</Button>
     <Button onClick={()=>updateEisaCandidate(r,{attendance_status:"Absent"})}>Absent</Button>
     <Button danger onClick={()=>updateEisaCandidate(r,{admission_status:"Withdrawn"})}>Withdraw</Button>
    </div>}
   />
  </Panel>}

  <Panel title="Capture Official EISA Outcome">
   <div className="form-grid three">
    <label><span>Learner</span><select value={ef.student_number} onChange={e=>setEf({...ef,student_number:e.target.value})}><option value="">Select EISA learner</option>{(eisa.data?.learners||[]).filter(x=>x.eisa_eligible).map(x=><option key={x.student_number} value={x.student_number}>{x.student_number} — {[x.first_name,x.middle_name,x.last_name].filter(Boolean).join(" ")} — {x.course_code}</option>)}</select></label>
    <label><span>Attempt</span><input type="number" min="1" value={ef.attempt_number} onChange={e=>setEf({...ef,attempt_number:e.target.value})}/></label>
    <label><span>Mark</span><input type="number" min="0" max="100" value={ef.mark} onChange={e=>setEf({...ef,mark:e.target.value})}/></label>
    <label><span>Result</span><select value={ef.result} onChange={e=>setEf({...ef,result:e.target.value})}><option value="C">Competent</option><option value="NYC">Not Yet Competent</option></select></label>
    <label><span>Assessment Date</span><input type="date" value={ef.assessment_date} onChange={e=>setEf({...ef,assessment_date:e.target.value})}/></label>
    <label><span>Status</span><select value={ef.status} onChange={e=>setEf({...ef,status:e.target.value})}><option>Draft</option><option>Published</option></select></label>
   </div>
   <button className="button gold" onClick={captureEisa}>Save EISA Outcome</button>
  </Panel>

  <Panel title="EISA Outcomes">
   <Tbl
    rows={eisa.data?.learners||[]}
    cols={["student_number","course_code","cycle_code","eisa_eligible","attempt_number","mark","result","status","assessment_date"]}
    act={r=>r.assessment_id&&r.status!=="Published"?<button className="button gold" onClick={async()=>{try{await send(token,`/api/staff/desktop-v5/eisa-results/${r.assessment_id}/publish`,"POST");eisa.refresh()}catch(e){setSt({e:e.message,m:""})}}}>Publish</button>:null}
   />
  </Panel>
 </>;
}


// ============================================================
// LEARNING RESOURCES
// ============================================================

export function LearningResources({token}){
 const classes=useGet("/api/staff/facilitator/classes",token);
 const[st,setSt]=useState({e:"",m:""});
 const[classCode,setClassCode]=useState("");
 const[classId,setClassId]=useState("");
 const[modules,setModules]=useState([]);
 const[resources,setResources]=useState([]);
 const[f,setF]=useState({module_id:"",title:"",description:"",content_text:"",external_url:""});

 const chooseClass=async(code)=>{
  setClassCode(code);
  const row=(classes.data?.classes||[]).find(x=>x.class_code===code);
  setClassId(row?.id||row?.class_id||"");
  try{
   const[a,b]=await Promise.all([
    API.request(`/api/staff/desktop-v5/class-modules${q({class_code:code})}`,{},token),
    API.request(`/api/staff/facilitator/classes/${encodeURIComponent(code)}/learning-resources`,{},token)
   ]);
   setModules(a.modules||[]);
   setResources(b.resources||b.data||[]);
  }catch(e){setSt({e:e.message,m:""});}
 };

 const reload=()=>classCode&&chooseClass(classCode);

 const createNote=async()=>{
  try{
   await send(token,"/api/staff/facilitator/learning-resources/note","POST",{
    class_id:classId,
    module_id:f.module_id||null,
    timetable_session_id:null,
    title:f.title,
    description:f.description||null,
    content_text:f.content_text
   });
   await reload();
  }catch(e){setSt({e:e.message,m:""});}
 };

 const createLink=async()=>{
  try{
   await send(token,"/api/staff/facilitator/learning-resources/link","POST",{
    class_id:classId,
    module_id:f.module_id||null,
    timetable_session_id:null,
    title:f.title,
    description:f.description||null,
    external_url:f.external_url
   });
   await reload();
  }catch(e){setSt({e:e.message,m:""});}
 };

 const upload=async()=>{
  const file=document.getElementById("v5-resource-file")?.files?.[0];
  if(!file){setSt({e:"Choose a file first.",m:""});return;}
  const form=new FormData();
  form.append("class_id",classId);
  form.append("title",f.title||file.name);
  form.append("description",f.description||"");
  if(f.module_id)form.append("module_id",f.module_id);
  form.append("file",file);
  try{
   await API.uploadForm("/api/staff/facilitator/learning-resources/file",token,form);
   await reload();
  }catch(e){setSt({e:e.message,m:""});}
 };

 const resourceAction=async(row,action)=>{
  try{
   await send(token,`/api/staff/facilitator/learning-resources/${row.id||row.resource_id}/${action}`,"POST");
   await reload();
  }catch(e){setSt({e:e.message,m:""});}
 };

 return <>
  <div className="page-title"><div><span className="eyebrow">Academic Delivery</span><h1>Learning Resources</h1><p>Create notes, links, upload files, publish/archive resources and generate AI study notes.</p></div></div>
  <Alert {...st}/>
  <Panel title="Class"><select value={classCode} onChange={e=>chooseClass(e.target.value)}><option value="">Select class</option>{(classes.data?.classes||[]).map(x=><option key={x.class_code} value={x.class_code}>{x.class_code} — {x.class_name||x.course_code}</option>)}</select></Panel>
  {classCode&&<>
   <Panel title="Create Resource">
    <div className="form-grid three">
     <label><span>Module</span><select value={f.module_id} onChange={e=>setF({...f,module_id:e.target.value})}><option value="">General</option>{modules.map(x=><option key={x.module_id} value={x.module_id}>{x.module_code} — {x.module_name}</option>)}</select></label>
     <label><span>Title</span><input value={f.title} onChange={e=>setF({...f,title:e.target.value})}/></label>
     <label><span>Description</span><input value={f.description} onChange={e=>setF({...f,description:e.target.value})}/></label>
     <label><span>Note Content</span><textarea value={f.content_text} onChange={e=>setF({...f,content_text:e.target.value})}/></label>
     <label><span>External URL</span><input value={f.external_url} onChange={e=>setF({...f,external_url:e.target.value})}/></label>
     <label><span>File</span><input id="v5-resource-file" type="file"/></label>
    </div>
    <div className="button-row"><button className="button gold" onClick={createNote}>Create Note</button><Button onClick={createLink}>Create Link</Button><Button onClick={upload}>Upload File</Button></div>
   </Panel>
   <Panel title="Class Resources"><Tbl rows={resources} act={r=><div className="button-row"><Button onClick={()=>resourceAction(r,"publish")}>Publish</Button><Button onClick={()=>resourceAction(r,"archive")}>Archive</Button><Button onClick={()=>resourceAction(r,"restore")}>Restore</Button><button className="button gold" onClick={()=>resourceAction(r,"generate-ai-notes")}>AI Notes</button></div>}/></Panel>
  </>}
 </>;
}


// ============================================================
// FACILITATOR DELIVERY
// ============================================================

export function Delivery({token}){
 const classes=useGet("/api/staff/facilitator/classes",token);
 const timetable=useGet("/api/staff/facilitator/timetable",token);
 const attendance=useGet("/api/staff/facilitator/attendance",token);
 const[st,setSt]=useState({e:"",m:""});
 const[selectedClass,setSelectedClass]=useState("");
 const[learners,setLearners]=useState([]);
 const[selectedSession,setSelectedSession]=useState(null);
 const[roster,setRoster]=useState(null);
 const[capture,setCapture]=useState({});

 const openClass=async code=>{
  setSelectedClass(code);
  try{
   const x=await API.request(`/api/staff/facilitator/classes/${encodeURIComponent(code)}/learners`,{},token);
   setLearners(x.learners||x.data||[]);
  }catch(e){setSt({e:e.message,m:""});}
 };

 const createAttendance=async row=>{
  try{
   const x=await send(token,`/api/staff/facilitator/attendance/sessions/${row.timetable_session_id||row.id}`,"POST");
   const session=x.attendance_session||x.data||x;
   setSelectedSession(session);
   const d=await API.request(`/api/staff/facilitator/attendance/${session.id||session.attendance_session_id}`,{},token);
   setRoster(d.data||d);
   setCapture({});
   attendance.refresh();
  }catch(e){setSt({e:e.message,m:""});}
 };

 const saveAttendance=async()=>{
  const sessionId=selectedSession?.id||selectedSession?.attendance_session_id||roster?.attendance_session?.id;
  const rows=roster?.learners||roster?.records||[];
  try{
   await send(token,`/api/staff/facilitator/attendance/${sessionId}`,"PUT",{
    records:rows.map(r=>({
     registration_id:r.registration_id,
     attendance_status:capture[r.registration_id]||r.attendance_status||"Present",
     minutes_late:null,
     notes:null
    }))
   });
   setSt({e:"",m:"Attendance saved."});
  }catch(e){setSt({e:e.message,m:""});}
 };

 const submitAttendance=async()=>{
  const sessionId=selectedSession?.id||selectedSession?.attendance_session_id||roster?.attendance_session?.id;
  try{
   await send(token,`/api/staff/facilitator/attendance/${sessionId}/submit`,"POST");
   setSt({e:"",m:"Attendance submitted for Admin confirmation."});
   attendance.refresh();
  }catch(e){setSt({e:e.message,m:""});}
 };

 return <>
  <div className="page-title"><div><span className="eyebrow">Academic Delivery</span><h1>Classes, Timetable & Attendance</h1><p>Operational Facilitator workspace.</p></div></div>
  <Alert {...st}/>
  <Panel title="Assigned Classes"><Tbl rows={classes.data?.classes||[]} act={r=><Button onClick={()=>openClass(r.class_code)}>Open Class</Button>}/></Panel>
  {selectedClass&&<Panel title={`Learners — ${selectedClass}`}><Tbl rows={learners}/></Panel>}
  <Panel title="My Timetable"><Tbl rows={timetable.data?.sessions||timetable.data?.timetable||[]} act={r=><div className="button-row"><button className="button gold" onClick={()=>createAttendance(r)}>Take Attendance</button><Button onClick={async()=>{await send(token,`/api/staff/facilitator/timetable/${r.timetable_session_id||r.id}/notify-learners`,"POST");setSt({e:"",m:"Learners notified."})}}>Notify Learners</Button><Button onClick={async()=>{await send(token,`/api/staff/facilitator/timetable/${r.timetable_session_id||r.id}/sync-calendar`,"POST");setSt({e:"",m:"Session synced to Google Calendar."})}}>Sync Calendar</Button></div>}/></Panel>
  {roster&&<Panel title="Attendance Capture">
   <div className="table-wrap"><table><thead><tr><th>Student</th><th>Name</th><th>Status</th></tr></thead><tbody>{(roster.learners||roster.records||[]).map(r=><tr key={r.registration_id}><td>{r.student_number}</td><td>{r.learner_name||[r.first_name,r.middle_name,r.last_name].filter(Boolean).join(" ")}</td><td><select value={capture[r.registration_id]||r.attendance_status||"Present"} onChange={e=>setCapture(x=>({...x,[r.registration_id]:e.target.value}))}>{["Present","Absent","Late","Excused"].map(x=><option key={x}>{x}</option>)}</select></td></tr>)}</tbody></table></div>
   <div className="button-row"><button className="button gold" onClick={saveAttendance}>Save Attendance</button><Button onClick={submitAttendance}>Submit for Confirmation</Button></div>
  </Panel>}
  <Panel title="Attendance History"><Tbl rows={attendance.data?.attendance||attendance.data?.sessions||[]}/></Panel>
 </>;
}


// ============================================================
// ASSESSOR / MODERATOR
// ============================================================

export function Assessments({token}){
 const assessorModules=useGet("/api/staff/assessment/assessor/module-queue",token);
 const assessorSummative=useGet("/api/staff/assessment/assessor/summative-queue",token);
 const moderatorModules=useGet("/api/staff/assessment/moderator/module-queue",token);
 const moderatorSummative=useGet("/api/staff/assessment/moderator/summative-queue",token);
 const[st,setSt]=useState({e:"",m:""});

 const captureModule=async r=>{
  const mark=document.getElementById(`mark-${r.module_registration_id}`)?.value;
  const result=document.getElementById(`result-${r.module_registration_id}`)?.value;
  try{
   const x=await send(token,"/api/staff/assessment/assessor/module-marks","POST",{
    module_registration_id:r.module_registration_id,
    attempt_number:1,
    mark:mark===""?null:Number(mark),
    grade:null,
    semester:null,
    academic_year:new Date().getFullYear(),
    result:result||null
   });
   const id=x.data?.id||x.id;
   if(id)await send(token,`/api/staff/assessment/assessor/module-marks/${id}/submit`,"POST");
   assessorModules.refresh();
   moderatorModules.refresh();
   setSt({e:"",m:"Module result captured and submitted."});
  }catch(e){setSt({e:e.message,m:""});}
 };

 const captureFisa=async r=>{
  const mark=document.getElementById(`fisa-mark-${r.registration_id}`)?.value;
  const result=document.getElementById(`fisa-result-${r.registration_id}`)?.value;
  try{
   const x=await send(token,"/api/staff/assessment/assessor/summative","POST",{
    registration_id:r.registration_id,
    assessment_type:"FISA",
    attempt_number:1,
    mark:mark===""?null:Number(mark),
    assessment_date:new Date().toISOString().slice(0,10),
    result:result||null
   });
   const id=x.data?.id||x.id;
   if(id)await send(token,`/api/staff/assessment/assessor/summative/${id}/submit`,"POST");
   assessorSummative.refresh();
   moderatorSummative.refresh();
   setSt({e:"",m:"FISA result captured and submitted."});
  }catch(e){setSt({e:e.message,m:""});}
 };

 const moderate=async(type,row,action)=>{
  const id=row.id||row.mark_id||row.assessment_id;
  const base=type==="module"?`/api/staff/assessment/moderator/module-marks/${id}`:`/api/staff/assessment/moderator/summative/${id}`;
  try{
   if(action==="moderate"){
    await send(token,`${base}/moderate`,"POST");
   }else{
    const reason=document.getElementById(`return-${id}`)?.value||"Returned for correction";
    await send(token,`${base}/return`,"POST",{return_reason:reason});
   }
   moderatorModules.refresh();
   moderatorSummative.refresh();
  }catch(e){setSt({e:e.message,m:""});}
 };

 return <>
  <div className="page-title"><div><span className="eyebrow">Assessment</span><h1>Assessment & Moderation</h1><p>Capture module/FISA results, submit for moderation, approve or return.</p></div></div>
  <Alert {...st}/>
  <Panel title="Assessor — Module Queue"><Tbl rows={assessorModules.data?.data||[]} act={r=><div className="button-row"><input id={`mark-${r.module_registration_id}`} type="number" min="0" max="100" placeholder="Mark" style={{width:"90px"}}/><select id={`result-${r.module_registration_id}`}><option value="C">C</option><option value="NYC">NYC</option></select><button className="button gold" onClick={()=>captureModule(r)}>Capture & Submit</button></div>}/></Panel>
  <Panel title="Assessor — FISA Queue"><Tbl rows={assessorSummative.data?.data||[]} act={r=><div className="button-row"><input id={`fisa-mark-${r.registration_id}`} type="number" min="0" max="100" placeholder="Mark" style={{width:"90px"}}/><select id={`fisa-result-${r.registration_id}`}><option value="C">C</option><option value="NYC">NYC</option></select><button className="button gold" onClick={()=>captureFisa(r)}>Capture & Submit</button></div>}/></Panel>
  <Panel title="Moderator — Module Queue"><Tbl rows={moderatorModules.data?.data||[]} act={r=><div className="button-row"><button className="button gold" onClick={()=>moderate("module",r,"moderate")}>Approve</button><input id={`return-${r.id||r.mark_id}`} placeholder="Return reason"/><Button danger onClick={()=>moderate("module",r,"return")}>Return</Button></div>}/></Panel>
  <Panel title="Moderator — FISA Queue"><Tbl rows={moderatorSummative.data?.data||[]} act={r=><div className="button-row"><button className="button gold" onClick={()=>moderate("summative",r,"moderate")}>Approve</button><input id={`return-${r.id||r.assessment_id}`} placeholder="Return reason"/><Button danger onClick={()=>moderate("summative",r,"return")}>Return</Button></div>}/></Panel>
 </>;
}


// ============================================================
// HR OPERATIONS
// ============================================================

export function HR({token}){
 const dashboard=useGet("/api/staff/hr/dashboard",token);
 const vacancies=useGet("/api/staff/hr/vacancies",token);
 const applications=useGet("/api/staff/hr/applications",token);
 const employees=useGet("/api/staff/hr/employees",token);

 const[st,setSt]=useState({e:"",m:""});
 const[selectedApp,setSelectedApp]=useState(null);
 const[appDetail,setAppDetail]=useState(null);

 const[vf,setVf]=useState({
  job_title:"",
  department:"",
  location:"",
  employment_type:"Permanent",
  positions_available:1,
  description:"",
  responsibilities:"",
  minimum_requirements:"",
  preferred_requirements:"",
  required_documents:[],
  opening_date:"",
  closing_date:""
 });

 const[interview,setInterview]=useState({
  scheduled_at:"",
  mode:"Physical",
  venue:"",
  panel:"",
  notes:""
 });

 const[offer,setOffer]=useState({
  start_date:"",
  employment_type:"Permanent",
  offer_summary:""
 });

 const createVacancy=async()=>{
  try{
   await send(token,"/api/staff/hr/vacancies","POST",{
    ...vf,
    department:vf.department||null,
    location:vf.location||null,
    responsibilities:vf.responsibilities||null,
    preferred_requirements:vf.preferred_requirements||null,
    opening_date:vf.opening_date||null
   });
   vacancies.refresh();
   dashboard.refresh();
   setSt({e:"",m:"Vacancy created."});
  }catch(e){setSt({e:e.message,m:""});}
 };

 const appAction=async(row,status)=>{
  try{
   await send(
    token,
    `/api/staff/hr/applications/${row.id||row.application_id}/status`,
    "PATCH",
    {status,reason:null}
   );
   applications.refresh();
   dashboard.refresh();
   if(selectedApp)await openApplication(row);
   setSt({e:"",m:`Application status updated to ${status}.`});
  }catch(e){setSt({e:e.message,m:""});}
 };

 const openApplication=async row=>{
  const id=row.id||row.application_id;
  setSelectedApp(row);
  try{
   const x=await API.request(
    `/api/staff/hr/applications/${id}`,
    {},
    token
   );
   setAppDetail(x.data||x);
   setSt({e:"",m:""});
  }catch(e){setSt({e:e.message,m:""});}
 };

 const scheduleInterview=async()=>{
  const id=selectedApp?.id||selectedApp?.application_id;
  if(!id)return;
  try{
   await send(
    token,
    `/api/staff/hr/applications/${id}/interviews`,
    "POST",
    {
     scheduled_at:new Date(interview.scheduled_at).toISOString(),
     mode:interview.mode,
     venue:interview.venue||null,
     panel:interview.panel||null,
     notes:interview.notes||null
    }
   );
   applications.refresh();
   dashboard.refresh();
   await openApplication(selectedApp);
   setSt({e:"",m:"Interview scheduled."});
  }catch(e){setSt({e:e.message,m:""});}
 };

 const makeOffer=async()=>{
  const id=selectedApp?.id||selectedApp?.application_id;
  if(!id)return;
  try{
   await send(
    token,
    `/api/staff/hr/applications/${id}/offers`,
    "POST",
    {
     start_date:offer.start_date||null,
     employment_type:offer.employment_type||null,
     offer_summary:offer.offer_summary
    }
   );
   applications.refresh();
   dashboard.refresh();
   await openApplication(selectedApp);
   setSt({e:"",m:"Job offer created."});
  }catch(e){setSt({e:e.message,m:""});}
 };

 const hire=async()=>{
  const id=selectedApp?.id||selectedApp?.application_id;
  if(!id)return;
  if(!offer.start_date){
   setSt({e:"Enter the employee start date before hiring.",m:""});
   return;
  }
  try{
   await send(
    token,
    `/api/staff/hr/applications/${id}/hire`,
    "POST",
    {
     start_date:offer.start_date,
     employment_type:offer.employment_type||null
    }
   );
   applications.refresh();
   employees.refresh();
   dashboard.refresh();
   await openApplication(selectedApp);
   setSt({e:"",m:"Applicant hired and employee record created."});
  }catch(e){setSt({e:e.message,m:""});}
 };

 const reviewDocument=async(doc,status)=>{
  const id=doc.id||doc.document_id;
  try{
   await send(
    token,
    `/api/staff/hr/documents/${id}/review`,
    "PATCH",
    {
     review_status:status,
     review_notes:null
    }
   );
   await openApplication(selectedApp);
  }catch(e){setSt({e:e.message,m:""});}
 };

 return <>
  <div className="page-title">
   <div>
    <span className="eyebrow">Human Resources</span>
    <h1>HR & Recruitment</h1>
    <p>Create vacancies, review applications and documents, schedule interviews, make offers and hire employees.</p>
   </div>
  </div>

  <Alert {...st}/>

  <Panel title="HR Dashboard">
   <Tbl rows={[dashboard.data?.data||dashboard.data||{}]}/>
  </Panel>

  <Panel title="Create Vacancy">
   <div className="form-grid three">
    <label><span>Job Title</span><input value={vf.job_title} onChange={e=>setVf({...vf,job_title:e.target.value})}/></label>
    <label><span>Department</span><input value={vf.department} onChange={e=>setVf({...vf,department:e.target.value})}/></label>
    <label><span>Location</span><input value={vf.location} onChange={e=>setVf({...vf,location:e.target.value})}/></label>
    <label><span>Employment Type</span><input value={vf.employment_type} onChange={e=>setVf({...vf,employment_type:e.target.value})}/></label>
    <label><span>Positions</span><input type="number" min="1" value={vf.positions_available} onChange={e=>setVf({...vf,positions_available:Number(e.target.value)})}/></label>
    <label><span>Opening Date</span><input type="date" value={vf.opening_date} onChange={e=>setVf({...vf,opening_date:e.target.value})}/></label>
    <label><span>Closing Date</span><input type="date" value={vf.closing_date} onChange={e=>setVf({...vf,closing_date:e.target.value})}/></label>
    <label><span>Description</span><textarea value={vf.description} onChange={e=>setVf({...vf,description:e.target.value})}/></label>
    <label><span>Responsibilities</span><textarea value={vf.responsibilities} onChange={e=>setVf({...vf,responsibilities:e.target.value})}/></label>
    <label><span>Minimum Requirements</span><textarea value={vf.minimum_requirements} onChange={e=>setVf({...vf,minimum_requirements:e.target.value})}/></label>
    <label><span>Preferred Requirements</span><textarea value={vf.preferred_requirements} onChange={e=>setVf({...vf,preferred_requirements:e.target.value})}/></label>
   </div>
   <button className="button gold" onClick={createVacancy}>Create Vacancy</button>
  </Panel>

  <Panel title="Vacancies">
   <Tbl
    rows={vacancies.data?.vacancies||[]}
    act={r=><div className="button-row">
     <Button onClick={async()=>{try{await send(token,`/api/staff/hr/vacancies/${r.id}/publish`,"POST");vacancies.refresh();dashboard.refresh()}catch(e){setSt({e:e.message,m:""})}}}>Publish</Button>
     <Button danger onClick={async()=>{try{await send(token,`/api/staff/hr/vacancies/${r.id}/close`,"POST");vacancies.refresh();dashboard.refresh()}catch(e){setSt({e:e.message,m:""})}}}>Close</Button>
    </div>}
   />
  </Panel>

  <Panel title="Job Applications">
   <Tbl
    rows={applications.data?.applications||[]}
    act={r=><div className="button-row">
     <Button onClick={()=>openApplication(r)}>Open</Button>
     <Button onClick={()=>appAction(r,"Under Review")}>Under Review</Button>
     <Button onClick={()=>appAction(r,"Shortlisted")}>Shortlist</Button>
     <Button danger onClick={()=>appAction(r,"Rejected")}>Reject</Button>
    </div>}
   />
  </Panel>

  {selectedApp&&<>
   <Panel title={`Application — ${selectedApp.application_number||selectedApp.id}`}>
    <Tbl rows={[appDetail?.application||appDetail||selectedApp]}/>
   </Panel>

   <Panel title="Applicant Documents">
    <Tbl
     rows={appDetail?.documents||[]}
     act={r=><div className="button-row">
      <Button onClick={()=>API.downloadFile(`/api/staff/hr/documents/${r.id||r.document_id}/download`,token,r.original_filename||"HR_Document")}>View / Download</Button>
      <Button onClick={()=>reviewDocument(r,"Accepted")}>Accept</Button>
      <Button danger onClick={()=>reviewDocument(r,"Rejected")}>Reject</Button>
     </div>}
    />
   </Panel>

   <div className="two-col">
    <Panel title="Schedule Interview">
     <div className="form-grid">
      <label><span>Date & Time</span><input type="datetime-local" value={interview.scheduled_at} onChange={e=>setInterview({...interview,scheduled_at:e.target.value})}/></label>
      <label><span>Mode</span><select value={interview.mode} onChange={e=>setInterview({...interview,mode:e.target.value})}><option>Physical</option><option>Online</option><option>Telephone</option></select></label>
      <label><span>Venue / Link</span><input value={interview.venue} onChange={e=>setInterview({...interview,venue:e.target.value})}/></label>
      <label><span>Panel</span><input value={interview.panel} onChange={e=>setInterview({...interview,panel:e.target.value})}/></label>
      <label><span>Notes</span><textarea value={interview.notes} onChange={e=>setInterview({...interview,notes:e.target.value})}/></label>
     </div>
     <button className="button gold" onClick={scheduleInterview}>Schedule Interview</button>
     <Tbl rows={appDetail?.interviews||[]}/>
    </Panel>

    <Panel title="Offer & Hire">
     <div className="form-grid">
      <label><span>Start Date</span><input type="date" value={offer.start_date} onChange={e=>setOffer({...offer,start_date:e.target.value})}/></label>
      <label><span>Employment Type</span><input value={offer.employment_type} onChange={e=>setOffer({...offer,employment_type:e.target.value})}/></label>
      <label><span>Offer Summary</span><textarea value={offer.offer_summary} onChange={e=>setOffer({...offer,offer_summary:e.target.value})}/></label>
     </div>
     <div className="button-row">
      <button className="button gold" onClick={makeOffer}>Create Offer</button>
      <Button onClick={hire}>Hire Applicant</Button>
     </div>
     <Tbl rows={appDetail?.offers||[]}/>
    </Panel>
   </div>
  </>}

  <Panel title="Employees">
   <Tbl rows={employees.data?.employees||[]}/>
  </Panel>
 </>;
}


// ============================================================
// PRINCIPAL
// ============================================================

export function Principal({token}){
 const overview=useGet("/api/staff/principal/overview",token);
 const staff=useGet("/api/staff/principal/staff",token);
 const[st,setSt]=useState({e:"",m:""});
 const[selected,setSelected]=useState(null);
 const[contact,setContact]=useState({email:"",cell_number:"",phone_number:""});
 const[credentials,setCredentials]=useState({temporary_password:"",temporary_pin:""});

 const select=row=>{
  setSelected(row);
  setContact({email:row.email||"",cell_number:row.cell_number||"",phone_number:row.phone_number||""});
 };

 const saveContact=async()=>{
  try{
   await send(token,`/api/staff/principal/staff/${selected.staff_code}/contact`,"PATCH",contact);
   staff.refresh();
   setSt({e:"",m:"Staff contact updated."});
  }catch(e){setSt({e:e.message,m:""});}
 };

 const resetCredentials=async()=>{
  try{
   await send(token,`/api/staff/principal/staff/${selected.staff_code}/temporary-credentials`,"POST",credentials);
   setSt({e:"",m:"Temporary credentials issued."});
  }catch(e){setSt({e:e.message,m:""});}
 };

 return <>
  <div className="page-title"><div><span className="eyebrow">Principal</span><h1>Institutional Oversight</h1><p>System overview, staff contact administration and temporary credential resets.</p></div></div>
  <Alert {...st}/>
  <Panel title="Overview"><Tbl rows={[overview.data?.data||overview.data||{}]}/></Panel>
  <Panel title="Staff"><Tbl rows={staff.data?.staff||[]} act={r=><Button onClick={()=>select(r)}>Manage</Button>}/></Panel>
  {selected&&<div className="two-col">
   <Panel title={`Contact — ${selected.staff_code}`}>
    <div className="form-grid"><label><span>Email</span><input value={contact.email} onChange={e=>setContact({...contact,email:e.target.value})}/></label><label><span>Cell</span><input value={contact.cell_number} onChange={e=>setContact({...contact,cell_number:e.target.value})}/></label><label><span>Phone</span><input value={contact.phone_number} onChange={e=>setContact({...contact,phone_number:e.target.value})}/></label></div>
    <button className="button gold" onClick={saveContact}>Save Contact</button>
   </Panel>
   <Panel title="Temporary Credentials">
    <div className="form-grid"><label><span>Temporary Password</span><input type="password" value={credentials.temporary_password} onChange={e=>setCredentials({...credentials,temporary_password:e.target.value})}/></label><label><span>Temporary 5-digit PIN</span><input value={credentials.temporary_pin} onChange={e=>setCredentials({...credentials,temporary_pin:e.target.value.replace(/\D/g,"").slice(0,5)})}/></label></div>
    <button className="button gold" onClick={resetCredentials}>Issue Temporary Credentials</button>
   </Panel>
  </div>}
 </>;
}


// ============================================================
// STUDENT CARDS
// ============================================================

export function StudentCards({token}){
 const[number,setNumber]=useState("");
 const[card,setCard]=useState(null);
 const[st,setSt]=useState({e:"",m:""});

 const load=async()=>{
  try{
   const x=await API.request(`/api/staff/desktop-v5/student-cards/${number}`,{},token);
   setCard(x.card||x);
   setSt({e:"",m:""});
  }catch(e){setSt({e:e.message,m:""});}
 };

 return <>
  <div className="page-title"><div><span className="eyebrow">Administration</span><h1>Student Card Centre</h1><p>Review and re-generate learner student cards.</p></div></div>
  <Alert {...st}/>
  <Panel title="Student"><div className="toolbar-grid"><input value={number} onChange={e=>setNumber(e.target.value.replace(/\D/g,"").slice(0,8))} placeholder="Student number"/><button className="button gold" onClick={load}>Load Card</button></div></Panel>
  {card&&<Panel title={`Student Card — ${number}`} actions={<button className="button gold" onClick={()=>API.downloadFile(`/api/staff/desktop-v5/student-cards/${number}/pdf`,token,`${number}_Student_Card.pdf`)}>Generate / Save PDF</button>}><Tbl rows={[{student_number:card.student_number,full_name:card.full_name,course_code:card.course?.course_code,course_name:card.course?.course_name,cycle:card.registration?.cycle,registration_status:card.registration?.registration_status,card_status:card.card?.card_status,issued_date:card.card?.issued_date,expiry_date:card.card?.expiry_date}]}/></Panel>}
 </>;
}


// ============================================================
// FINANCE OPERATIONS
// ============================================================

export function FinanceOperations({token}){
 const dash=useGet("/api/staff/finance/dashboard",token);
 const sponsors=useGet("/api/staff/finance/sponsors",token);

 const[st,setSt]=useState({e:"",m:""});
 const[search,setSearch]=useState("");
 const[students,setStudents]=useState([]);
 const[selected,setSelected]=useState("");
 const[detail,setDetail]=useState(null);
 const[payments,setPayments]=useState([]);
 const[invoices,setInvoices]=useState([]);
 const[receipts,setReceipts]=useState([]);
 const[plan,setPlan]=useState(null);
 const[statements,setStatements]=useState([]);

 const[charge,setCharge]=useState({
  charge_type:"Tuition",
  amount:"",
  description:"",
  due_date:""
 });

 const[payment,setPayment]=useState({
  amount:"",
  method:"EFT",
  reference:"",
  invoice_number:""
 });

 const[credit,setCredit]=useState({
  amount:"",
  reason:""
 });

 const[reverseReason,setReverseReason]=useState("");

 const[planForm,setPlanForm]=useState({
  plan_months:6,
  deposit:"0",
  interest_rate:"0",
  start_date:""
 });

 const[sponsorForm,setSponsorForm]=useState({
  sponsor_name:"",
  sponsor_type:"SETA",
  approval_number:"",
  approved_amount:""
 });

 const[assignSponsor,setAssignSponsor]=useState({
  sponsor_id:"",
  amount_covered:"",
  reference:""
 });

 const findStudents=async()=>{
  try{
   const x=await API.request(
    "/api/staff/finance/students"+q({
     search,
     limit:100
    }),
    {},
    token
   );
   setStudents(x.students||[]);
   setSt({e:"",m:""});
  }catch(e){
   setSt({e:e.message,m:""});
  }
 };

 const open=async studentNumber=>{
  setSelected(studentNumber);
  const paths=[
   `/api/staff/finance/students/${studentNumber}`,
   `/api/staff/finance/students/${studentNumber}/payments`,
   `/api/staff/finance/students/${studentNumber}/invoices`,
   `/api/staff/finance/students/${studentNumber}/receipts`,
   `/api/staff/finance/students/${studentNumber}/payment-plan`,
   `/api/staff/finance/students/${studentNumber}/statements`
  ];

  const results=await Promise.allSettled(
   paths.map(path=>API.request(path,{},token))
  );

  const [a,b,c,d,e,f]=results;

  setDetail(a.status==="fulfilled"?(a.value.data||a.value):null);
  setPayments(b.status==="fulfilled"?(b.value.payments||[]):[]);
  setInvoices(c.status==="fulfilled"?(c.value.invoices||[]):[]);
  setReceipts(d.status==="fulfilled"?(d.value.receipts||[]):[]);
  setPlan(e.status==="fulfilled"?(e.value.payment_plan||e.value.plan||e.value):null);
  setStatements(f.status==="fulfilled"?(f.value.statements||[]):[]);

  const failed=results.filter(x=>x.status==="rejected");

  setSt({
   e:failed.length?`${failed.length} finance section(s) could not be loaded. The available sections are still shown.`:"",
   m:""
  });
 };

 const refresh=()=>selected&&open(selected);

 const createCharge=async()=>{
  try{
   await send(token,`/api/staff/finance/students/${selected}/charges`,"POST",{
    charge_type:charge.charge_type,
    amount:Number(charge.amount),
    description:charge.description,
    due_date:charge.due_date||null
   });
   setSt({e:"",m:"Charge / invoice created."});
   await refresh();
  }catch(e){setSt({e:e.message,m:""});}
 };

 const recordPayment=async()=>{
  try{
   await send(token,`/api/staff/finance/students/${selected}/payments`,"POST",{
    amount:Number(payment.amount),
    method:payment.method,
    reference:payment.reference||null,
    invoice_number:payment.invoice_number||null
   });
   setSt({e:"",m:"Payment recorded."});
   await refresh();
  }catch(e){setSt({e:e.message,m:""});}
 };

 const reversePayment=async row=>{
  if(!reverseReason.trim()){
   setSt({e:"Enter a payment reversal reason first.",m:""});
   return;
  }
  try{
   await send(
    token,
    `/api/staff/finance/payments/${row.id||row.payment_id}/reverse`,
    "POST",
    {reason:reverseReason.trim()}
   );
   setReverseReason("");
   setSt({e:"",m:"Payment reversed."});
   await refresh();
  }catch(e){setSt({e:e.message,m:""});}
 };

 const addCredit=async()=>{
  try{
   await send(token,`/api/staff/finance/students/${selected}/credit`,"POST",{
    amount:Number(credit.amount),
    reason:credit.reason
   });
   setSt({e:"",m:"Finance credit applied."});
   await refresh();
  }catch(e){setSt({e:e.message,m:""});}
 };

 const createPlan=async()=>{
  try{
   await send(token,`/api/staff/finance/students/${selected}/payment-plan`,"POST",{
    plan_months:Number(planForm.plan_months),
    deposit:Number(planForm.deposit||0),
    interest_rate:Number(planForm.interest_rate||0),
    start_date:planForm.start_date||null
   });
   setSt({e:"",m:"Payment plan created."});
   await refresh();
  }catch(e){setSt({e:e.message,m:""});}
 };

 const createSponsor=async()=>{
  try{
   await send(token,"/api/staff/finance/sponsors","POST",{
    sponsor_name:sponsorForm.sponsor_name,
    sponsor_type:sponsorForm.sponsor_type,
    approval_number:sponsorForm.approval_number||null,
    approved_amount:Number(sponsorForm.approved_amount)
   });
   sponsors.refresh();
   setSt({e:"",m:"Sponsor created."});
  }catch(e){setSt({e:e.message,m:""});}
 };

 const assignSponsorToStudent=async()=>{
  try{
   await send(token,`/api/staff/finance/students/${selected}/sponsor`,"POST",{
    sponsor_id:assignSponsor.sponsor_id,
    amount_covered:Number(assignSponsor.amount_covered),
    reference:assignSponsor.reference||null
   });
   setSt({e:"",m:"Sponsor assigned to learner."});
   await refresh();
  }catch(e){setSt({e:e.message,m:""});}
 };

 const generateStatement=async()=>{
  try{
   await send(token,`/api/staff/finance/students/${selected}/statements`,"POST");
   setSt({e:"",m:"Statement generated."});
   await refresh();
  }catch(e){setSt({e:e.message,m:""});}
 };

 return <>
  <div className="page-title">
   <div>
    <span className="eyebrow">Finance</span>
    <h1>Finance Operations</h1>
    <p>CFO and Financial Officer workspace for charges, payments, reversals, credits, plans, sponsors and statements.</p>
   </div>
  </div>
  <Alert {...st}/>

  <Panel title="Finance Dashboard">
   <Tbl rows={[dash.data?.data||dash.data||{}]}/>
  </Panel>

  <Panel title="Find Learner Account">
   <div className="toolbar-grid">
    <input value={search} onChange={e=>setSearch(e.target.value)} placeholder="Student number or learner name"/>
    <button className="button gold" onClick={findStudents}>Search</button>
   </div>
   <Tbl rows={students} act={r=><Button onClick={()=>open(r.student_number)}>Open Finance</Button>}/>
  </Panel>

  {selected&&<>
   <Panel
    title={`Learner Finance — ${selected}`}
    actions={<div className="button-row">
     <Button onClick={generateStatement}>Generate Statement</Button>
     <button className="button gold" onClick={()=>API.downloadFile(`/api/staff/finance/documents/statement/${selected}`,token,`${selected}_Statement.pdf`)}>Statement PDF</button>
    </div>}
   >
    <Tbl rows={[detail||{}]}/>
   </Panel>

   <div className="two-col">
    <Panel title="Create Charge / Invoice">
     <div className="form-grid">
      <label><span>Charge Type</span><input value={charge.charge_type} onChange={e=>setCharge({...charge,charge_type:e.target.value})}/></label>
      <label><span>Amount</span><input type="number" value={charge.amount} onChange={e=>setCharge({...charge,amount:e.target.value})}/></label>
      <label><span>Description</span><input value={charge.description} onChange={e=>setCharge({...charge,description:e.target.value})}/></label>
      <label><span>Due Date</span><input type="date" value={charge.due_date} onChange={e=>setCharge({...charge,due_date:e.target.value})}/></label>
     </div>
     <button className="button gold" onClick={createCharge}>Create Charge</button>
    </Panel>

    <Panel title="Record Payment">
     <div className="form-grid">
      <label><span>Amount</span><input type="number" value={payment.amount} onChange={e=>setPayment({...payment,amount:e.target.value})}/></label>
      <label><span>Method</span><select value={payment.method} onChange={e=>setPayment({...payment,method:e.target.value})}>{["EFT","Cash","Card","PayFast","Other"].map(x=><option key={x}>{x}</option>)}</select></label>
      <label><span>Reference</span><input value={payment.reference} onChange={e=>setPayment({...payment,reference:e.target.value})}/></label>
      <label><span>Invoice Number</span><input value={payment.invoice_number} onChange={e=>setPayment({...payment,invoice_number:e.target.value})}/></label>
     </div>
     <button className="button gold" onClick={recordPayment}>Record Payment</button>
    </Panel>
   </div>

   <div className="two-col">
    <Panel title="Credit / Adjustment">
     <div className="form-grid">
      <label><span>Amount</span><input type="number" value={credit.amount} onChange={e=>setCredit({...credit,amount:e.target.value})}/></label>
      <label><span>Reason</span><input value={credit.reason} onChange={e=>setCredit({...credit,reason:e.target.value})}/></label>
     </div>
     <button className="button gold" onClick={addCredit}>Apply Credit</button>
    </Panel>

    <Panel title="Payment Plan">
     <div className="form-grid">
      <label><span>Months</span><input type="number" min="1" max="36" value={planForm.plan_months} onChange={e=>setPlanForm({...planForm,plan_months:e.target.value})}/></label>
      <label><span>Deposit</span><input type="number" value={planForm.deposit} onChange={e=>setPlanForm({...planForm,deposit:e.target.value})}/></label>
      <label><span>Interest %</span><input type="number" value={planForm.interest_rate} onChange={e=>setPlanForm({...planForm,interest_rate:e.target.value})}/></label>
      <label><span>Start Date</span><input type="date" value={planForm.start_date} onChange={e=>setPlanForm({...planForm,start_date:e.target.value})}/></label>
     </div>
     <button className="button gold" onClick={createPlan}>Create Payment Plan</button>
     {plan&&<Tbl rows={[plan]}/>}
    </Panel>
   </div>

   <Panel title="Payments" text="Enter a reason before reversing a payment.">
    <div className="form-grid" style={{marginBottom:"14px"}}>
     <label><span>Reversal Reason</span><input value={reverseReason} onChange={e=>setReverseReason(e.target.value)} placeholder="Required for payment reversal"/></label>
    </div>
    <Tbl rows={payments} act={r=><Button danger onClick={()=>reversePayment(r)}>Reverse</Button>}/>
   </Panel>
   <Panel title="Invoices"><Tbl rows={invoices} act={r=>r.invoice_number?<Button onClick={()=>API.downloadFile(`/api/staff/finance/documents/invoice/${r.invoice_number}`,token,`${r.invoice_number}.pdf`)}>PDF</Button>:null}/></Panel>
   <Panel title="Receipts"><Tbl rows={receipts} act={r=>r.receipt_number?<Button onClick={()=>API.downloadFile(`/api/staff/finance/documents/receipt/${r.receipt_number}`,token,`${r.receipt_number}.pdf`)}>PDF</Button>:null}/></Panel>
   <Panel title="Statements"><Tbl rows={statements}/></Panel>

   <Panel title="Assign Sponsor">
    <div className="form-grid three">
     <label><span>Sponsor</span><select value={assignSponsor.sponsor_id} onChange={e=>setAssignSponsor({...assignSponsor,sponsor_id:e.target.value})}><option value="">Select sponsor</option>{(sponsors.data?.sponsors||[]).map(x=><option key={x.id||x.sponsor_id} value={x.id||x.sponsor_id}>{x.sponsor_name} — {x.sponsor_type}</option>)}</select></label>
     <label><span>Amount Covered</span><input type="number" value={assignSponsor.amount_covered} onChange={e=>setAssignSponsor({...assignSponsor,amount_covered:e.target.value})}/></label>
     <label><span>Reference</span><input value={assignSponsor.reference} onChange={e=>setAssignSponsor({...assignSponsor,reference:e.target.value})}/></label>
    </div>
    <button className="button gold" onClick={assignSponsorToStudent}>Assign Sponsor</button>
   </Panel>
  </>}

  <Panel title="Create Sponsor">
   <div className="form-grid three">
    <label><span>Sponsor Name</span><input value={sponsorForm.sponsor_name} onChange={e=>setSponsorForm({...sponsorForm,sponsor_name:e.target.value})}/></label>
    <label><span>Sponsor Type</span><input value={sponsorForm.sponsor_type} onChange={e=>setSponsorForm({...sponsorForm,sponsor_type:e.target.value})}/></label>
    <label><span>Approval Number</span><input value={sponsorForm.approval_number} onChange={e=>setSponsorForm({...sponsorForm,approval_number:e.target.value})}/></label>
    <label><span>Approved Amount</span><input type="number" value={sponsorForm.approved_amount} onChange={e=>setSponsorForm({...sponsorForm,approved_amount:e.target.value})}/></label>
   </div>
   <button className="button gold" onClick={createSponsor}>Create Sponsor</button>
  </Panel>
  <Panel title="Sponsors"><Tbl rows={sponsors.data?.sponsors||[]}/></Panel>
 </>;
}


export function AssessmentAdminV54({token}){
 const courses=useGet("/api/staff/academic-management/courses",token);
 const cycles=useGet("/api/staff/academic-management/cycles",token);
 const rooms=useGet("/api/staff/desktop-v5/fisa-rooms",token);
 const fisa=useGet("/api/staff/desktop-v5/fisa-sittings",token);
 const eisaSittings=useGet("/api/staff/compliance-records/eisa/sittings",token);
 const eisa=useGet("/api/staff/desktop-v5/eisa-results",token);

 const[st,setSt]=useState({e:"",m:""});
 const[roomEdit,setRoomEdit]=useState(null);
 const[roomForm,setRoomForm]=useState({
  assessment_centre:"",
  venue_name:"",
  classroom_name:"",
  room_code:"",
  capacity:"",
  sort_order:100,
  is_active:true,
  notes:""
 });

 const[sf,setSf]=useState({
  course_code:"",
  cycle_code:"",
  assessment_date:"",
  reporting_time:"",
  start_time:"",
  end_time:"",
  assessment_centre:"",
  instructions:"",
  status:"Draft",
  female_min_percentage:55
 });

 const[plan,setPlan]=useState(null);
 const[selectedFisa,setSelectedFisa]=useState(null);
 const[fisaRoomSummary,setFisaRoomSummary]=useState([]);
 const[fisaCandidates,setFisaCandidates]=useState([]);

 const[selectedEisa,setSelectedEisa]=useState(null);
 const[eisaCandidates,setEisaCandidates]=useState([]);

 const[se,setSe]=useState({
  course_code:"",
  cycle_code:"",
  assessment_date:"",
  reporting_time:"",
  start_time:"",
  end_time:"",
  venue:"",
  assessment_centre:"",
  capacity:"",
  instructions:"",
  status:"Draft"
 });

 const[ef,setEf]=useState({
  student_number:"",
  attempt_number:1,
  mark:"",
  result:"C",
  assessment_date:"",
  status:"Draft"
 });

 const centres=[
  ...new Set(
   (rooms.data?.rooms||[])
    .filter(x=>x.is_active)
    .map(x=>x.assessment_centre)
    .filter(Boolean)
  )
 ].sort();

 const saveRoom=async()=>{
  try{
   const payload={
    ...roomForm,
    room_code:roomForm.room_code.toUpperCase(),
    capacity:Number(roomForm.capacity),
    sort_order:Number(roomForm.sort_order||100),
    notes:roomForm.notes||null
   };

   if(roomEdit){
    await send(
     token,
     `/api/staff/desktop-v5/fisa-rooms/${roomEdit.id}`,
     "PATCH",
     payload
    );
   }else{
    await send(
     token,
     "/api/staff/desktop-v5/fisa-rooms",
     "POST",
     payload
    );
   }

   setRoomEdit(null);
   setRoomForm({
    assessment_centre:"",
    venue_name:"",
    classroom_name:"",
    room_code:"",
    capacity:"",
    sort_order:100,
    is_active:true,
    notes:""
   });

   rooms.refresh();

   setSt({
    e:"",
    m:roomEdit
      ?"Classroom updated."
      :"Classroom created."
   });
  }catch(e){
   setSt({e:e.message,m:""});
  }
 };

 const editRoom=row=>{
  setRoomEdit(row);
  setRoomForm({
   assessment_centre:row.assessment_centre||"",
   venue_name:row.venue_name||"",
   classroom_name:row.classroom_name||"",
   room_code:row.room_code||"",
   capacity:row.capacity??"",
   sort_order:row.sort_order??100,
   is_active:row.is_active!==false,
   notes:row.notes||""
  });
 };

 const previewPlan=async()=>{
  if(
   !sf.course_code
   ||!sf.cycle_code
   ||!sf.assessment_date
   ||!sf.start_time
   ||!sf.end_time
   ||!sf.assessment_centre
  ){
   setSt({
    e:"Select course, cycle, assessment centre, date, start time and end time first.",
    m:""
   });
   return;
  }

  try{
   const x=await API.request(
    "/api/staff/desktop-v5/fisa-auto-plan"
     +q({
      course_code:sf.course_code,
      cycle_code:sf.cycle_code,
      assessment_centre:sf.assessment_centre,
      assessment_date:sf.assessment_date,
      start_time:sf.start_time,
      end_time:sf.end_time,
      female_min_percentage:sf.female_min_percentage
     }),
    {},
    token
   );

   setPlan(x.plan||null);
   setSt({e:"",m:"FISA auto-allocation preview calculated."});
  }catch(e){
   setPlan(null);
   setSt({e:e.message,m:""});
  }
 };

 const createAutoFisa=async()=>{
  try{
   const x=await send(
    token,
    "/api/staff/desktop-v5/fisa-sittings/auto-create",
    "POST",
    {
     ...sf,
     female_min_percentage:Number(sf.female_min_percentage)
    }
   );

   fisa.refresh();
   setPlan(x.plan||null);

   setSt({
    e:"",
    m:
     `FISA sitting created and ${x.allocated_candidates} learner(s) `
     +"automatically allocated to classrooms."
   });
  }catch(e){
   setSt({e:e.message,m:""});
  }
 };

 const openFisa=async row=>{
  setSelectedFisa(row);

  try{
   const[a,b]=await Promise.all([
    API.request(
     `/api/staff/desktop-v5/fisa-sittings/${row.id}/room-summary`,
     {},
     token
    ),
    API.request(
     `/api/staff/desktop-v5/fisa-sittings/${row.id}/allocated-candidates`,
     {},
     token
    )
   ]);

   setFisaRoomSummary(a.rooms||[]);
   setFisaCandidates(b.candidates||[]);
  }catch(e){
   setSt({e:e.message,m:""});
  }
 };

 const fisaStatus=async(row,status)=>{
  try{
   await send(
    token,
    `/api/staff/desktop-v5/fisa-sittings/${row.id}/status`,
    "PATCH",
    {status}
   );

   fisa.refresh();

   if(selectedFisa?.id===row.id){
    setSelectedFisa(x=>x?{...x,status}:x);
   }

   setSt({
    e:"",
    m:`FISA sitting updated to ${status}.`
   });
  }catch(e){
   setSt({e:e.message,m:""});
  }
 };

 const createEisa=async()=>{
  try{
   await send(
    token,
    "/api/staff/compliance-records/eisa/sittings",
    "POST",
    {
     ...se,
     cycle_code:se.cycle_code||null,
     reporting_time:se.reporting_time||null,
     assessment_centre:se.assessment_centre||null,
     capacity:se.capacity?Number(se.capacity):null,
     instructions:se.instructions||null
    }
   );

   eisaSittings.refresh();
   setSt({e:"",m:"EISA sitting created."});
  }catch(e){
   setSt({e:e.message,m:""});
  }
 };

 const openEisa=async row=>{
  setSelectedEisa(row);

  try{
   const x=await API.request(
    `/api/staff/compliance-records/eisa/sittings/${row.id}/candidates`,
    {},
    token
   );

   setEisaCandidates(x.candidates||[]);
  }catch(e){
   setSt({e:e.message,m:""});
  }
 };

 const captureEisa=async()=>{
  try{
   await send(
    token,
    `/api/staff/desktop-v5/eisa-results/${ef.student_number}`,
    "POST",
    {
     attempt_number:Number(ef.attempt_number),
     mark:ef.mark===""?null:Number(ef.mark),
     result:ef.result,
     assessment_date:ef.assessment_date,
     status:ef.status
    }
   );

   eisa.refresh();
   setSt({e:"",m:"EISA outcome saved."});
  }catch(e){
   setSt({e:e.message,m:""});
  }
 };

 return <>
  <div className="page-title">
   <div>
    <span className="eyebrow">Assessment Administration</span>
    <h1>FISA & EISA Administration</h1>
    <p>Configure examination classrooms once, then automatically seat FISA learners while enforcing the minimum female representation rule per classroom.</p>
   </div>
  </div>

  <Alert {...st}/>

  <Panel
   title="FISA Venue / Classroom Configuration"
   text="Create the classrooms once. Seat capacity and priority are then used automatically whenever a FISA sitting is created."
  >
   <div className="form-grid three">
    <label><span>Assessment Centre</span><input value={roomForm.assessment_centre} onChange={e=>setRoomForm({...roomForm,assessment_centre:e.target.value})} placeholder="e.g. Glen Moniques Assessment Centre"/></label>
    <label><span>Venue / Building</span><input value={roomForm.venue_name} onChange={e=>setRoomForm({...roomForm,venue_name:e.target.value})} placeholder="e.g. Main Campus"/></label>
    <label><span>Classroom Name</span><input value={roomForm.classroom_name} onChange={e=>setRoomForm({...roomForm,classroom_name:e.target.value})} placeholder="e.g. Classroom A"/></label>
    <label><span>Room Code</span><input value={roomForm.room_code} onChange={e=>setRoomForm({...roomForm,room_code:e.target.value.toUpperCase()})} placeholder="e.g. ROOM-A"/></label>
    <label><span>Number of Seats</span><input type="number" min="1" value={roomForm.capacity} onChange={e=>setRoomForm({...roomForm,capacity:e.target.value})}/></label>
    <label><span>Auto-fill Priority</span><input type="number" min="1" value={roomForm.sort_order} onChange={e=>setRoomForm({...roomForm,sort_order:e.target.value})}/></label>
    <label><span>Active</span><select value={roomForm.is_active?"Yes":"No"} onChange={e=>setRoomForm({...roomForm,is_active:e.target.value==="Yes"})}><option>Yes</option><option>No</option></select></label>
    <label><span>Notes</span><input value={roomForm.notes} onChange={e=>setRoomForm({...roomForm,notes:e.target.value})}/></label>
   </div>

   <div className="button-row">
    <button className="button gold" onClick={saveRoom}>
     {roomEdit?"Save Classroom Changes":"Create Classroom"}
    </button>

    {roomEdit&&<Button onClick={()=>{
     setRoomEdit(null);
     setRoomForm({
      assessment_centre:"",
      venue_name:"",
      classroom_name:"",
      room_code:"",
      capacity:"",
      sort_order:100,
      is_active:true,
      notes:""
     });
    }}>Cancel Edit</Button>}
   </div>

   <Tbl
    rows={rooms.data?.rooms||[]}
    cols={[
     "assessment_centre",
     "venue_name",
     "classroom_name",
     "room_code",
     "capacity",
     "sort_order",
     "is_active"
    ]}
    act={r=><Button onClick={()=>editRoom(r)}>Edit</Button>}
   />
  </Panel>

  <Panel
   title="Create FISA Sitting — Automatic Classroom Allocation"
   text="The system selects all FISA-outstanding learners in the selected course/cycle, chooses enough available classrooms, and allocates seats automatically. Every used classroom must meet the configured female minimum."
  >
   <div className="form-grid three">
    <label><span>Course</span><select value={sf.course_code} onChange={e=>{setSf({...sf,course_code:e.target.value});setPlan(null)}}><option value="">Select course</option>{(courses.data?.courses||[]).map(x=><option key={x.course_code} value={x.course_code}>{x.course_code} — {x.course_name}</option>)}</select></label>

    <label><span>Cycle</span><select value={sf.cycle_code} onChange={e=>{setSf({...sf,cycle_code:e.target.value});setPlan(null)}}><option value="">Select cycle</option>{(cycles.data?.cycles||[]).map(x=><option key={x.cycle_code} value={x.cycle_code}>{x.cycle_code} — {x.cycle_name||""}</option>)}</select></label>

    <label><span>Assessment Centre</span><select value={sf.assessment_centre} onChange={e=>{setSf({...sf,assessment_centre:e.target.value});setPlan(null)}}><option value="">Select centre</option>{centres.map(x=><option key={x}>{x}</option>)}</select></label>

    <label><span>Assessment Date</span><input type="date" value={sf.assessment_date} onChange={e=>{setSf({...sf,assessment_date:e.target.value});setPlan(null)}}/></label>
    <label><span>Reporting Time</span><input type="time" value={sf.reporting_time} onChange={e=>setSf({...sf,reporting_time:e.target.value})}/></label>
    <label><span>Start</span><input type="time" value={sf.start_time} onChange={e=>{setSf({...sf,start_time:e.target.value});setPlan(null)}}/></label>
    <label><span>End</span><input type="time" value={sf.end_time} onChange={e=>{setSf({...sf,end_time:e.target.value});setPlan(null)}}/></label>

    <label><span>Minimum Females per Classroom (%)</span><input type="number" min="0" max="100" step="1" value={sf.female_min_percentage} onChange={e=>{setSf({...sf,female_min_percentage:e.target.value});setPlan(null)}}/></label>

    <label><span>Status</span><select value={sf.status} onChange={e=>setSf({...sf,status:e.target.value})}><option>Draft</option><option>Published</option></select></label>

    <label style={{gridColumn:"1 / -1"}}><span>Instructions</span><input value={sf.instructions} onChange={e=>setSf({...sf,instructions:e.target.value})}/></label>
   </div>

   <div className="button-row">
    <Button onClick={previewPlan}>Preview Auto Allocation</Button>
    <button className="button gold" onClick={createAutoFisa}>Create & Auto-Fill Classrooms</button>
   </div>

   {plan&&<>
    <div className={`alert ${plan.feasible?"success":"error"}`} style={{marginTop:"16px"}}>
     Eligible learners: {plan.eligible_total} • Females: {plan.female_total} ({plan.female_percentage}%) • Female seats required: {plan.female_required} • Selected classrooms: {plan.selected_room_count} • Capacity: {plan.selected_capacity}
     {!plan.capacity_ok&&<> • Not enough seats</>}
     {!plan.female_quota_ok&&<> • Female shortage: {plan.female_shortage}</>}
    </div>

    <Tbl
     rows={plan.rooms||[]}
     cols={[
      "room_code",
      "venue_name",
      "classroom_name",
      "capacity",
      "planned_count",
      "female_required"
     ]}
    />
   </>}
  </Panel>

  <Panel title="FISA Sittings">
   <Tbl
    rows={fisa.data?.sittings||[]}
    cols={[
     "sitting_reference",
     "course_code",
     "cycle_code",
     "assessment_date",
     "start_time",
     "assessment_centre",
     "venue",
     "female_min_percentage",
     "allocation_status",
     "status",
     "candidate_count"
    ]}
    act={r=><div className="button-row">
     <Button onClick={()=>openFisa(r)}>Rooms & Candidates</Button>
     <Button onClick={()=>fisaStatus(r,"Published")}>Publish</Button>
     <Button onClick={()=>fisaStatus(r,"Completed")}>Complete</Button>
     <Button danger onClick={()=>fisaStatus(r,"Cancelled")}>Cancel</Button>
    </div>}
   />
  </Panel>

  {selectedFisa&&<>
   <Panel title={`Classroom Allocation — ${selectedFisa.sitting_reference}`}>
    <Tbl
     rows={fisaRoomSummary}
     cols={[
      "room_code",
      "venue_name",
      "classroom_name",
      "capacity",
      "assigned_count",
      "female_count",
      "non_female_count",
      "female_percentage",
      "female_min_percentage",
      "female_quota_met",
      "seats_remaining"
     ]}
    />
   </Panel>

   <Panel title={`Candidate Seating — ${selectedFisa.sitting_reference}`}>
    <Tbl
     rows={fisaCandidates}
     cols={[
      "room_code",
      "classroom_name",
      "room_seat_number",
      "seat_number",
      "student_number",
      "learner_name",
      "gender_code",
      "admission_status",
      "attendance_status"
     ]}
    />
   </Panel>
  </>}

  <Panel title="Create EISA Sitting">
   <div className="form-grid three">
    <label><span>Course</span><select value={se.course_code} onChange={e=>setSe({...se,course_code:e.target.value})}><option value="">Select FISA + EISA course</option>{(courses.data?.courses||[]).filter(x=>x.assessment_type==="FISA_PLUS_EISA").map(x=><option key={x.course_code} value={x.course_code}>{x.course_code} — {x.course_name}</option>)}</select></label>
    <label><span>Cycle</span><select value={se.cycle_code} onChange={e=>setSe({...se,cycle_code:e.target.value})}><option value="">No cycle</option>{(cycles.data?.cycles||[]).map(x=><option key={x.cycle_code} value={x.cycle_code}>{x.cycle_code}</option>)}</select></label>
    <label><span>Assessment Date</span><input type="date" value={se.assessment_date} onChange={e=>setSe({...se,assessment_date:e.target.value})}/></label>
    <label><span>Reporting Time</span><input type="time" value={se.reporting_time} onChange={e=>setSe({...se,reporting_time:e.target.value})}/></label>
    <label><span>Start</span><input type="time" value={se.start_time} onChange={e=>setSe({...se,start_time:e.target.value})}/></label>
    <label><span>End</span><input type="time" value={se.end_time} onChange={e=>setSe({...se,end_time:e.target.value})}/></label>
    <label><span>Venue</span><input value={se.venue} onChange={e=>setSe({...se,venue:e.target.value})}/></label>
    <label><span>Assessment Centre</span><input value={se.assessment_centre} onChange={e=>setSe({...se,assessment_centre:e.target.value})}/></label>
    <label><span>Capacity</span><input type="number" min="1" value={se.capacity} onChange={e=>setSe({...se,capacity:e.target.value})}/></label>
    <label><span>Status</span><select value={se.status} onChange={e=>setSe({...se,status:e.target.value})}>{["Draft","Published","Completed","Cancelled"].map(x=><option key={x}>{x}</option>)}</select></label>
   </div>
   <button className="button gold" onClick={createEisa}>Create EISA Sitting</button>
  </Panel>

  <Panel title="EISA Sittings">
   <Tbl
    rows={eisaSittings.data?.sittings||[]}
    cols={[
     "sitting_reference",
     "course_code",
     "cycle_code",
     "assessment_date",
     "start_time",
     "venue",
     "capacity",
     "status",
     "candidate_count"
    ]}
    act={r=><Button onClick={()=>openEisa(r)}>Candidates</Button>}
   />
  </Panel>

  {selectedEisa&&<Panel title={`EISA Candidates — ${selectedEisa.sitting_reference}`}>
   <Tbl rows={eisaCandidates}/>
  </Panel>}

  <Panel title="Capture Official EISA Outcome">
   <div className="form-grid three">
    <label><span>Learner</span><select value={ef.student_number} onChange={e=>setEf({...ef,student_number:e.target.value})}><option value="">Select EISA learner</option>{(eisa.data?.learners||[]).filter(x=>x.eisa_eligible).map(x=><option key={x.student_number} value={x.student_number}>{x.student_number} — {[x.first_name,x.middle_name,x.last_name].filter(Boolean).join(" ")} — {x.course_code}</option>)}</select></label>
    <label><span>Attempt</span><input type="number" min="1" value={ef.attempt_number} onChange={e=>setEf({...ef,attempt_number:e.target.value})}/></label>
    <label><span>Mark</span><input type="number" min="0" max="100" value={ef.mark} onChange={e=>setEf({...ef,mark:e.target.value})}/></label>
    <label><span>Result</span><select value={ef.result} onChange={e=>setEf({...ef,result:e.target.value})}><option value="C">Competent</option><option value="NYC">Not Yet Competent</option></select></label>
    <label><span>Assessment Date</span><input type="date" value={ef.assessment_date} onChange={e=>setEf({...ef,assessment_date:e.target.value})}/></label>
    <label><span>Status</span><select value={ef.status} onChange={e=>setEf({...ef,status:e.target.value})}><option>Draft</option><option>Published</option></select></label>
   </div>
   <button className="button gold" onClick={captureEisa}>Save EISA Outcome</button>
  </Panel>

  <Panel title="EISA Outcomes">
   <Tbl
    rows={eisa.data?.learners||[]}
    cols={[
     "student_number",
     "course_code",
     "cycle_code",
     "eisa_eligible",
     "attempt_number",
     "mark",
     "result",
     "status",
     "assessment_date"
    ]}
   />
  </Panel>
 </>;
}
