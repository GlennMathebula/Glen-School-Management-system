import {createContext,useContext,useEffect,useMemo,useState} from "react";import * as A from "./api";
const C=createContext(null),TK="gm_student_token",MK="gm_student_meta";const read=()=>{try{return JSON.parse(localStorage.getItem(MK)||"null")}catch{return null}};
export function AuthProvider({children}){const [token,setToken]=useState(()=>localStorage.getItem(TK)||"");const [meta,setMeta]=useState(read);const [student,setStudent]=useState(null);const [loading,setLoading]=useState(false);
const save=(t,m)=>{t?localStorage.setItem(TK,t):localStorage.removeItem(TK);m?localStorage.setItem(MK,JSON.stringify(m)):localStorage.removeItem(MK);setToken(t||"");setMeta(m||null)};const logout=()=>{save("",null);setStudent(null)};
const needsOnboarding=!!token&&!!meta&&(!!meta.must_change_password||meta.pin_created===false);
const needsPin=!!token&&!!meta&&!needsOnboarding&&meta.login_method==="password_pending_pin";
const fullAccess=!!token&&!!meta&&!meta.must_change_password&&meta.pin_created===true&&meta.login_method==="password+pin";
useEffect(()=>{let on=true;if(!fullAccess){setStudent(null);setLoading(false);return}setLoading(true);A.me(token).then(r=>{if(on){setStudent(r.student);setLoading(false)}}).catch(()=>{if(on){logout();setLoading(false)}});return()=>{on=false}},[token,fullAccess]);
async function pw(n,p){const x=(await A.loginPassword({student_number:n,password:p})).result;save(x.access_token,{student_number:x.student_number,login_method:x.login_method||"password_pending_pin",must_change_password:!!x.must_change_password,pin_created:!!x.pin_created});return x}
async function pin(n,p){if(!token)throw new Error("Password verification is required before PIN verification.");const x=(await A.loginPin({student_number:n,pin:p},token)).result;save(x.access_token,{student_number:x.student_number,login_method:x.login_method||"password+pin",must_change_password:false,pin_created:true});return x}
const update=(t,c)=>save(t||token,{...(meta||{}),...(c||{})});const value=useMemo(()=>({token,meta,student,loading,isAuthenticated:!!token,fullAccess,needsOnboarding,needsPin,loginPassword:pw,loginPin:pin,update,logout}),[token,meta,student,loading,fullAccess,needsOnboarding,needsPin]);return <C.Provider value={value}>{children}</C.Provider>}
export const useAuth=()=>useContext(C);
