
import {useEffect,useMemo,useState} from "react";
import * as API from "./api";

const q=(o={})=>{const p=new URLSearchParams();Object.entries(o).forEach(([k,v])=>{if(v!==""&&v!==null&&v!==undefined)p.set(k,v)});const s=p.toString();return s?`?${s}`:""};
const h=s=>String(s??"").replace(/_/g," ").replace(/\b\w/g,c=>c.toUpperCase());
const v=x=>x===null||x===undefined||x===""?"—":typeof x==="boolean"?(x?"Yes":"No"):typeof x==="object"?JSON.stringify(x):String(x);

function Alert({e,m}){return e||m?<div className={`alert ${e?"error":"success"}`}>{e||m}</div>:null}
function Panel({title,text,children,actions}){return <section className="panel"><div className="panel-head"><div><h2>{title}</h2>{text&&<p>{text}</p>}</div>{actions&&<div className="panel-actions">{actions}</div>}</div><div className="panel-body">{children}</div></section>}
function Obj({data}){if(!data||typeof data!=="object")return <div className="empty">No data</div>;return <div className="object-grid">{Object.entries(data).map(([k,x])=><div className="object-item" key={k}><span>{h(k)}</span><strong>{v(x)}</strong></div>)}</div>}
function Tbl({rows=[],cols,act,onRow}){const[f,setF]=useState("");const rr=useMemo(()=>rows.filter(r=>JSON.stringify(r).toLowerCase().includes(f.toLowerCase())),[rows,f]);if(!rows.length)return <div className="empty">No records available.</div>;const kk=cols||Object.keys(rows[0]).filter(k=>typeof rows[0][k]!=="object").slice(0,7);return <><div className="table-tools"><input placeholder="Filter records..." value={f} onChange={e=>setF(e.target.value)}/><span>{rr.length} of {rows.length}</span></div><div className="table-wrap"><table><thead><tr>{kk.map(k=><th key={k}>{h(k)}</th>)}{act&&<th>Actions</th>}</tr></thead><tbody>{rr.map((r,i)=><tr key={r.id||r.student_number||r.staff_code||r.class_code||r.cycle_code||i} className={onRow?"clickable":""} onClick={()=>onRow?.(r)}>{kk.map(k=><td key={k}>{k.toLowerCase().includes("status")?<span className="badge">{v(r[k])}</span>:v(r[k])}</td>)}{act&&<td onClick={e=>e.stopPropagation()}>{act(r)}</td>}</tr>)}</tbody></table></div></>}
function useGet(path,token){const[s,setS]=useState({data:null,e:"",loading:false,n:0});useEffect(()=>{let on=true;if(!path)return;setS(x=>({...x,loading:true,e:""}));API.request(path,{},token).then(data=>on&&setS(x=>({...x,data,loading:false}))).catch(e=>on&&setS(x=>({...x,e:e.message,loading:false})));return()=>{on=false}},[path,token,s.n]);return {...s,refresh:()=>setS(x=>({...x,n:x.n+1}))}}
async function send(token,path,method,body){return API.request(path,{method,...(body===undefined?{}:{body:JSON.stringify(body)})},token)}
const Button=({children,onClick,danger=false})=><button className={`button ${danger?"danger":"light"}`} onClick={onClick}>{children}</button>;

export function Admissions({token}){
 const[search,setSearch]=useState("");
 const[status,setStatus]=useState("");
 const[path,setPath]=useState("/api/staff/admissions/applications?limit=100");
 const[selected,setSelected]=useState([]);
 const[sel,setSel]=useState("");
 const[detail,setDetail]=useState(null);
 const[docs,setDocs]=useState([]);
 const[st,setSt]=useState({e:"",m:""});
 const[preview,setPreview]=useState(null);
 const[requestSelected,setRequestSelected]=useState([]);
 const[requestReason,setRequestReason]=useState("");
 const[requestInstructions,setRequestInstructions]=useState("");
 const[requestDueDate,setRequestDueDate]=useState("");
 const[bulkResult,setBulkResult]=useState([]);

 const list=useGet(path,token);
 const applications=list.data?.applications||[];

 const closePreview=()=>{
  if(preview?.url){
   URL.revokeObjectURL(
    preview.url
   );
  }
  setPreview(null);
 };

 const open=async n=>{
  setSel(n);
  closePreview();

  try{
   const[a,b]=await Promise.all([
    API.request(
     `/api/staff/admissions/applications/${n}`,
     {},
     token
    ),
    API.request(
     `/api/staff/admissions/applications/${n}/document-checklist`,
     {},
     token
    )
   ]);

   setDetail(
    a.data||a
   );

   const checklist=(
    b.data?.checklist
    ||b.checklist
    ||[]
   );

   setDocs(
    checklist
   );

   setRequestSelected([]);
   setSt({e:"",m:""});
  }catch(e){
   setSt({e:e.message,m:""});
  }
 };

 const doPost=async(path,body,msg)=>{
  try{
   const result=await send(
    token,
    path,
    "POST",
    body
   );

   setSt({e:"",m:msg});
   list.refresh();

   if(sel){
    await open(sel);
   }

   return result;
  }catch(e){
   setSt({e:e.message,m:""});
   return null;
  }
 };

 const accept=()=>{
  if(!sel)return;

  const cycle=prompt(
   "Cycle code (leave blank to use the application's configured cycle):",
   ""
  );

  if(cycle===null)return;

  const start=prompt(
   "Programme start date YYYY-MM-DD (leave blank to use the cycle default):",
   ""
  );

  if(start===null)return;

  const end=prompt(
   "Expected completion date YYYY-MM-DD (optional):",
   ""
  );

  if(end===null)return;

  doPost(
   `/api/staff/admissions/applications/${sel}/accept`,
   {
    funding_type:null,
    cycle_code:cycle||null,
    program_start_date:start||null,
    expected_completion_date:end||null,
    enforce_documents:true
   },
   "Application accepted and registration processed."
  );
 };

 const reject=()=>{
  if(!sel)return;

  const reason=prompt(
   "Rejection reason:",
   ""
  );

  if(reason===null)return;

  doPost(
   `/api/staff/admissions/applications/${sel}/reject`,
   {reason:reason||null},
   "Application rejected."
  );
 };

 const retryRegistration=()=>{
  if(!sel)return;

  const cycle=prompt(
   "Cycle code (optional):",
   ""
  );

  if(cycle===null)return;

  const start=prompt(
   "Programme start date YYYY-MM-DD (optional):",
   ""
  );

  if(start===null)return;

  const end=prompt(
   "Expected completion date YYYY-MM-DD (optional):",
   ""
  );

  if(end===null)return;

  doPost(
   `/api/staff/admissions/applications/${sel}/registration/retry`,
   {
    funding_type:null,
    cycle_code:cycle||null,
    program_start_date:start||null,
    expected_completion_date:end||null
   },
   "Registration retry processed."
  );
 };

 const review=async(row,action)=>{
  const id=(
   row.document?.id
   ||row.document_id
   ||row.id
  );

  if(!id){
   setSt({
    e:"No uploaded document is attached to this checklist item.",
    m:""
   });
   return;
  }

  let notes=null;

  if(action!=="Approved"){
   notes=prompt(
    action==="Resubmission Required"
     ?"Reason/instructions for re-upload:"
     :"Document rejection reason:",
    row.document?.review_notes||""
   );

   if(notes===null)return;

   if(!notes.trim()){
    setSt({
     e:"Review notes are required for this action.",
     m:""
    });
    return;
   }
  }

  try{
   await send(
    token,
    `/api/staff/admissions/documents/${id}/review`,
    "PATCH",
    {
     action,
     review_notes:notes?.trim()||null
    }
   );

   setSt({
    e:"",
    m:
     action==="Approved"
      ?"Document approved."
      :action==="Rejected"
       ?"Document rejected."
       :"Re-upload requested."
   });

   await open(sel);
  }catch(e){
   setSt({e:e.message,m:""});
  }
 };

 const previewDocument=async row=>{
  const doc=row.document;

  if(!doc?.id){
   setSt({
    e:"There is no uploaded file to preview for this requirement.",
    m:""
   });
   return;
  }

  try{
   const result=await API.fetchBlob(
    `/api/staff/admissions/documents/${doc.id}/preview`,
    token
   );

   if(preview?.url){
    URL.revokeObjectURL(
     preview.url
    );
   }

   const url=URL.createObjectURL(
    result.blob
   );

   setPreview({
    url,
    mime:
     doc.mime_type
     ||result.contentType
     ||"",
    name:
     doc.original_filename
     ||doc.document_label
     ||"Uploaded Document"
   });

   setSt({e:"",m:""});
  }catch(e){
   setSt({e:e.message,m:""});
  }
 };

 const toggleSelected=n=>{
  setSelected(current=>
   current.includes(n)
    ?current.filter(x=>x!==n)
    :[...current,n]
  );
 };

 const toggleAll=()=>{
  const visible=applications.map(
   x=>x.student_number
  );

  const allSelected=(
   visible.length>0
   &&visible.every(
    n=>selected.includes(n)
   )
  );

  if(allSelected){
   setSelected(current=>
    current.filter(
     n=>!visible.includes(n)
    )
   );
  }else{
   setSelected(current=>
    Array.from(
     new Set([
      ...current,
      ...visible
     ])
    )
   );
  }
 };

 const bulkAccept=async()=>{
  if(!selected.length){
   setSt({
    e:"Select at least one application.",
    m:""
   });
   return;
  }

  if(!window.confirm(
   `Accept and register ${selected.length} selected application(s)? Required documents will be enforced.`
  )){
   return;
  }

  const cycle=prompt(
   "Shared cycle code (optional - leave blank to use each application's configured/default cycle):",
   ""
  );

  if(cycle===null)return;

  const start=prompt(
   "Shared programme start date YYYY-MM-DD (optional):",
   ""
  );

  if(start===null)return;

  const end=prompt(
   "Shared expected completion date YYYY-MM-DD (optional):",
   ""
  );

  if(end===null)return;

  try{
   const result=await send(
    token,
    "/api/staff/admissions/bulk/accept",
    "POST",
    {
     student_numbers:selected,
     funding_type:null,
     cycle_code:cycle||null,
     program_start_date:start||null,
     expected_completion_date:end||null,
     enforce_documents:true
    }
   );

   setBulkResult(
    result.results||[]
   );

   setSt({
    e:"",
    m:`Bulk accept completed: ${result.success_count} successful, ${result.failure_count} failed.`
   });

   setSelected([]);
   list.refresh();
  }catch(e){
   setSt({e:e.message,m:""});
  }
 };

 const bulkReject=async()=>{
  if(!selected.length){
   setSt({
    e:"Select at least one application.",
    m:""
   });
   return;
  }

  const reason=prompt(
   `Rejection reason for ${selected.length} selected application(s):`,
   ""
  );

  if(reason===null)return;

  if(!window.confirm(
   `Reject ${selected.length} selected application(s)?`
  )){
   return;
  }

  try{
   const result=await send(
    token,
    "/api/staff/admissions/bulk/reject",
    "POST",
    {
     student_numbers:selected,
     reason:reason.trim()||null
    }
   );

   setBulkResult(
    result.results||[]
   );

   setSt({
    e:"",
    m:`Bulk reject completed: ${result.success_count} successful, ${result.failure_count} failed.`
   });

   setSelected([]);
   list.refresh();
  }catch(e){
   setSt({e:e.message,m:""});
  }
 };

 const toggleRequest=documentType=>{
  setRequestSelected(current=>
   current.includes(documentType)
    ?current.filter(x=>x!==documentType)
    :[...current,documentType]
  );
 };

 const requestDocuments=async()=>{
  if(!sel){
   setSt({
    e:"Open an application first.",
    m:""
   });
   return;
  }

  const chosen=docs.filter(
   row=>
    requestSelected.includes(
     row.document_type
    )
  );

  if(!chosen.length){
   setSt({
    e:"Select at least one missing document to request.",
    m:""
   });
   return;
  }

  const documents=chosen.map(
   row=>({
    document_type:row.document_type,
    document_label:
     row.document_label
     ||row.document_type,
    reason:
     requestReason.trim()
     ||null,
    instructions:
     requestInstructions.trim()
     ||null,
    due_date:
     requestDueDate
     ||null,
    is_required:
     row.is_required!==false
   })
  );

  try{
   await send(
    token,
    `/api/staff/admissions/applications/${sel}/outstanding-documents`,
    "POST",
    {documents}
   );

   setRequestSelected([]);
   setRequestReason("");
   setRequestInstructions("");
   setRequestDueDate("");

   setSt({
    e:"",
    m:`Requested ${documents.length} outstanding document(s).`
   });

   list.refresh();
   await open(sel);
  }catch(e){
   setSt({e:e.message,m:""});
  }
 };

 const requestable=docs.filter(
  row=>!row.document
 );

 return <><div className="page-title"><div><span className="eyebrow">Admissions</span><h1>Applications & Registration</h1><p>Preview and review uploaded documents, request missing evidence, process applications individually or in bulk, and retry registrations.</p></div></div><Alert {...st}/>

 <Panel title="Search & Filter">
  <div className="toolbar-grid">
   <input placeholder="Student number, name or email" value={search} onChange={e=>setSearch(e.target.value)}/>
   <select value={status} onChange={e=>setStatus(e.target.value)}>
    <option value="">All statuses</option>
    {["Pending","Outstanding Documents","Accepted","Rejected"].map(x=><option key={x}>{x}</option>)}
   </select>
   <button className="button gold" onClick={()=>setPath("/api/staff/admissions/applications"+q({search,status,limit:100}))}>Search</button>
  </div>
 </Panel>

 <Panel title={`Applications (${applications.length})`} text={`${selected.length} application(s) selected.`} actions={<div className="button-row"><button className="button gold" disabled={!selected.length} onClick={bulkAccept}>Accept Selected</button><Button danger onClick={bulkReject}>Reject Selected</Button><Button onClick={list.refresh}>Refresh</Button></div>}>
  <Alert e={list.e}/>
  {!applications.length?<div className="empty">No applications found.</div>:<div className="table-wrap"><table><thead><tr><th><input type="checkbox" checked={applications.length>0&&applications.every(x=>selected.includes(x.student_number))} onChange={toggleAll}/></th><th>Student Number</th><th>Name</th><th>Course</th><th>Cycle</th><th>Status</th><th>Created</th><th>Action</th></tr></thead><tbody>{applications.map(r=><tr key={r.student_number}><td><input type="checkbox" checked={selected.includes(r.student_number)} onChange={()=>toggleSelected(r.student_number)}/></td><td>{v(r.student_number)}</td><td>{[r.first_name,r.middle_name,r.last_name].filter(Boolean).join(" ")}</td><td>{v(r.course_code||r.qualification_id)}</td><td>{v(r.cycle_code)}</td><td><span className="badge">{v(r.app_status)}</span></td><td>{v(r.created_at)}</td><td><Button onClick={()=>open(r.student_number)}>Open</Button></td></tr>)}</tbody></table></div>}
 </Panel>

 {bulkResult.length>0&&<Panel title="Bulk Action Results" text="Each learner is processed separately so one failure does not hide successful records."><Tbl rows={bulkResult.map(x=>({student_number:x.student_number,status:x.success?"Success":"Failed",message:x.message||x.error||""}))} cols={["student_number","status","message"]}/></Panel>}

 {sel&&<><Panel title={`Application ${sel}`} actions={<div className="button-row"><button className="button gold" onClick={accept}>Accept & Register</button><Button danger onClick={reject}>Reject</Button><Button onClick={retryRegistration}>Retry Registration</Button></div>}><Obj data={detail?.application||detail||{}}/></Panel>

 <Panel title="Uploaded Documents & Review" text="Preview the actual uploaded PDF/JPG/PNG before approving, rejecting or requesting a corrected re-upload.">
  {!docs.length?<div className="empty">No document requirements are configured for this application.</div>:<div className="table-wrap"><table><thead><tr><th>Document</th><th>Required</th><th>Stage</th><th>Uploaded File</th><th>Review Status</th><th>Request Status</th><th>Actions</th></tr></thead><tbody>{docs.map((row,i)=>{const doc=row.document||null;const req=row.request||null;return <tr key={`${row.document_type}-${i}`}><td>{v(row.document_label||row.document_type)}</td><td>{row.is_required?"Yes":"No"}</td><td>{v(row.trigger_stage)}</td><td>{doc?v(doc.original_filename):"Not uploaded"}</td><td><span className="badge">{v(doc?.review_status||"Not Uploaded")}</span></td><td><span className="badge">{v(req?.status||"—")}</span></td><td><div className="button-row">{doc&&<Button onClick={()=>previewDocument(row)}>Preview</Button>}{doc&&<Button onClick={()=>review(row,"Approved")}>Approve</Button>}{doc&&<Button danger onClick={()=>review(row,"Rejected")}>Reject</Button>}{doc&&<Button onClick={()=>review(row,"Resubmission Required")}>Request Re-upload</Button>}</div></td></tr>})}</tbody></table></div>}
 </Panel>

 {preview&&<Panel title={`Document Preview - ${preview.name}`} actions={<Button onClick={closePreview}>Close Preview</Button>}>
  <div style={{minHeight:"650px"}}>
   {preview.mime.startsWith("image/")?<img src={preview.url} alt={preview.name} style={{maxWidth:"100%",maxHeight:"780px",display:"block",margin:"0 auto"}}/>:<iframe title={preview.name} src={preview.url} style={{width:"100%",height:"760px",border:"1px solid #d5d9e2",borderRadius:"10px",background:"#fff"}}/>}
  </div>
 </Panel>}

 <Panel title="Request Missing Documents" text="Select missing configured requirements. The learner will be placed in Outstanding Documents status and the normal outstanding-document workflow will run.">
  {!requestable.length?<div className="empty">There are no currently missing configured documents to request.</div>:<><div className="table-wrap"><table><thead><tr><th>Select</th><th>Document</th><th>Required</th><th>Stage</th></tr></thead><tbody>{requestable.map(row=><tr key={row.document_type}><td><input type="checkbox" checked={requestSelected.includes(row.document_type)} onChange={()=>toggleRequest(row.document_type)}/></td><td>{v(row.document_label||row.document_type)}</td><td>{row.is_required?"Yes":"No"}</td><td>{v(row.trigger_stage)}</td></tr>)}</tbody></table></div><div className="form-grid"><label><span>Reason</span><input value={requestReason} onChange={e=>setRequestReason(e.target.value)} placeholder="Why the document is required"/></label><label><span>Due Date</span><input type="date" value={requestDueDate} onChange={e=>setRequestDueDate(e.target.value)}/></label><label><span>Instructions</span><input value={requestInstructions} onChange={e=>setRequestInstructions(e.target.value)} placeholder="Upload instructions"/></label></div><button className="button gold" onClick={requestDocuments}>Request Selected Documents</button></>}
 </Panel></>}</>
}


