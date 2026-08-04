import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import toast from "react-hot-toast";
import { FiUser, FiMail, FiLock, FiEye, FiEyeOff } from "react-icons/fi";
import { useAuth } from "../../hooks/useAuth";
import { usePreferences } from "../../hooks/usePreferences";
import Button from "../../components/Button";

export default function Register() {
  const { register } = useAuth(); const { t } = usePreferences(); const navigate = useNavigate();
  const [form,setForm]=useState({name:"",email:"",password:"",confirmPassword:""});
  const [loading,setLoading]=useState(false); const [errors,setErrors]=useState({});
  const [passwordVisible,setPasswordVisible]=useState({password:false,confirmPassword:false});
  const validate=()=>{const e={};if(form.name.trim().length<2)e.name=t("auth.nameRequired");if(!form.email)e.email=t("auth.emailRequired");if(!/^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z0-9]).{8,}$/.test(form.password))e.password=t("auth.strongPassword");if(form.password!==form.confirmPassword)e.confirmPassword=t("auth.passwordMismatch");setErrors(e);return !Object.keys(e).length};
  const submit=async e=>{e.preventDefault();if(!validate())return;setLoading(true);try{await register(form.name,form.email,form.password,form.confirmPassword);toast.success(t("auth.accountCreated"));navigate("/login",{replace:true})}catch(err){toast.error(err.response?.data?.detail||t("auth.registrationFailed"))}finally{setLoading(false)}};
  const field=(key,label,type,Icon,placeholder,autoComplete)=>{const isPassword=type==="password",visible=isPassword&&passwordVisible[key];return <div><label className="mb-1 block text-sm font-medium text-slate-600 dark:text-slate-300">{label}</label><div className="relative"><Icon className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400"/><input type={visible?"text":type} autoComplete={autoComplete} className={`input-field pl-10 ${isPassword?"pr-11":""}`} placeholder={placeholder} value={form[key]} onChange={e=>setForm({...form,[key]:e.target.value})}/>{isPassword&&<button type="button" className="absolute right-3 top-1/2 -translate-y-1/2 rounded-md p-1 text-slate-400 hover:text-slate-700 focus:outline-none focus:ring-2 focus:ring-primary-500 dark:hover:text-slate-200" onClick={()=>setPasswordVisible(current=>({...current,[key]:!current[key]}))} aria-label={visible?t("auth.hidePassword"):t("auth.showPassword")}>{visible?<FiEyeOff aria-hidden="true"/>:<FiEye aria-hidden="true"/>}</button>}</div>{errors[key]&&<p className="mt-1 text-xs text-red-500">{errors[key]}</p>}</div>};
  return <div><h2 className="mb-1 text-2xl font-bold text-slate-800 dark:text-white">{t("auth.createTitle")}</h2><p className="mb-6 text-slate-500">{t("auth.createSubtitle")}</p><form onSubmit={submit} className="space-y-4">{field("name",t("auth.fullName"),"text",FiUser,t("auth.fullNamePlaceholder"),"name")}{field("email",t("auth.email"),"email",FiMail,t("auth.emailPlaceholder"),"email")}{field("password",t("auth.password"),"password",FiLock,t("auth.passwordPlaceholder"),"new-password")}{field("confirmPassword",t("auth.confirmPassword"),"password",FiLock,t("auth.confirmPasswordPlaceholder"),"new-password")}<Button type="submit" className="w-full" loading={loading}>{t("auth.createAccount")}</Button></form><p className="mt-6 text-center text-sm text-slate-500">{t("auth.haveAccount")} <Link to="/login" className="font-semibold text-primary-600 hover:underline">{t("auth.login")}</Link></p></div>;
}
