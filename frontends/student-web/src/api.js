const BASE=(import.meta.env.VITE_API_BASE_URL||"").replace(/\/$/,"");
async function parse(r){let b=null;try{b=await r.json()}catch{} if(!r.ok)throw new Error(b?.detail||b?.message||`HTTP ${r.status}`);return b}
export async function req(path,opt={},token=null){const h={...(opt.body instanceof FormData?{}:{"Content-Type":"application/json"}),...(token?{Authorization:`Bearer ${token}`}:{})};return parse(await fetch(BASE+path,{...opt,headers:{...h,...(opt.headers||{})}}))}
export const loginPassword=p=>req("/api/student-auth/login/password",{method:"POST",body:JSON.stringify(p)});
export const loginPin=(p,t)=>req("/api/student-auth/login/pin",{method:"POST",body:JSON.stringify(p)},t);
export const changePassword=p=>req("/api/student-auth/change-password",{method:"POST",body:JSON.stringify(p)});
export const setupPin=p=>req("/api/student-auth/setup-pin",{method:"POST",body:JSON.stringify(p)});
export const me=t=>req("/api/student-auth/me",{},t); export const profile=t=>req("/api/student/profile",{},t); export const modules=t=>req("/api/student/modules",{},t); export const results=t=>req("/api/student/results",{},t); export const assessment=t=>req("/api/student/assessment-status",{},t); export const timetable=t=>req("/api/student/timetable",{},t); export const documents=t=>req("/api/student/documents",{},t); export const finance=t=>req("/api/student/finance",{},t); export const card=t=>req("/api/student/card",{},t); export const announcements=t=>req("/api/student/announcements",{},t); export const messages=t=>req("/api/student/messages",{},t); export const support=t=>req("/api/student/support",{},t); export const settings=t=>req("/api/student/settings",{},t);
export function uploadDoc(id,file,t){const f=new FormData();f.append("request_id",id);f.append("file",file);return req("/api/student/documents/upload",{method:"POST",body:f},t)}
export function uploadAvatar(file,t){const f=new FormData();f.append("avatar",file);return req("/api/student/card/avatar",{method:"POST",body:f},t)}
export const newMessage=(p,t)=>req("/api/student/messages",{method:"POST",body:JSON.stringify(p)},t); export const newSupport=(p,t)=>req("/api/student/support",{method:"POST",body:JSON.stringify(p)},t); export const saveContact=(p,t)=>req("/api/student/settings/contact",{method:"PATCH",body:JSON.stringify(p)},t); export const savePrefs=(p,t)=>req("/api/student/settings/preferences",{method:"PATCH",body:JSON.stringify(p)},t);
export async function download(path,t,name){const r=await fetch(BASE+path,{headers:{Authorization:`Bearer ${t}`}});if(!r.ok){await parse(r);return}const blob=await r.blob();const u=URL.createObjectURL(blob);const a=document.createElement("a");a.href=u;a.download=name;a.click();URL.revokeObjectURL(u)}
export async function blobUrl(path,t){const r=await fetch(BASE+path,{headers:{Authorization:`Bearer ${t}`}});if(!r.ok){await parse(r);return ""}return URL.createObjectURL(await r.blob())}
export const attendance=t=>req("/api/student/attendance",{},t);
export const resources=t=>req("/api/student/learning-resources",{},t);
export const resource=(id,t)=>req(`/api/student/learning-resources/${encodeURIComponent(id)}`,{},t);
export const completion=t=>req("/api/student/completion-documents",{},t);
export const requestAvatarReplacement=(reason,t)=>req("/api/student/card/avatar/replacement-request",{method:"POST",body:JSON.stringify({reason})},t);
export const startPayfast=(payload,t)=>req("/api/student/finance/payfast/start",{method:"POST",body:JSON.stringify(payload||{})},t);