export function Academics({token}){
 const cyc=useGet("/api/staff/academic-management/cycles",token);
 const cou=useGet("/api/staff/academic-management/courses",token);
 const cls=useGet("/api/staff/desktop-v5/academic-classes",token);
 const staff=useGet("/api/staff/desktop-v5/academic-staff-options",token);

 const[st,setSt]=useState({e:"",m:""});

 const[cycleForm,setCycleForm]=useState({
  cycle_code:"",
  cycle_name:"",
  application_start_date:"",
  application_end_date:"",
  registration_start_date:"",
  registration_end_date:"",
  program_start_date:"",
  expected_completion_date:"",
  cipc_required:false,
  status:"Draft"
 });

 const[selectedCycle,setSelectedCycle]=useState(null);
 const[cycleStatus,setCycleStatus]=useState("Draft");
 const[cycleCourses,setCycleCourses]=useState([]);

 const[classForm,setClassForm]=useState({
  class_code:"",
  class_name:"",
  course_code:"",
  cycle_code:"",
  class_group:"",
  status:"Draft"
 });

 const[selectedClass,setSelectedClass]=useState(null);
 const[classEdit,setClassEdit]=useState({
  class_name:"",
  class_group:"",
  status:"Draft"
 });
 const[facilitatorCode,setFacilitatorCode]=useState("");
 const[assessorCode,setAssessorCode]=useState("");
 const[moderatorCode,setModeratorCode]=useState("");
 const[classLearners,setClassLearners]=useState([]);
 const[eligibleLearners,setEligibleLearners]=useState([]);

 const cycles=cyc.data?.cycles||[];
 const courses=cou.data?.courses||[];
 const classes=cls.data?.classes||[];
 const staffRows=staff.data?.staff||staff.data?.staff_options||[];

 const facilitators=staffRows.filter(
  x=>Boolean(x.can_facilitate)
 );
 const assessors=staffRows.filter(
  x=>Boolean(x.can_assess)
 );
 const moderators=staffRows.filter(
  x=>Boolean(x.can_moderate)
 );

 const changeCycle=(key,value)=>{
  setCycleForm(x=>({...x,[key]:value}));
 };

 const changeClass=(key,value)=>{
  setClassForm(x=>({...x,[key]:value}));
 };

 const act=async(path,method,body,msg)=>{
  try{
   const result=await send(
    token,
    path,
    method,
    body
   );
   setSt({e:"",m:msg});
   return result;
  }catch(e){
   setSt({e:e.message,m:""});
   return null;
  }
 };

 const createCycle=async()=>{
  if(!cycleForm.cycle_code.trim()){
   setSt({e:"Cycle code is required.",m:""});
   return;
  }

  if(!cycleForm.program_start_date){
   setSt({e:"Programme start date is required.",m:""});
   return;
  }

  const payload={
   ...cycleForm,
   cycle_name:cycleForm.cycle_name||null,
   application_start_date:cycleForm.application_start_date||null,
   application_end_date:cycleForm.application_end_date||null,
   registration_start_date:cycleForm.registration_start_date||null,
   registration_end_date:cycleForm.registration_end_date||null,
   expected_completion_date:cycleForm.expected_completion_date||null
  };

  const result=await act(
   "/api/staff/academic-management/cycles",
   "POST",
   payload,
   "Academic cycle created."
  );

  if(!result)return;

  setCycleForm({
   cycle_code:"",
   cycle_name:"",
   application_start_date:"",
   application_end_date:"",
   registration_start_date:"",
   registration_end_date:"",
   program_start_date:"",
   expected_completion_date:"",
   cipc_required:false,
   status:"Draft"
  });

  cyc.refresh();
 };

 const openCycle=async(row)=>{
  setSelectedCycle(row);
  setCycleStatus(row.status||"Draft");

  try{
   const x=await API.request(
    "/api/staff/desktop-v5/cycle-courses"
      +q({cycle_code:row.cycle_code}),
    {},
    token
   );
   setCycleCourses(x.courses||[]);
   setSt({e:"",m:""});
  }catch(e){
   setSt({e:e.message,m:""});
  }
 };

 const saveCycleStatus=async()=>{
  if(!selectedCycle)return;

  const result=await act(
   `/api/staff/academic-management/cycles/${selectedCycle.cycle_code}/status`,
   "PATCH",
   {status:cycleStatus},
   `Cycle ${selectedCycle.cycle_code} status updated to ${cycleStatus}.`
  );

  if(!result)return;

  cyc.refresh();
  setSelectedCycle(x=>(
   x?{...x,status:cycleStatus}:x
  ));
 };

 const offeringMap=Object.fromEntries(
  cycleCourses.map(
   x=>[x.course_code,x]
  )
 );

 const offeringRows=courses.map(
  c=>({
   course_code:c.course_code,
   course_name:c.course_name,
   nqf_level:c.nqf_level,
   credits:c.credits,
   assessment_type:c.assessment_type,
   is_active:Boolean(
    offeringMap[c.course_code]?.is_active
   )
  })
 );

 const toggleOffering=async(row)=>{
  if(!selectedCycle)return;

  const result=await act(
   "/api/staff/desktop-v5/cycle-course-status",
   "POST",
   {
    cycle_code:selectedCycle.cycle_code,
    course_code:row.course_code,
    is_active:!row.is_active
   },
   `${row.course_code} offering updated.`
  );

  if(!result)return;

  await openCycle({
   ...selectedCycle,
   status:cycleStatus
  });
  cyc.refresh();
 };

 const createClass=async()=>{
  if(!classForm.class_code.trim()){
   setSt({e:"Class code is required.",m:""});
   return;
  }

  if(!classForm.cycle_code){
   setSt({e:"Select a cycle.",m:""});
   return;
  }

  if(!classForm.course_code){
   setSt({e:"Select a course.",m:""});
   return;
  }

  const result=await act(
   "/api/staff/academic-management/classes",
   "POST",
   {
    class_code:classForm.class_code,
    class_name:classForm.class_name||null,
    course_code:classForm.course_code,
    cycle_code:classForm.cycle_code,
    class_group:classForm.class_group||null,
    facilitator_code:null,
    assessor_code:null,
    status:classForm.status
   },
   "Class created."
  );

  if(!result)return;

  setClassForm({
   class_code:"",
   class_name:"",
   course_code:"",
   cycle_code:"",
   class_group:"",
   status:"Draft"
  });

  cls.refresh();
  cyc.refresh();
 };

 const openClass=async(row)=>{
  setSelectedClass(row);
  setClassEdit({
   class_name:row.class_name||"",
   class_group:row.class_group||"",
   status:row.status||"Draft"
  });
  setFacilitatorCode(
   row.facilitator_code||""
  );
  setAssessorCode(
   row.assessor_code||""
  );
  setModeratorCode(
   row.moderator_code||""
  );

  try{
   const[a,b]=await Promise.all([
    API.request(
     `/api/staff/academic-management/classes/${row.class_code}/learners`,
     {},
     token
    ),
    API.request(
     `/api/staff/academic-management/classes/${row.class_code}/eligible-learners`,
     {},
     token
    )
   ]);

   setClassLearners(
    a.learners||[]
   );
   setEligibleLearners(
    b.learners||b.eligible_learners||[]
   );
   setSt({e:"",m:""});
  }catch(e){
   setSt({e:e.message,m:""});
  }
 };

 const saveClassDetails=async()=>{
  if(!selectedClass)return;

  const result=await act(
   `/api/staff/academic-management/classes/${selectedClass.class_code}`,
   "PUT",
   {
    class_name:classEdit.class_name||null,
    course_code:selectedClass.course_code,
    cycle_code:selectedClass.cycle_code,
    class_group:classEdit.class_group||null,
    status:classEdit.status
   },
   "Class details updated."
  );

  if(!result)return;

  cls.refresh();
  setSelectedClass(x=>(
   x?{
    ...x,
    class_name:classEdit.class_name,
    class_group:classEdit.class_group,
    status:classEdit.status
   }:x
  ));
 };

 const saveStaffAssignment=async()=>{
  if(!selectedClass)return;

  const result=await act(
   `/api/staff/desktop-v5/classes/${selectedClass.class_code}/academic-staff`,
   "PUT",
   {
    facilitator_code:facilitatorCode||null,
    assessor_code:assessorCode||null,
    moderator_code:moderatorCode||null
   },
   "Class academic staff assignment updated."
  );

  if(!result)return;

  cls.refresh();
  await openClass({
   ...selectedClass,
   facilitator_code:facilitatorCode||null,
   assessor_code:assessorCode||null,
   moderator_code:moderatorCode||null
  });
 };

 const enrolLearner=async(row)=>{
  if(!selectedClass)return;

  const result=await act(
   `/api/staff/academic-management/classes/${selectedClass.class_code}/enrolments`,
   "POST",
   {registration_id:row.registration_id},
   `${row.student_number} enrolled in ${selectedClass.class_code}.`
  );

  if(!result)return;

  cls.refresh();
  await openClass(selectedClass);
 };

 const removeLearner=async(row)=>{
  if(!selectedClass)return;

  const ok=window.confirm(
   `Remove ${row.student_number} from ${selectedClass.class_code}?`
  );

  if(!ok)return;

  const result=await act(
   `/api/staff/academic-management/classes/${selectedClass.class_code}/enrolments/${row.registration_id}/remove`,
   "PATCH",
   undefined,
   `${row.student_number} removed from ${selectedClass.class_code}.`
  );

  if(!result)return;

  cls.refresh();
  await openClass(selectedClass);
 };

 return <><div className="page-title"><div><span className="eyebrow">Academic Administration</span><h1>Academic Management</h1><p>Create cycles and classes, control cycle status and course offerings, assign Facilitators/Assessors/Moderators and manage learner class enrolment.</p></div></div><Alert e={st.e||cyc.e||cou.e||cls.e||staff.e} m={st.m}/>

 <Panel title="Create Academic Cycle" text="Create the intake/programme cycle first. New cycles normally begin in Draft status.">
  <div className="form-grid">
   <label><span>Cycle Code *</span><input value={cycleForm.cycle_code} onChange={e=>changeCycle("cycle_code",e.target.value)} placeholder="e.g. 2027-INTAKE-01"/></label>
   <label><span>Cycle Name</span><input value={cycleForm.cycle_name} onChange={e=>changeCycle("cycle_name",e.target.value)} placeholder="e.g. January 2027 Intake"/></label>
   <label><span>Programme Start Date *</span><input type="date" value={cycleForm.program_start_date} onChange={e=>changeCycle("program_start_date",e.target.value)}/></label>
   <label><span>Expected Completion Date</span><input type="date" value={cycleForm.expected_completion_date} onChange={e=>changeCycle("expected_completion_date",e.target.value)}/></label>
   <label><span>Application Start</span><input type="date" value={cycleForm.application_start_date} onChange={e=>changeCycle("application_start_date",e.target.value)}/></label>
   <label><span>Application End</span><input type="date" value={cycleForm.application_end_date} onChange={e=>changeCycle("application_end_date",e.target.value)}/></label>
   <label><span>Registration Start</span><input type="date" value={cycleForm.registration_start_date} onChange={e=>changeCycle("registration_start_date",e.target.value)}/></label>
   <label><span>Registration End</span><input type="date" value={cycleForm.registration_end_date} onChange={e=>changeCycle("registration_end_date",e.target.value)}/></label>
   <label><span>Status</span><select value={cycleForm.status} onChange={e=>changeCycle("status",e.target.value)}>{["Draft","Active","Closed","Archived"].map(x=><option key={x}>{x}</option>)}</select></label>
   <label><span>CIPC Required</span><select value={cycleForm.cipc_required?"Yes":"No"} onChange={e=>changeCycle("cipc_required",e.target.value==="Yes")}><option>No</option><option>Yes</option></select></label>
  </div>
  <button className="button gold" onClick={createCycle}>Create Cycle</button>
 </Panel>

 <Panel title="Academic Cycles" text="The cycle status is shown directly in this table. Select Manage to change status and configure course offerings.">
  <Tbl rows={cycles} cols={["cycle_code","cycle_name","status","program_start_date","expected_completion_date","active_course_count","class_count"]} act={r=><Button onClick={()=>openCycle(r)}>Manage Cycle</Button>}/>
 </Panel>

 {selectedCycle&&<><Panel title={`Manage Cycle - ${selectedCycle.cycle_code}`} text="Change the lifecycle status for this academic cycle.">
  <div className="form-grid">
   <label><span>Cycle</span><input value={selectedCycle.cycle_code} disabled/></label>
   <label><span>Current / New Status</span><select value={cycleStatus} onChange={e=>setCycleStatus(e.target.value)}>{["Draft","Active","Closed","Archived"].map(x=><option key={x}>{x}</option>)}</select></label>
  </div>
  <button className="button gold" onClick={saveCycleStatus}>Save Cycle Status</button>
 </Panel>

 <Panel title={`Course Offerings - ${selectedCycle.cycle_code}`} text="A course must be active for the cycle before a class can be created for it.">
  <Tbl rows={offeringRows} cols={["course_code","course_name","nqf_level","credits","assessment_type","is_active"]} act={r=><Button onClick={()=>toggleOffering(r)}>{r.is_active?"Deactivate":"Activate"}</Button>}/>
 </Panel></>}

 <Panel title="Create Class" text="Create a class after activating the course for the selected cycle. Staff and learners can be assigned after creation.">
  <div className="form-grid">
   <label><span>Class Code *</span><input value={classForm.class_code} onChange={e=>changeClass("class_code",e.target.value)} placeholder="e.g. NVC-2027-A"/></label>
   <label><span>Class Name</span><input value={classForm.class_name} onChange={e=>changeClass("class_name",e.target.value)} placeholder="e.g. New Venture Creation Group A"/></label>
   <label><span>Cycle *</span><select value={classForm.cycle_code} onChange={e=>changeClass("cycle_code",e.target.value)}><option value="">Select cycle</option>{cycles.map(x=><option key={x.cycle_code} value={x.cycle_code}>{x.cycle_code} - {x.cycle_name||x.status}</option>)}</select></label>
   <label><span>Course *</span><select value={classForm.course_code} onChange={e=>changeClass("course_code",e.target.value)}><option value="">Select course</option>{courses.map(x=><option key={x.course_code} value={x.course_code}>{x.course_code} - {x.course_name}</option>)}</select></label>
   <label><span>Class Group</span><input value={classForm.class_group} onChange={e=>changeClass("class_group",e.target.value)} placeholder="e.g. A"/></label>
   <label><span>Status</span><select value={classForm.status} onChange={e=>changeClass("status",e.target.value)}>{["Draft","Active","Closed","Archived"].map(x=><option key={x}>{x}</option>)}</select></label>
  </div>
  <button className="button gold" onClick={createClass}>Create Class</button>
 </Panel>

 <Panel title="Classes" text="Class status, assigned Facilitator/Assessor and learner count are visible here.">
  <Tbl rows={classes} cols={["class_code","class_name","course_code","cycle_code","status","facilitator_name","assessor_name","moderator_name","active_learner_count"]} act={r=><Button onClick={()=>openClass(r)}>Manage Class</Button>}/>
 </Panel>

 {selectedClass&&<><Panel title={`Manage Class - ${selectedClass.class_code}`} text="Update class details and status.">
  <div className="form-grid">
   <label><span>Class Code</span><input value={selectedClass.class_code} disabled/></label>
   <label><span>Course</span><input value={selectedClass.course_code} disabled/></label>
   <label><span>Cycle</span><input value={selectedClass.cycle_code} disabled/></label>
   <label><span>Class Name</span><input value={classEdit.class_name} onChange={e=>setClassEdit(x=>({...x,class_name:e.target.value}))}/></label>
   <label><span>Class Group</span><input value={classEdit.class_group} onChange={e=>setClassEdit(x=>({...x,class_group:e.target.value}))}/></label>
   <label><span>Class Status</span><select value={classEdit.status} onChange={e=>setClassEdit(x=>({...x,status:e.target.value}))}>{["Draft","Active","Closed","Archived"].map(x=><option key={x}>{x}</option>)}</select></label>
  </div>
  <button className="button gold" onClick={saveClassDetails}>Save Class Details</button>
 </Panel>

 <Panel title={`Assign Academic Staff - ${selectedClass.class_code}`} text="Choose an active Facilitator, Assessor and Moderator. The Assessor and Moderator must be different staff members.">
  <div className="form-grid three">
   <label><span>Facilitator</span><select value={facilitatorCode} onChange={e=>setFacilitatorCode(e.target.value)}><option value="">Unassigned</option>{facilitators.map(x=><option key={x.staff_code} value={x.staff_code}>{x.staff_code} - {[x.first_name,x.middle_name,x.last_name].filter(Boolean).join(" ")}</option>)}</select></label>
   <label><span>Assessor</span><select value={assessorCode} onChange={e=>setAssessorCode(e.target.value)}><option value="">Unassigned</option>{assessors.map(x=><option key={x.staff_code} value={x.staff_code}>{x.staff_code} - {[x.first_name,x.middle_name,x.last_name].filter(Boolean).join(" ")}</option>)}</select></label>
   <label><span>Moderator</span><select value={moderatorCode} onChange={e=>setModeratorCode(e.target.value)}><option value="">Unassigned</option>{moderators.map(x=><option key={x.staff_code} value={x.staff_code}>{x.staff_code} - {[x.first_name,x.middle_name,x.last_name].filter(Boolean).join(" ")}</option>)}</select></label>
  </div>
  {!moderators.length&&<div className="alert error" style={{marginTop:"12px"}}>No active Moderator account exists. Create a staff member with the MODERATOR role under System Management first.</div>}
  <button className="button gold" onClick={saveStaffAssignment}>Save Staff Assignment</button>
 </Panel>

 <div className="two-col">
  <Panel title={`Learners in ${selectedClass.class_code}`} text="These learners are currently enrolled in this class.">
   <Tbl rows={classLearners} cols={["student_number","first_name","last_name","registration_status","class_enrolment_status","enrolled_at"]} act={r=><Button danger onClick={()=>removeLearner(r)}>Remove</Button>}/>
  </Panel>
  <Panel title="Eligible Learners" text="Only learners registered for this course/cycle and not already actively enrolled in another class are listed.">
   <Tbl rows={eligibleLearners} cols={["student_number","first_name","last_name","registration_status","course_code","cycle"]} act={r=><button className="button gold" onClick={()=>enrolLearner(r)}>Add to Class</button>}/>
  </Panel>
 </div></>}

 <Panel title="Academic Staff Options" text="Active staff accounts with Facilitator, Assessor and/or Moderator roles.">
  <Tbl rows={staffRows} cols={["staff_code","first_name","last_name","primary_role","can_facilitate","can_assess","can_moderate"]}/>
 </Panel></>
}


