import { cn, riskColor } from "@/lib/utils"
export function Badge({label, className}:{label:string, className?:string}){
  return <span className={cn("inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[11px] font-semibold tracking-wide", riskColor(label), className)}><span className={`h-1.5 w-1.5 rounded-full ${label==="Positive"||label==="High"||label==="Higher Risk"?"bg-[#E02424]":label==="Medium"?"bg-[#C27803]":"bg-[#0E9F6E]"}`} />{label}</span>
}
export function Pill({children, className}:{children:React.ReactNode, className?:string}){ return <span className={cn("inline-flex items-center rounded-full bg-[#EFF4F8] border border-[#DDE7EF] px-2.5 py-1 text-[11px] font-medium text-[#4A6572]",className)}>{children}</span>}
