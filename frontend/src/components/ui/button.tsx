import * as React from "react"
import { cn } from "@/lib/utils"
type Props = React.ButtonHTMLAttributes<HTMLButtonElement> & { variant?: "default"|"outline"|"ghost"|"subtle", size?: "sm"|"md"|"lg" }
export function Button({ className, variant="default", size="md", ...props}: Props){
  const base="inline-flex items-center justify-center font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#D97706] focus-visible:ring-offset-2 disabled:opacity-50 disabled:pointer-events-none rounded-[10px] font-sans"
  const variants={
    default:"bg-[#0F0F0F] text-white hover:bg-[#1F1F1F] active:scale-[0.98]",
    outline:"border border-[#E7E5E4] bg-white hover:bg-[#F8F7F4] text-[#0F0F0F]",
    ghost:"hover:bg-[#F1EFE9] text-[#57534E]",
    subtle:"bg-[#FFF7ED] text-[#B45309] hover:bg-[#FFEDD5] border border-[#FDE68A]"
  }
  const sizes={sm:"h-8 px-3 text-[13px]", md:"h-9 px-4 text-[14px]", lg:"h-11 px-6 text-[15px]"}
  return <button className={cn(base, variants[variant], sizes[size], className)} {...props} />
}