export function Timetable({token}){
 const list=useGet("/api/staff/admin/timetable?limit=200",token),opts=useGet("/api/staff/admin/timetable/options",token);const[f,setF]=useState({id:"",class_code:"",module_code:"",session_title:"",session_date:"",start_time:"",end_time:"",delivery_mode:"Physical",venue:"",meeting_link:"",notes:"",status:"Draft"}),[st,setSt]=useState({e:"",m:""});const classes=opts.data?.classes||[],mods=(opts.data?.modules||[]).filter(m=>!f.class_code||m.course_code===classes.find(c=>c.class_code===f.class_code)?.course_code);
 const save=async e=>{e.preventDefault();const body={class_code:f.class_code,module_code:f.module_code||null,session_title:f.session_title||null,session_date:f.session_date,start_time:f.start_time,end_time:f.end_time,delivery_mode:f.delivery_mode,venue:f.venue||null,meeting_link:f.meeting_link||null,notes:f.notes||null,...(!f.id?{status:f.status}:{})};try{await send(token,f.id?`/api/staff/admin/timetable/sessions/${f.id}`:"/api/staff/admin/timetable/sessions",f.id?"PUT":"POST",body);setSt({e:"",m:f.id?"Session updated.":"Session created."});setF({id:"",class_code:"",module_code:"",session_title:"",session_date:"",start_time:"",end_time:"",delivery_mode:"Physical",venue:"",meeting_link:"",notes:"",status:"Draft"});list.refresh()}catch(e){setSt({e:e.message,m:""})}};
 const status=async(r,s)=>{try{await send(token,`/api/staff/admin/timetable/sessions/${r.timetable_session_id}/status`+q({new_status:s}),"PATCH");list.refresh()}catch(e){setSt({e:e.message,m:""})}};
 const edit=r=>setF({id:r.timetable_session_id,class_code:r.class_code||"",module_code:r.module_code||"",session_title:r.session_title||"",session_date:r.session_date||"",start_time:String(r.start_time||"").slice(0,5),end_time:String(r.end_time||"").slice(0,5),delivery_mode:r.delivery_mode||"Physical",venue:r.venue||"",meeting_link:r.meeting_link||"",notes:r.notes||"",status:r.status||"Draft"});
 return <><div className="page-title"><div><span className="eyebrow">Academic Calendar</span><h1>Timetable</h1><p>Create, edit, publish, cancel and delete Draft sessions.</p></div></div><Alert {...st}/><form onSubmit={save}><Panel title={f.id?"Edit Session":"Create Timetable Session"}><div className="form-grid three"><label><span>Class</span><select required value={f.class_code} onChange={e=>setF({...f,class_code:e.target.value,module_code:""})}><option value="">Select class</option>{classes.map(x=><option value={x.class_code} key={x.class_code}>{x.class_code} — {x.class_name}</option>)}</select></label><label><span>Module</span><select value={f.module_code} onChange={e=>setF({...f,module_code:e.target.value})}><option value="">General / No Module</option>{mods.map(x=><option key={x.module_code} value={x.module_code}>{x.module_code} — {x.module_name}</option>)}</select></label><label><span>Title</span><input value={f.session_title} onChange={e=>setF({...f,session_title:e.target.value})}/></label><label><span>Date</span><input required type="date" value={f.session_date} onChange={e=>setF({...f,session_date:e.target.value})}/></label><label><span>Start</span><input required type="time" value={f.start_time} onChange={e=>setF({...f,start_time:e.target.value})}/></label><label><span>End</span><input required type="time" value={f.end_time} onChange={e=>setF({...f,end_time:e.target.value})}/></label><label><span>Delivery</span><select value={f.delivery_mode} onChange={e=>setF({...f,delivery_mode:e.target.value})}>{["Physical","Online","Blended"].map(x=><option key={x}>{x}</option>)}</select></label><label><span>Venue</span><input value={f.venue} onChange={e=>setF({...f,venue:e.target.value})}/></label><label><span>Meeting Link</span><input value={f.meeting_link} onChange={e=>setF({...f,meeting_link:e.target.value})}/></label></div><label><span>Notes</span><textarea value={f.notes} onChange={e=>setF({...f,notes:e.target.value})}/></label><button className="button gold">{f.id?"Save Session":"Create Session"}</button>{f.id&&<Button onClick={()=>setF({...f,id:""})}>Cancel Edit</Button>}</Panel></form><Panel title="Sessions"><Tbl rows={list.data?.sessions||[]} cols={["session_date","start_time","class_code","module_code","session_title","delivery_mode","status"]} act={r=><div className="button-row"><Button onClick={()=>edit(r)}>Edit</Button>{r.status!=="Published"&&<button className="button gold" onClick={()=>status(r,"Published")}>Publish</button>}{r.status!=="Cancelled"&&<Button onClick={()=>status(r,"Cancelled")}>Cancel</Button>}{r.status==="Draft"&&<Button danger onClick={async()=>{if(confirm("Delete this Draft session?")){await send(token,`/api/staff/admin/timetable/sessions/${r.timetable_session_id}`,"DELETE");list.refresh()}}}>Delete</Button>}</div>}/></Panel></>
}

