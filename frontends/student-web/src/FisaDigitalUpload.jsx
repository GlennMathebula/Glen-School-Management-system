import {useEffect,useState} from "react";
import * as A from "./api";
import {useAuth} from "./auth";
export default function FisaDigitalUpload(){
 const auth=useAuth();const [items,setItems]=useState([]),[files,setFiles]=useState({}),[busy,setBusy]=useState(""),[message,setMessage]=useState("");
 async function reload(){try{const r=await A.req("/api/fisa-digital/student/sittings",{},auth.token);setItems(r.sittings||[])}catch(e){setMessage(e.message)}}
 useEffect(()=>{reload()},[auth.token]);
 async function submit(id){const file=files[id];if(!file)return;setBusy(id);setMessage("");try{const form=new FormData();form.append("file",file);await A.req(`/api/fisa-digital/student/sittings/${id}/upload`,{method:"POST",body:form},auth.token);setMessage("FISA script submitted successfully. Your receipt is recorded.");await reload()}catch(e){setMessage(e.message)}finally{setBusy("")}}
 return <section className="panel" style={{marginTop:18,padding:16}}><h2>Submit completed FISA answer script</h2><p>Upload after writing the supervised examination. PDF/JPG/PNG, maximum 10 MB. Results remain hidden until official publication.</p>{message&&<p role="status">{message}</p>}{!items.length?<p>No digital FISA sittings available for your registration.</p>:items.map(s=><div key={s.id} style={{borderTop:"1px solid #ddd",padding:"12px 0"}}><strong>{s.title} — {s.course_code}</strong><p>Cycle: {s.cycle} | Submission: {s.status||"Not submitted"}{s.submission_deadline?` | Deadline: ${new Date(s.submission_deadline).toLocaleString()}`:""}</p>{s.status?<p>{s.status==="Published"?`Published result: ${s.outcome}`:"Result pending assessment / QA release"}</p>:<><input type="file" accept=".pdf,.jpg,.jpeg,.png" onChange={e=>setFiles({...files,[s.id]:e.target.files?.[0]})}/><button className="btn gold" disabled={!files[s.id]||!!busy} onClick={()=>submit(s.id)}>{busy===s.id?"Submitting...":"Submit script"}</button></>}</div>)}</section>
}
