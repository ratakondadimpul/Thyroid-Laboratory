import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"
export function cn(...inputs: ClassValue[]) { return twMerge(clsx(inputs)) }
export function statusColor(label:string){
  if(label==="Positive" || label==="High" || label==="Higher Risk") return "text-[#E02424] bg-[#FDE8E8] border-[#F8B4B4]"
  if(label==="Medium" || label==="Higher Risk") return "text-[#C27803] bg-[#FFF4DB] border-[#FDE68A]"
  return "text-[#0E9F6E] bg-[#EAF9F1] border-[#A7F3D0]"
}
export function riskColor(label: string) {
  if (label==="Positive" || label==="High" || label==="Higher Risk") return "text-[#E02424] bg-[#FDE8E8] border-[#F8B4B4]"
  if (label==="Medium") return "text-[#C27803] bg-[#FFF4DB] border-[#FDE68A]"
  return "text-[#0E9F6E] bg-[#EAF9F1] border-[#A7F3D0]"
}
export function riskDot(label:string){
  if(label==="Positive" || label==="High" || label==="Higher Risk") return "bg-[#E02424]"
  if(label==="Medium") return "bg-[#C27803]"
  return "bg-[#0E9F6E]"
}
export const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