export function Completion({token}){
 const list=useGet("/api/staff/admin/completion?limit=200",token),[sel,setSel]=useState(""),[detail,setDetail]=useState(null),[st,setSt]=useState({e:"",m:""});
 const open=async n=>{setSel(n);try{const x=await API.request(`/api/staff/admin/completion-management/${n}`,{},token);setDetail(x.data||x);setSt({e:"",m:""})}catch(e){setSt({e:e.message,m:""})}};
 const upd=async kind=>{let body;if(kind==="certification"){const s=prompt("Certificate status:","Pending");if(!s)return;body={certificate_status:s,certificate_number:prompt("Certificate number (optional):","")||null,certificate_date:prompt("Certificate date YYYY-MM-DD (optional):","")||null,certificate_received_date:prompt("Certificate received date YYYY-MM-DD (optional):","")||null,certificate_issued_date:prompt("Certificate issued date YYYY-MM-DD (optional):","")||null,notes:prompt("Notes (optional):","")||null}}else{const s=prompt("Graduation status:","Pending");if(!s)return;body={graduation_status:s,graduation_date:prompt("Graduation date YYYY-MM-DD (optional):","")||null,notes:prompt("Notes (optional):","")||null}}try{await send(token,`/api/staff/admin/completion-management/${sel}/${kind}`,"PATCH",body);setSt({e:"",m:`${h(kind)} updated.`});open(sel);list.refresh()}catch(e){setSt({e:e.message,m:""})}};
 const complete=Boolean(detail?.final_completion_confirmed);
 return <><div className="page-title"><div><span className="eyebrow">Completion</span><h1>Completion, Certification & Graduation</h1><p>Programme completion is calculated automatically from published assessment results. Admin tracks certification and graduation after academic completion.</p></div></div><Alert {...st}/><Panel title="Completion Dashboard" text="FISA-only learners complete when a published FISA is competent. FISA + EISA learners are not finally complete until the external EISA outcome is captured."><Tbl rows={list.data?.records||[]} cols={["student_number","course_code","course_name","assessment_type","fisa_mark","fisa_result","completion_state"]} act={r=><Button onClick={()=>open(r.student_number)}>Manage</Button>}/></Panel>{sel&&<><Panel title={`Academic Completion - ${sel}`} text="This status is system-calculated and cannot be manually overridden." actions={<span className="badge">{complete?"COMPLETED":"PENDING"}</span>}><Obj data={detail||{}}/></Panel><Panel title="Certification & Graduation" text="These are administrative tracking steps after the academic assessment outcome."><div className="button-row"><Button onClick={()=>upd("certification")}>Update Certification</Button><Button onClick={()=>upd("graduation")}>Update Graduation</Button></div></Panel></>}</>
}

export function Eisa({token}){
 const list=useGet("/api/staff/admin/eisa/learners?limit=200",token),[st,setSt]=useState({e:"",m:""});const tog=async r=>{try{await send(token,`/api/staff/admin/eisa/learners/${r.student_number}/eligibility`+q({eligible:!Boolean(r.eisa_eligible)}),"PATCH");setSt({e:"",m:"EISA eligibility updated."});list.refresh()}catch(e){setSt({e:e.message,m:""})}};return <><div className="page-title"><div><span className="eyebrow">EISA</span><h1>EISA Learner Eligibility</h1><p>Manage readiness for programmes that require the external EISA exit assessment.</p></div></div><Alert {...st}/><Panel title="EISA Learners"><Tbl rows={list.data?.learners||[]} act={r=><Button onClick={()=>tog(r)}>{r.eisa_eligible?"Mark Not Eligible":"Mark Eligible"}</Button>}/></Panel></>
}

export function Finance({token}){
 const dash=useGet("/api/staff/finance/dashboard",token),[search,setSearch]=useState(""),[students,setStudents]=useState([]),[sel,setSel]=useState(""),[detail,setDetail]=useState(null),[inv,setInv]=useState([]),[rec,setRec]=useState([]),[pay,setPay]=useState([]),[st,setSt]=useState({e:"",m:""});

 const find=async()=>{
  try{
   const x=await API.request(
    "/api/staff/finance/students"+q({search,limit:100}),
    {},
    token
   );
   setStudents(x.students||[]);
   setSt({e:"",m:""});
  }catch(e){
   setSt({e:e.message,m:""});
  }
 };

 const open=async n=>{
  setSel(n);
  setDetail(null);
  setInv([]);
  setRec([]);
  setPay([]);

  const results=await Promise.allSettled([
   API.request(`/api/staff/finance/students/${n}`,{},token),
   API.request(`/api/staff/finance/students/${n}/invoices`,{},token),
   API.request(`/api/staff/finance/students/${n}/receipts`,{},token),
   API.request(`/api/staff/finance/students/${n}/payments`,{},token)
  ]);

  const[a,b,c,d]=results;

  if(a.status==="fulfilled"){
   setDetail(a.value.data||a.value);
  }

  if(b.status==="fulfilled"){
   setInv(b.value.invoices||[]);
  }

  if(c.status==="fulfilled"){
   setRec(c.value.receipts||[]);
  }

  if(d.status==="fulfilled"){
   setPay(d.value.payments||[]);
  }

  const failed=results.find(
   x=>x.status==="rejected"
  );

  setSt({
   e:failed
    ?`${failed.reason?.message||"Finance data could not fully load."} Course finance/account setup may still be required.`
    :"",
   m:""
  });
 };

 const dashboard=(
  dash.data?.data
  ||dash.data
  ||{}
 );

 const recent=(
  dashboard.recent_payments
  ||[]
 );

 const summary=Object.fromEntries(
  Object.entries(dashboard).filter(
   ([key])=>key!=="recent_payments"
  )
 );

 return <><div className="page-title"><div><span className="eyebrow">Finance</span><h1>Finance Oversight</h1><p>Admin has visibility only; transactions remain CFO/Financial Officer functions.</p></div></div><Alert {...st}/><Panel title="Finance Dashboard"><Obj data={summary}/></Panel><Panel title="Recent Payments"><Tbl rows={recent}/></Panel><Panel title="Find Student Account"><div className="toolbar-grid"><input value={search} onChange={e=>setSearch(e.target.value)} placeholder="Student number or name"/><button className="button gold" onClick={find}>Search</button></div><Tbl rows={students} act={r=><Button onClick={()=>open(r.student_number)}>Open</Button>}/></Panel>{sel&&<><Panel title={`Finance - ${sel}`} actions={detail?<button className="button gold" onClick={()=>API.downloadFile(`/api/staff/finance/documents/statement/${sel}`,token,`${sel}_Statement.pdf`)}>Statement PDF</button>:null}><Obj data={detail||{}}/></Panel><div className="two-col"><Panel title="Invoices"><Tbl rows={inv} act={r=>r.invoice_number?<Button onClick={()=>API.downloadFile(`/api/staff/finance/documents/invoice/${r.invoice_number}`,token,`${r.invoice_number}.pdf`)}>PDF</Button>:null}/></Panel><Panel title="Receipts"><Tbl rows={rec} act={r=>r.receipt_number?<Button onClick={()=>API.downloadFile(`/api/staff/finance/documents/receipt/${r.receipt_number}`,token,`${r.receipt_number}.pdf`)}>PDF</Button>:null}/></Panel></div><Panel title="Payments"><Tbl rows={pay}/></Panel></>}</>
}

export function Communications({token}){
 const sm=useGet("/api/staff/communications/staff-messages",token);
 const stm=useGet("/api/staff/communications/student-messages",token);
 const ann=useGet("/api/staff/communications/announcements",token);
 const dir=useGet("/api/staff/communications/staff-directory",token);
 const courses=useGet("/api/staff/academic-management/courses",token);
 const cycles=useGet("/api/staff/academic-management/cycles",token);
 const classes=useGet("/api/staff/academic-management/classes",token);
 const[st,setSt]=useState({e:"",m:""});
 const[staffForm,setStaffForm]=useState({recipient_staff_code:"",subject:"",category:"General",message_body:""});
 const[announcement,setAnnouncement]=useState({title:"",message:"",announcement_type:"General",priority:"Normal",audience_type:"AllStudents",course_code:"",cycle_code:"",class_id:"",student_number:"",expires_at:""});
 const staffRows=dir.data?.staff||dir.data?.directory||[];
 const courseRows=courses.data?.courses||[];
 const cycleRows=cycles.data?.cycles||[];
 const classRows=classes.data?.classes||[];

 const sendStaffMessage=async()=>{
  if(!staffForm.recipient_staff_code){setSt({e:"Select a staff member.",m:""});return}
  if(!staffForm.subject.trim()){setSt({e:"Enter a message subject.",m:""});return}
  if(!staffForm.message_body.trim()){setSt({e:"Enter the staff message.",m:""});return}
  try{
   await send(token,"/api/staff/communications/staff-messages","POST",{recipient_staff_code:staffForm.recipient_staff_code,subject:staffForm.subject.trim(),category:staffForm.category.trim()||"General",message_body:staffForm.message_body.trim()});
   setStaffForm({recipient_staff_code:"",subject:"",category:"General",message_body:""});
   setSt({e:"",m:"Staff message sent."});
   sm.refresh();
  }catch(e){setSt({e:e.message,m:""})}
 };

 const createAnnouncement=async()=>{
  if(!announcement.title.trim()){setSt({e:"Enter an announcement title.",m:""});return}
  if(!announcement.message.trim()){setSt({e:"Enter the announcement message.",m:""});return}
  const payload={title:announcement.title.trim(),message:announcement.message.trim(),announcement_type:announcement.announcement_type,priority:announcement.priority,audience_type:announcement.audience_type,course_code:null,cycle_code:null,class_id:null,student_number:null,expires_at:announcement.expires_at?new Date(announcement.expires_at).toISOString():null};
  if(announcement.audience_type==="Course"){if(!announcement.course_code){setSt({e:"Select a course for this announcement.",m:""});return}payload.course_code=announcement.course_code}
  if(announcement.audience_type==="Cycle"){if(!announcement.cycle_code){setSt({e:"Select a cycle for this announcement.",m:""});return}payload.cycle_code=announcement.cycle_code}
  if(announcement.audience_type==="Class"){if(!announcement.class_id){setSt({e:"Select a class for this announcement.",m:""});return}payload.class_id=announcement.class_id}
  if(announcement.audience_type==="IndividualStudent"){if(!announcement.student_number.trim()){setSt({e:"Enter the student number for this announcement.",m:""});return}payload.student_number=announcement.student_number.trim()}
  try{
   await send(token,"/api/staff/communications/announcements","POST",payload);
   setAnnouncement({title:"",message:"",announcement_type:"General",priority:"Normal",audience_type:"AllStudents",course_code:"",cycle_code:"",class_id:"",student_number:"",expires_at:""});
   setSt({e:"",m:"Announcement saved as Draft."});
   ann.refresh();
  }catch(e){setSt({e:e.message,m:""})}
 };

 const reply=async r=>{const id=r.thread_id||r.id,body=prompt("Reply to student:","");if(!body)return;try{await send(token,`/api/staff/communications/student-messages/${id}/reply`,"POST",{message_body:body});stm.refresh()}catch(e){setSt({e:e.message,m:""})}};
 const publish=async r=>{const id=r.announcement_id||r.id;try{await send(token,`/api/staff/communications/announcements/${id}/publish`,"POST");setSt({e:"",m:"Announcement published."});ann.refresh()}catch(e){setSt({e:e.message,m:""})}};

 return <><div className="page-title"><div><span className="eyebrow">Communications</span><h1>Messages & Announcements</h1><p>Send staff messages and create targeted learner announcements using full forms.</p></div></div><Alert {...st}/>
 <div className="two-col">
  <Panel title="Send Staff Message" text="Choose an active staff account, then send the message."><div className="form-grid"><label><span>Staff Member</span><select value={staffForm.recipient_staff_code} onChange={e=>setStaffForm(x=>({...x,recipient_staff_code:e.target.value}))}><option value="">Select staff member</option>{staffRows.map(x=><option key={x.staff_code} value={x.staff_code}>{x.staff_code} - {[x.first_name,x.middle_name,x.last_name].filter(Boolean).join(" ")} - {x.role_code}</option>)}</select></label><label><span>Category</span><input value={staffForm.category} onChange={e=>setStaffForm(x=>({...x,category:e.target.value}))}/></label><label><span>Subject</span><input value={staffForm.subject} onChange={e=>setStaffForm(x=>({...x,subject:e.target.value}))}/></label></div><label><span>Message</span><textarea rows="6" value={staffForm.message_body} onChange={e=>setStaffForm(x=>({...x,message_body:e.target.value}))}/></label><button className="button gold" onClick={sendStaffMessage}>Send Staff Message</button></Panel>
  <Panel title="Create Announcement" text="Create as Draft, then publish it from the Announcements table after review."><div className="form-grid"><label><span>Title</span><input value={announcement.title} onChange={e=>setAnnouncement(x=>({...x,title:e.target.value}))}/></label><label><span>Type</span><select value={announcement.announcement_type} onChange={e=>setAnnouncement(x=>({...x,announcement_type:e.target.value}))}>{["General","Academic","Assessment","Timetable","Finance","Documents","Emergency"].map(x=><option key={x}>{x}</option>)}</select></label><label><span>Priority</span><select value={announcement.priority} onChange={e=>setAnnouncement(x=>({...x,priority:e.target.value}))}>{["Normal","Important","Urgent"].map(x=><option key={x}>{x}</option>)}</select></label><label><span>Audience</span><select value={announcement.audience_type} onChange={e=>setAnnouncement(x=>({...x,audience_type:e.target.value,course_code:"",cycle_code:"",class_id:"",student_number:""}))}>{["AllStudents","Course","Cycle","Class","IndividualStudent"].map(x=><option key={x} value={x}>{x}</option>)}</select></label>{announcement.audience_type==="Course"&&<label><span>Course</span><select value={announcement.course_code} onChange={e=>setAnnouncement(x=>({...x,course_code:e.target.value}))}><option value="">Select course</option>{courseRows.map(x=><option key={x.course_code} value={x.course_code}>{x.course_code} - {x.course_name}</option>)}</select></label>}{announcement.audience_type==="Cycle"&&<label><span>Cycle</span><select value={announcement.cycle_code} onChange={e=>setAnnouncement(x=>({...x,cycle_code:e.target.value}))}><option value="">Select cycle</option>{cycleRows.map(x=><option key={x.cycle_code} value={x.cycle_code}>{x.cycle_code} - {x.cycle_name||x.status}</option>)}</select></label>}{announcement.audience_type==="Class"&&<label><span>Class</span><select value={announcement.class_id} onChange={e=>setAnnouncement(x=>({...x,class_id:e.target.value}))}><option value="">Select class</option>{classRows.map(x=><option key={x.id} value={x.id}>{x.class_code} - {x.class_name||x.course_code}</option>)}</select></label>}{announcement.audience_type==="IndividualStudent"&&<label><span>Student Number</span><input value={announcement.student_number} onChange={e=>setAnnouncement(x=>({...x,student_number:e.target.value}))} placeholder="e.g. 20260010"/></label>}<label><span>Expires At (optional)</span><input type="datetime-local" value={announcement.expires_at} onChange={e=>setAnnouncement(x=>({...x,expires_at:e.target.value}))}/></label></div><label><span>Announcement</span><textarea rows="6" value={announcement.message} onChange={e=>setAnnouncement(x=>({...x,message:e.target.value}))}/></label><button className="button gold" onClick={createAnnouncement}>Make Announcement</button></Panel>
 </div>
 <Panel title="Staff Directory"><Tbl rows={staffRows}/></Panel><Panel title="Student Messages"><Tbl rows={stm.data?.messages||stm.data?.threads||[]} act={r=><div className="button-row"><Button onClick={()=>reply(r)}>Reply</Button><Button onClick={async()=>{try{await send(token,`/api/staff/communications/student-messages/${r.thread_id||r.id}/resolve`,"PATCH");stm.refresh()}catch(e){setSt({e:e.message,m:""})}}}>Resolve</Button></div>}/></Panel><Panel title="Staff Messages"><Tbl rows={sm.data?.messages||sm.data?.threads||[]}/></Panel><Panel title="Announcements"><Tbl rows={ann.data?.announcements||[]} act={r=>String(r.status||"").toLowerCase()!=="published"?<button className="button gold" onClick={()=>publish(r)}>Publish</button>:null}/></Panel></>
}


export function Support({token}){
 const[path,setPath]=useState("/api/staff/student-support/tickets");
 const list=useGet(path,token);

 const[selected,setSelected]=useState(null);
 const[detail,setDetail]=useState(null);
 const[replyText,setReplyText]=useState("");
 const[newStatus,setNewStatus]=useState("Open");
 const[filterStatus,setFilterStatus]=useState("");
 const[st,setSt]=useState({e:"",m:""});

 const tickets=list.data?.tickets||[];
 const ticket=detail?.ticket||selected||null;
 const messages=detail?.messages||[];

 const openTicket=async row=>{
  const id=row.ticket_id||row.id;

  if(!id){
   setSt({
    e:"This ticket does not have a valid ticket ID.",
    m:""
   });
   return;
  }

  try{
   const x=await API.request(
    `/api/staff/student-support/tickets/${id}`,
    {},
    token
   );

   const data=x.data||x;

   setSelected(
    data.ticket||row
   );

   setDetail(
    data
   );

   setNewStatus(
    data.ticket?.status
    ||row.status
    ||"Open"
   );

   setReplyText("");

   setSt({
    e:"",
    m:""
   });
  }catch(e){
   setSt({
    e:e.message,
    m:""
   });
  }
 };

 const reloadTicket=async()=>{
  const id=(
   ticket?.ticket_id
   ||ticket?.id
  );

  if(!id)return;

  try{
   const x=await API.request(
    `/api/staff/student-support/tickets/${id}`,
    {},
    token
   );

   const data=x.data||x;

   setDetail(
    data
   );

   setSelected(
    data.ticket||ticket
   );

   setNewStatus(
    data.ticket?.status
    ||newStatus
   );
  }catch(e){
   setSt({
    e:e.message,
    m:""
   });
  }
 };

 const sendReply=async()=>{
  const id=(
   ticket?.ticket_id
   ||ticket?.id
  );

  if(!id){
   setSt({
    e:"Open a support ticket first.",
    m:""
   });
   return;
  }

  const body=replyText.trim();

  if(!body){
   setSt({
    e:"Enter a reply message.",
    m:""
   });
   return;
  }

  try{
   await send(
    token,
    `/api/staff/student-support/tickets/${id}/reply`,
    "POST",
    {
     message_body:body
    }
   );

   setReplyText("");

   setSt({
    e:"",
    m:"Reply sent to the student."
   });

   list.refresh();

   await reloadTicket();
  }catch(e){
   setSt({
    e:e.message,
    m:""
   });
  }
 };

 const updateStatus=async()=>{
  const id=(
   ticket?.ticket_id
   ||ticket?.id
  );

  if(!id){
   setSt({
    e:"Open a support ticket first.",
    m:""
   });
   return;
  }

  try{
   await send(
    token,
    `/api/staff/student-support/tickets/${id}/status`,
    "PATCH",
    {
     status:newStatus
    }
   );

   setSt({
    e:"",
    m:`Ticket status updated to ${newStatus}.`
   });

   list.refresh();

   await reloadTicket();
  }catch(e){
   setSt({
    e:e.message,
    m:""
   });
  }
 };

 const applyFilter=()=>{
  setPath(
   "/api/staff/student-support/tickets"
   +q({
    status:filterStatus
   })
  );
 };

 const closed=(
  String(
   ticket?.status||""
  ).toLowerCase()==="closed"
  ||String(
   ticket?.status||""
  ).toLowerCase()==="resolved"
 );

 return <><div className="page-title"><div><span className="eyebrow">Student Services</span><h1>Student Support</h1><p>Open a support ticket, read the full conversation, reply to the learner and manage ticket status.</p></div></div><Alert {...st}/>

 <Panel title="Ticket Filter">
  <div className="toolbar-grid">
   <select
    value={filterStatus}
    onChange={e=>setFilterStatus(e.target.value)}
   >
    <option value="">All statuses</option>
    {["Open","InProgress","AwaitingStudent","Resolved","Closed"].map(x=><option key={x} value={x}>{h(x)}</option>)}
   </select>
   <button
    className="button gold"
    onClick={applyFilter}
   >
    Apply Filter
   </button>
   <Button onClick={list.refresh}>Refresh</Button>
  </div>
 </Panel>

 <Panel title={`Support Tickets (${tickets.length})`} text="Select Open Ticket to view the original request and all replies.">
  <Alert e={list.e}/>
  <Tbl
   rows={tickets}
   cols={["ticket_number","student_number","category","subject","priority","status","assigned_staff_code","updated_at"]}
   act={r=><button className="button gold" onClick={()=>openTicket(r)}>Open Ticket</button>}
  />
 </Panel>

 {ticket&&<><Panel
  title={`Ticket ${ticket.ticket_number||""}`}
  text={`Student ${ticket.student_number||"—"} • ${ticket.subject||""}`}
 >
  <Obj data={ticket}/>
 </Panel>

 <Panel title="Conversation" text="Student and staff messages are shown in chronological order.">
  {!messages.length
   ?<div className="empty">No conversation messages are available.</div>
   :<div className="table-wrap">
    <table>
     <thead>
      <tr>
       <th>Sender</th>
       <th>Code</th>
       <th>Message</th>
       <th>Sent At</th>
       <th>Read At</th>
      </tr>
     </thead>
     <tbody>
      {messages.map((m,i)=><tr key={m.id||m.message_id||i}>
       <td><span className="badge">{v(m.sender_type)}</span></td>
       <td>{v(m.sender_code)}</td>
       <td style={{whiteSpace:"pre-wrap",minWidth:"320px"}}>{v(m.message_body)}</td>
       <td>{v(m.sent_at||m.created_at)}</td>
       <td>{v(m.read_at)}</td>
      </tr>)}
     </tbody>
    </table>
   </div>}
 </Panel>

 <div className="two-col">
  <Panel
   title="Reply to Ticket"
   text={closed
    ?"This ticket is Resolved/Closed. Re-open it by changing the status before sending another reply."
    :"Your reply will be added to the conversation and the ticket will move to Awaiting Student."
   }
  >
   <label>
    <span>Reply</span>
    <textarea
     rows="7"
     value={replyText}
     disabled={closed}
     onChange={e=>setReplyText(e.target.value)}
     placeholder="Type your reply to the student..."
    />
   </label>
   <button
    className="button gold"
    disabled={closed||!replyText.trim()}
    onClick={sendReply}
   >
    Send Reply
   </button>
  </Panel>

  <Panel
   title="Ticket Status"
   text="Use only the supported SMS ticket statuses."
  >
   <label>
    <span>Status</span>
    <select
     value={newStatus}
     onChange={e=>setNewStatus(e.target.value)}
    >
     {["Open","InProgress","AwaitingStudent","Resolved","Closed"].map(x=><option key={x} value={x}>{h(x)}</option>)}
    </select>
   </label>
   <button
    className="button gold"
    onClick={updateStatus}
   >
    Update Status
   </button>
  </Panel>
 </div></>}</>
}


export function Notifications({token}){
 const list=useGet("/api/staff/notifications?limit=100",token);return <><div className="page-title"><div><span className="eyebrow">Notifications</span><h1>Notification Centre</h1><p>System notifications for your staff account.</p></div><button className="button gold" onClick={async()=>{await send(token,"/api/staff/notifications/read-all","PATCH");list.refresh()}}>Mark All Read</button></div><Panel title="Notifications"><Tbl rows={list.data?.notifications||[]} act={r=>r.is_read?null:<Button onClick={async()=>{await send(token,`/api/staff/notifications/${r.id}/read`,"PATCH");list.refresh()}}>Mark Read</Button>}/></Panel></>
}

export function Reports({token}){
 const cat=useGet("/api/staff/reports/catalog",token),[prev,setPrev]=useState(null),[st,setSt]=useState({e:"",m:""});const view=async r=>{const code=r.report_code||r.code;try{const x=await API.request(`/api/staff/reports/${code}`,{},token);setPrev(x.report||x)}catch(e){setSt({e:e.message,m:""})}};return <><div className="page-title"><div><span className="eyebrow">QA & Compliance</span><h1>Reports</h1><p>Preview and export supported institutional reports.</p></div></div><Alert {...st}/><Panel title="Report Catalogue"><Tbl rows={cat.data?.reports||[]} act={r=><div className="button-row"><Button onClick={()=>view(r)}>Preview</Button><button className="button gold" onClick={()=>API.downloadFile(`/api/staff/reports/${r.report_code||r.code}/pdf`,token,`${r.report_code||r.code}.pdf`)}>PDF</button></div>}/></Panel>{prev&&<Panel title="Preview"><Obj data={prev}/></Panel>}</>
}

export function Audit({token}){
 const[actor,setActor]=useState(""),[module,setModule]=useState(""),[action,setAction]=useState(""),[path,setPath]=useState("/api/staff/audit?limit=200");const list=useGet(path,token);return <><div className="page-title"><div><span className="eyebrow">Governance</span><h1>Audit Log</h1><p>Search staff and system activity.</p></div></div><Panel title="Filters"><div className="form-grid three"><label><span>Staff Code</span><input value={actor} onChange={e=>setActor(e.target.value)}/></label><label><span>Module</span><input value={module} onChange={e=>setModule(e.target.value)}/></label><label><span>Action</span><input value={action} onChange={e=>setAction(e.target.value)}/></label></div><button className="button gold" onClick={()=>setPath("/api/staff/audit"+q({actor_staff_code:actor,module_code:module,action_code:action,limit:200}))}>Search</button></Panel><Panel title="Audit Records"><Tbl rows={list.data?.logs||[]}/></Panel></>
}

const ROLES=["ADMIN","PRINCIPAL","HR","CFO","FINANCIAL_OFFICER","FACILITATOR","ASSESSOR","MODERATOR"];
export function System({token}){
 const settings=useGet("/api/staff/admin/system-management/settings",token);
 const accounts=useGet("/api/staff/admin/system-management/staff-accounts",token);
 const roles=useGet("/api/staff/admin/system-management/roles",token);
 const emps=useGet("/api/staff/admin/system-management/employee-options",token);
 const perms=useGet("/api/staff/admin/system-management/permissions",token);

 const[st,setSt]=useState({e:"",m:""});
 const[mode,setMode]=useState("new");

 const[newStaff,setNewStaff]=useState({
  first_name:"",
  middle_name:"",
  last_name:"",
  email:"",
  phone_number:"",
  national_id:"",
  job_title:"",
  department:"",
  employment_type:"Permanent",
  start_date:"",
  staff_code:"",
  role_code:"ADMIN",
  temporary_password:"",
  temporary_pin:""
 });

 const[existing,setExisting]=useState({
  employee_id:"",
  staff_code:"",
  role_code:"ADMIN",
  temporary_password:"",
  temporary_pin:""
 });

 const[selectedSetting,setSelectedSetting]=useState(null);
 const[settingValue,setSettingValue]=useState("");

 const[selectedRole,setSelectedRole]=useState(null);
 const[selectedPermissions,setSelectedPermissions]=useState([]);

 const availableEmployees=(emps.data?.employees||[]).filter(x=>!x.staff_code);
 const permissionRows=perms.data?.permissions||[];
 const roleRows=(roles.data?.roles||[]).filter(x=>x.role_code!=="CEO");

 const createNewStaff=async()=>{
  if(newStaff.temporary_pin.length!==5){
   setSt({e:"Temporary PIN must be exactly 5 digits.",m:""});
   return;
  }

  try{
   const result=await send(
    token,
    "/api/staff/desktop-v5/staff-members",
    "POST",
    {
     ...newStaff,
     middle_name:newStaff.middle_name||null,
     phone_number:newStaff.phone_number||null,
     national_id:newStaff.national_id||null,
     department:newStaff.department||null,
     employment_type:newStaff.employment_type||null,
     start_date:newStaff.start_date||null,
     staff_code:newStaff.staff_code.toUpperCase(),
     role_code:newStaff.role_code.toUpperCase()
    }
   );

   setSt({
    e:"",
    m:`Staff member ${result.staff_account?.staff_code||newStaff.staff_code} created successfully.`
   });

   setNewStaff({
    first_name:"",
    middle_name:"",
    last_name:"",
    email:"",
    phone_number:"",
    national_id:"",
    job_title:"",
    department:"",
    employment_type:"Permanent",
    start_date:"",
    staff_code:"",
    role_code:"ADMIN",
    temporary_password:"",
    temporary_pin:""
   });

   accounts.refresh();
   emps.refresh();
  }catch(e){
   setSt({e:e.message,m:""});
  }
 };

 const createExistingAccount=async()=>{
  if(existing.temporary_pin.length!==5){
   setSt({e:"Temporary PIN must be exactly 5 digits.",m:""});
   return;
  }

  try{
   await send(
    token,
    "/api/staff/admin/system-management/staff-accounts",
    "POST",
    {
     ...existing,
     staff_code:existing.staff_code.toUpperCase(),
     role_code:existing.role_code.toUpperCase()
    }
   );

   setSt({
    e:"",
    m:"Staff system account created."
   });

   setExisting({
    employee_id:"",
    staff_code:"",
    role_code:"ADMIN",
    temporary_password:"",
    temporary_pin:""
   });

   accounts.refresh();
   emps.refresh();
  }catch(e){
   setSt({e:e.message,m:""});
  }
 };

 const openSetting=row=>{
  setSelectedSetting(row);
  setSettingValue(
   row.setting_value
   ??row.value
   ??row.value_text
   ??""
  );
 };

 const saveSetting=async()=>{
  if(!selectedSetting)return;
  const key=
   selectedSetting.setting_key
   ||selectedSetting.key
   ||selectedSetting.name
   ||selectedSetting.code;

  try{
   await send(
    token,
    `/api/staff/admin/system-management/settings/${encodeURIComponent(key)}`,
    "PATCH",
    {value:String(settingValue)}
   );
   settings.refresh();
   setSt({e:"",m:`Setting ${key} updated.`});
  }catch(e){
   setSt({e:e.message,m:""});
  }
 };

 const openRole=row=>{
  setSelectedRole(row);
  setSelectedPermissions([...(row.permissions||[])]);
 };

 const togglePermission=code=>{
  setSelectedPermissions(current=>
   current.includes(code)
    ?current.filter(x=>x!==code)
    :[...current,code]
  );
 };

 const saveRole=async()=>{
  if(!selectedRole)return;
  try{
   await send(
    token,
    `/api/staff/admin/system-management/roles/${selectedRole.role_code}/permissions`,
    "PATCH",
    {permission_codes:selectedPermissions}
   );
   roles.refresh();
   setSt({e:"",m:`Permissions updated for ${selectedRole.role_code}.`});
  }catch(e){
   setSt({e:e.message,m:""});
  }
 };

 return <>
  <div className="page-title">
   <div>
    <span className="eyebrow">Administration</span>
    <h1>System Management</h1>
    <p>Create staff properly, manage system settings, staff accounts and role permissions.</p>
   </div>
  </div>

  <Alert {...st}/>

  <Panel
   title="Create Staff"
   text="Create a new employee and system account together, or create system access for an existing employee."
  >
   <div className="button-row" style={{marginBottom:"14px"}}>
    <button
     className={`button ${mode==="new"?"gold":"light"}`}
     onClick={()=>setMode("new")}
    >
     New Staff Member
    </button>
    <button
     className={`button ${mode==="existing"?"gold":"light"}`}
     onClick={()=>setMode("existing")}
    >
     Existing Employee Account
    </button>
   </div>

   {mode==="new"?<>
    <div className="form-grid three">
     <label><span>First Name *</span><input value={newStaff.first_name} onChange={e=>setNewStaff(x=>({...x,first_name:e.target.value}))}/></label>
     <label><span>Middle Name</span><input value={newStaff.middle_name} onChange={e=>setNewStaff(x=>({...x,middle_name:e.target.value}))}/></label>
     <label><span>Last Name *</span><input value={newStaff.last_name} onChange={e=>setNewStaff(x=>({...x,last_name:e.target.value}))}/></label>
     <label><span>Email *</span><input type="email" value={newStaff.email} onChange={e=>setNewStaff(x=>({...x,email:e.target.value}))}/></label>
     <label><span>Phone</span><input value={newStaff.phone_number} onChange={e=>setNewStaff(x=>({...x,phone_number:e.target.value}))}/></label>
     <label><span>National ID</span><input value={newStaff.national_id} onChange={e=>setNewStaff(x=>({...x,national_id:e.target.value}))}/></label>
     <label><span>Job Title *</span><input value={newStaff.job_title} onChange={e=>setNewStaff(x=>({...x,job_title:e.target.value}))}/></label>
     <label><span>Department</span><input value={newStaff.department} onChange={e=>setNewStaff(x=>({...x,department:e.target.value}))}/></label>
     <label><span>Employment Type</span><input value={newStaff.employment_type} onChange={e=>setNewStaff(x=>({...x,employment_type:e.target.value}))}/></label>
     <label><span>Start Date</span><input type="date" value={newStaff.start_date} onChange={e=>setNewStaff(x=>({...x,start_date:e.target.value}))}/></label>
     <label><span>Staff Code *</span><input value={newStaff.staff_code} onChange={e=>setNewStaff(x=>({...x,staff_code:e.target.value.toUpperCase()}))} placeholder="e.g. FAC0002"/></label>
     <label><span>Primary Role *</span><select value={newStaff.role_code} onChange={e=>setNewStaff(x=>({...x,role_code:e.target.value}))}>{ROLES.map(x=><option key={x}>{x}</option>)}</select></label>
     <label><span>Temporary Password *</span><input type="password" value={newStaff.temporary_password} onChange={e=>setNewStaff(x=>({...x,temporary_password:e.target.value}))}/></label>
     <label><span>Temporary 5-digit PIN *</span><input value={newStaff.temporary_pin} onChange={e=>setNewStaff(x=>({...x,temporary_pin:e.target.value.replace(/\D/g,"").slice(0,5)}))}/></label>
    </div>
    <button className="button gold" onClick={createNewStaff}>Create Staff Member & Account</button>
   </>:<>
    <div className="form-grid three">
     <label><span>Employee *</span><select value={existing.employee_id} onChange={e=>setExisting(x=>({...x,employee_id:e.target.value}))}><option value="">Select employee</option>{availableEmployees.map(x=><option key={x.employee_id} value={x.employee_id}>{x.employee_number||""} — {x.first_name} {x.last_name} — {x.job_title||""}</option>)}</select></label>
     <label><span>Staff Code *</span><input value={existing.staff_code} onChange={e=>setExisting(x=>({...x,staff_code:e.target.value.toUpperCase()}))}/></label>
     <label><span>Role *</span><select value={existing.role_code} onChange={e=>setExisting(x=>({...x,role_code:e.target.value}))}>{ROLES.map(x=><option key={x}>{x}</option>)}</select></label>
     <label><span>Temporary Password *</span><input type="password" value={existing.temporary_password} onChange={e=>setExisting(x=>({...x,temporary_password:e.target.value}))}/></label>
     <label><span>Temporary 5-digit PIN *</span><input value={existing.temporary_pin} onChange={e=>setExisting(x=>({...x,temporary_pin:e.target.value.replace(/\D/g,"").slice(0,5)}))}/></label>
    </div>
    <button className="button gold" onClick={createExistingAccount}>Create System Account</button>
   </>}
  </Panel>

  <Panel title="Staff Accounts">
   <Tbl
    rows={accounts.data?.staff_accounts||[]}
    cols={["staff_code","employee_number","first_name","last_name","role_code","job_title","is_active","last_login_at"]}
    act={r=><Button
     danger={r.is_active}
     onClick={async()=>{
      if(!confirm(`${r.is_active?"Deactivate":"Activate"} ${r.staff_code}?`))return;
      try{
       await send(
        token,
        `/api/staff/admin/system-management/staff-accounts/${r.staff_code}/status`,
        "PATCH",
        {is_active:!r.is_active}
       );
       accounts.refresh();
      }catch(e){
       setSt({e:e.message,m:""});
      }
     }}
    >{r.is_active?"Deactivate":"Activate"}</Button>}
   />
  </Panel>

  <Panel title="System Settings">
   <Tbl
    rows={settings.data?.settings||[]}
    act={r=><Button onClick={()=>openSetting(r)}>Edit</Button>}
   />
   {selectedSetting&&<div className="form-grid" style={{marginTop:"16px"}}>
    <label><span>Setting</span><input disabled value={selectedSetting.setting_key||selectedSetting.key||""}/></label>
    <label><span>Value</span><input value={settingValue} onChange={e=>setSettingValue(e.target.value)}/></label>
    <div><button className="button gold" onClick={saveSetting}>Save Setting</button></div>
   </div>}
  </Panel>

  <Panel title="Roles & Permissions" text="CEO remains excluded from the Glen Moniques SMS roles.">
   <Tbl
    rows={roleRows}
    cols={["role_code","role_name","permissions"]}
    act={r=><Button onClick={()=>openRole(r)}>Manage Permissions</Button>}
   />
   {selectedRole&&<div style={{marginTop:"18px"}}>
    <h3>{selectedRole.role_code} Permissions</h3>
    <div className="permission-grid">
     {permissionRows.map(p=>{
      const code=p.permission_code;
      return <label key={code} style={{display:"flex",gap:"8px",alignItems:"center"}}>
       <input type="checkbox" checked={selectedPermissions.includes(code)} onChange={()=>togglePermission(code)}/>
       <span>{code}</span>
      </label>;
     })}
    </div>
    <button className="button gold" onClick={saveRole}>Save Role Permissions</button>
   </div>}
  </Panel>

  <Panel title="Permission Catalogue">
   <Tbl rows={permissionRows}/>
  </Panel>
 </>;
}


export function Profile({token}){
 const p=useGet("/api/staff/profile",token),[st,setSt]=useState({e:"",m:""});

 const contact=async()=>{
  const d=p.data?.data||{};
  const employee=d.employee||d;
  const email=prompt("Email:",employee.email||d.email||"");
  if(email===null)return;
  const phone=prompt("Phone number:",employee.phone_number||d.phone_number||"");
  try{
   await send(token,"/api/staff/profile/contact","PATCH",{email:email||null,phone_number:phone||null});
   setSt({e:"",m:"Contact updated."});
   p.refresh();
  }catch(e){setSt({e:e.message,m:""})}
 };

 const password=async()=>{
  const current=prompt("Current password:","");
  if(!current)return;
  const next=prompt("New password:","");
  if(!next)return;
  try{
   await send(token,"/api/staff/profile/change-password","POST",{current_password:current,new_password:next});
   setSt({e:"",m:"Password changed."});
  }catch(e){setSt({e:e.message,m:""})}
 };

 const pin=async()=>{
  const current=prompt("Current PIN:","");
  if(!current)return;
  const next=prompt("New 5-digit PIN:","");
  if(!next)return;
  try{
   await send(token,"/api/staff/profile/change-pin","POST",{current_pin:current,new_pin:next});
   setSt({e:"",m:"PIN changed."});
  }catch(e){setSt({e:e.message,m:""})}
 };

 const d=p.data?.data||{};
 const role=d.role||{};
 const employee=d.employee||{};
 const account=d.account||{};

 const display=(value,fallback="—")=>{
  if(value===null||value===undefined||value==="")return fallback;
  return String(value);
 };

 const yesNo=value=>{
  if(value===null||value===undefined||value==="")return "—";
  return Boolean(value)?"Yes":"No";
 };

 const prettyRole=value=>{
  if(!value)return "—";
  return String(value)
   .toLowerCase()
   .split("_")
   .map(x=>x.charAt(0).toUpperCase()+x.slice(1))
   .join(" ");
 };

 const fmtDateTime=value=>{
  if(!value)return "—";
  const dt=new Date(value);
  if(Number.isNaN(dt.getTime()))return display(value);
  return dt.toLocaleString("en-ZA",{
   year:"numeric",
   month:"2-digit",
   day:"2-digit",
   hour:"2-digit",
   minute:"2-digit"
  });
 };

 const fmtDate=value=>{
  if(!value)return "—";
  const dt=new Date(value);
  if(Number.isNaN(dt.getTime()))return display(value);
  return dt.toLocaleDateString("en-ZA",{
   year:"numeric",
   month:"2-digit",
   day:"2-digit"
  });
 };

 const fullName=
  employee.full_name||
  [employee.first_name,employee.middle_name,employee.last_name]
   .filter(Boolean)
   .join(" ")||
  d.full_name||
  "—";

 const staffCode=
  d.staff_code||
  account.staff_code||
  employee.staff_code||
  "—";

 const roleName=
  role.role_name||
  role.name||
  prettyRole(role.role_code||d.role_code);

 const roleDescription=
  role.description||
  role.role_description||
  "Access and responsibilities assigned to this staff role.";

 const cardStyle={
  background:"#ffffff",
  border:"1px solid #dfe7f1",
  borderRadius:"14px",
  padding:"18px 20px",
  boxShadow:"0 2px 8px rgba(15,35,75,.04)",
  minWidth:0
 };

 const cardTitleStyle={
  display:"flex",
  alignItems:"center",
  gap:"10px",
  marginBottom:"14px",
  paddingBottom:"12px",
  borderBottom:"1px solid #e8edf4",
  color:"#102653",
  fontWeight:800,
  fontSize:"16px"
 };

 const iconStyle={
  width:"34px",
  height:"34px",
  borderRadius:"50%",
  background:"#edf5ff",
  color:"#1f6fc8",
  display:"inline-flex",
  alignItems:"center",
  justifyContent:"center",
  fontWeight:800,
  flex:"0 0 34px"
 };

 const rowStyle={
  display:"grid",
  gridTemplateColumns:"minmax(145px, 34%) 1fr",
  gap:"14px",
  padding:"8px 0",
  borderBottom:"1px solid #eef2f7",
  alignItems:"start"
 };

 const labelStyle={
  color:"#65758d",
  fontSize:"13px",
  fontWeight:600
 };

 const valueStyle={
  color:"#13284b",
  fontSize:"14px",
  fontWeight:600,
  overflowWrap:"anywhere"
 };

 const DetailRow=({label,value,last=false})=>
  <div style={{...rowStyle,borderBottom:last?"none":rowStyle.borderBottom}}>
   <div style={labelStyle}>{label}</div>
   <div style={valueStyle}>{value}</div>
  </div>;

 const Status=({active})=>
  <span style={{
   display:"inline-flex",
   alignItems:"center",
   padding:"4px 11px",
   borderRadius:"999px",
   fontSize:"12px",
   fontWeight:800,
   background:active?"#dcf7e5":"#f4e6e6",
   color:active?"#147a38":"#a03232"
  }}>
   {active?"Active":"Inactive"}
  </span>;

 return <>
  <div className="page-title">
   <div>
    <span className="eyebrow">My Account</span>
    <h1>Staff Profile & Security</h1>
    <p>Your staff identity, role, employment details and account security.</p>
   </div>
   <div className="page-actions">
    <Button onClick={contact}>Edit Contact</Button>
    <Button onClick={password}>Change Password</Button>
    <Button onClick={pin}>Change PIN</Button>
   </div>
  </div>

  <Alert {...st}/>

  <Panel title="Profile">
   <div style={{
    display:"grid",
    gridTemplateColumns:"repeat(auto-fit,minmax(360px,1fr))",
    gap:"14px"
   }}>

    <div style={cardStyle}>
     <div style={cardTitleStyle}>
      <span style={iconStyle}>ID</span>
      <span>Staff Code</span>
     </div>
     <div style={{
      color:"#102653",
      fontWeight:900,
      fontSize:"23px",
      letterSpacing:".3px",
      padding:"4px 2px 8px"
     }}>
      {display(staffCode)}
     </div>
    </div>

    <div style={cardStyle}>
     <div style={cardTitleStyle}>
      <span style={iconStyle}>R</span>
      <span>Role</span>
     </div>
     <DetailRow label="Role" value={display(roleName)}/>
     <DetailRow label="Description" value={display(roleDescription)} last/>
    </div>

    <div style={cardStyle}>
     <div style={cardTitleStyle}>
      <span style={iconStyle}>P</span>
      <span>Employee</span>
     </div>
     <DetailRow label="Employee ID" value={display(employee.employee_id||employee.id)}/>
     <DetailRow label="Employee Number" value={display(employee.employee_number)}/>
     <DetailRow label="Full Name" value={display(fullName)}/>
     <DetailRow label="Email" value={display(employee.email||d.email)}/>
     <DetailRow label="Phone Number" value={display(employee.phone_number||d.phone_number)}/>
     <DetailRow label="Job Title" value={display(employee.job_title)}/>
     <DetailRow label="Department" value={display(employee.department)}/>
     <DetailRow label="Employment Type" value={display(employee.employment_type)}/>
     <DetailRow
      label="Employment Status"
      value={
       String(employee.employment_status||"").toLowerCase()==="active"
        ?<Status active/>
        :display(employee.employment_status)
      }
     />
     <DetailRow label="Start Date" value={fmtDate(employee.start_date)}/>
     <DetailRow label="End Date" value={fmtDate(employee.end_date)}/>
     <DetailRow label="System Access" value={yesNo(employee.requires_system_access)} last/>
    </div>

    <div style={cardStyle}>
     <div style={cardTitleStyle}>
      <span style={iconStyle}>S</span>
      <span>Account</span>
     </div>
     <DetailRow label="Account Status" value={<Status active={Boolean(account.is_active)}/>}/>
     <DetailRow label="Must Change Password" value={yesNo(account.must_change_password)}/>
     <DetailRow label="Must Change PIN" value={yesNo(account.must_change_pin)}/>
     <DetailRow label="Failed Login Attempts" value={display(account.failed_login_attempts,"0")}/>
     <DetailRow label="Locked Until" value={fmtDateTime(account.locked_until)}/>
     <DetailRow label="Credentials Issued At" value={fmtDateTime(account.credentials_issued_at)}/>
     <DetailRow label="Password Changed At" value={fmtDateTime(account.password_changed_at)}/>
     <DetailRow label="PIN Changed At" value={fmtDateTime(account.pin_changed_at)}/>
     <DetailRow label="Last Login At" value={fmtDateTime(account.last_login_at)}/>
     <DetailRow label="Account Created At" value={fmtDateTime(account.account_created_at||account.created_at)} last/>
    </div>

   </div>
  </Panel>
 </>;
}

export function Calendar({token}){
 const s=useGet("/api/google/calendar/status",token),[st,setSt]=useState({e:"",m:""});const connect=async()=>{try{const x=await API.request("/api/google/calendar/connect",{},token);if(x.authorization_url)window.open(x.authorization_url,"_blank");setSt({e:"",m:"Google authorization opened in your browser."})}catch(e){setSt({e:e.message,m:""})}};return <><div className="page-title"><div><span className="eyebrow">Integration</span><h1>Google Calendar</h1><p>Connect the current staff account to Google Calendar.</p></div></div><Alert {...st}/><Panel title="Connection Status" actions={s.data?.connected?<Button danger onClick={async()=>{await send(token,"/api/google/calendar/disconnect","POST");s.refresh()}}>Disconnect</Button>:<button className="button gold" onClick={connect}>Connect Google Calendar</button>}><Obj data={s.data||{}}/></Panel></>
}





export function AttendanceRegisters({token}){
 const classes=useGet("/api/staff/academic-management/classes",token);
 const queue=useGet("/api/staff/admin/attendance-review?status=Submitted&limit=200",token);
 const[classId,setClassId]=useState("");
 const[weekStart,setWeekStart]=useState("");
 const[review,setReview]=useState(null);
 const[st,setSt]=useState({e:"",m:""});
 const rows=classes.data?.classes||[];
 const submitted=queue.data?.records||[];
 const selected=rows.find(x=>String(x.id)===String(classId));

 const openReview=async(row)=>{
  try{
   const x=await API.request(`/api/staff/admin/attendance-review/${row.attendance_session_id}`,{},token);
   setReview(x.data||x);
   setSt({e:"",m:""});
  }catch(e){setSt({e:e.message,m:""})}
 };

 const confirmAttendance=async()=>{
  if(!review?.attendance?.attendance_session_id)return;
  if(!window.confirm("Confirm this submitted attendance as the official attendance record?"))return;
  try{
   await send(token,`/api/staff/admin/attendance-review/${review.attendance.attendance_session_id}/confirm`,"POST");
   setReview(null);
   queue.refresh();
   setSt({e:"",m:"Attendance confirmed as official."});
  }catch(e){setSt({e:e.message,m:""})}
 };

 const returnForCorrection=async()=>{
  if(!review?.attendance?.attendance_session_id)return;
  const reason=prompt("Reason for returning this attendance to the Facilitator/Assessor:","");
  if(reason===null)return;
  if(!reason.trim()){
   setSt({e:"A return reason is required.",m:""});
   return;
  }
  try{
   await send(token,`/api/staff/admin/attendance-review/${review.attendance.attendance_session_id}/return`,"POST",{reason:reason.trim()});
   setReview(null);
   queue.refresh();
   setSt({e:"",m:"Attendance returned for correction."});
  }catch(e){setSt({e:e.message,m:""})}
 };

 const generate=async()=>{
  if(!classId){setSt({e:"Select a class.",m:""});return}
  if(!weekStart){setSt({e:"Select the Monday starting the attendance week.",m:""});return}
  const d=new Date(`${weekStart}T12:00:00`);
  if(d.getDay()!==1){setSt({e:"Week start must be a Monday.",m:""});return}
  try{
   const name=`Attendance_Register_${selected?.class_code||"Class"}_${weekStart}.pdf`;
   await API.downloadFile(`/api/staff/admin/attendance-registers/daily-pack${q({class_id:classId,week_start:weekStart})}`,token,name);
   setSt({e:"",m:"Daily attendance register pack generated and downloaded."});
  }catch(e){setSt({e:e.message,m:""})}
 };

 return <><div className="page-title"><div><span className="eyebrow">Attendance Administration</span><h1>Attendance Registers</h1><p>Review attendance submitted by Facilitators/Assessors, confirm official attendance, return incorrect submissions, and generate daily attendance register packs.</p></div></div><Alert e={st.e||classes.e||queue.e} m={st.m}/><Panel title={`Submitted Attendance for Confirmation (${submitted.length})`} text="Attendance submitted by a Facilitator or Assessor stays pending here until Admin confirms it or returns it for correction."><Tbl rows={submitted} cols={["session_date","class_code","course_name","module_code","submitted_by_name","submitted_at","status"]} act={r=><Button onClick={()=>openReview(r)}>Review</Button>}/></Panel>{review&&<Panel title="Review Submitted Attendance" text="Check the learner-by-learner attendance before confirming it as official." actions={<><button className="button gold" onClick={confirmAttendance}>Confirm Attendance</button><button className="button danger" onClick={returnForCorrection}>Return for Correction</button><button className="button light" onClick={()=>setReview(null)}>Close</button></>}><Obj data={review.attendance||{}}/><h3>Learner Attendance</h3><Tbl rows={review.students||[]} cols={["student_number","first_name","last_name","attendance_status","minutes_late","notes"]}/></Panel>}<Panel title="Generate Daily Attendance Register Pack" text="Choose a class and the Monday starting the week. One register page is generated for each training day from Monday to Friday."><div className="form-grid"><label><span>Class</span><select value={classId} onChange={e=>setClassId(e.target.value)}><option value="">Select class</option>{rows.map(x=><option key={x.id} value={x.id}>{x.class_code} - {x.class_name||x.course_code} - {x.cycle_code}</option>)}</select></label><label><span>Week Starting Monday</span><input type="date" value={weekStart} onChange={e=>setWeekStart(e.target.value)}/></label></div><button className="button gold" onClick={generate}>Generate & Download Attendance Register</button></Panel><Panel title="Attendance Workflow" text="The SMS keeps capture, submission and Admin confirmation separate."><div className="where-grid"><div><strong>1. Facilitator / Assessor</strong><span>Captures attendance for every learner and submits the completed attendance session.</span></div><div><strong>2. Admin Review</strong><span>Reviews submitted learner statuses and confirms the register or returns it with a correction reason.</span></div><div><strong>3. Official Attendance</strong><span>Once confirmed, the attendance session is rendered as the official attendance record.</span></div><div><strong>4. Register PDF</strong><span>Admin can separately generate the daily attendance register pack using the existing PDF layout.</span></div></div></Panel></>
}

