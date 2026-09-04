import * as React from "react"
import { cn } from "@/lib/utils"
export function Card({className,...p}:React.HTMLAttributes<HTMLDivElement>){return <div className={cn("card", className)} {...p} />}
export function CardHeader({className,...p}:React.HTMLAttributes<HTMLDivElement>){return <div className={cn("p-5 pb-3",className)} {...p} />}
export function CardTitle({className,...p}:React.HTMLAttributes<HTMLHeadingElement>){return <h3 className={cn("font-semibold text-[14px] tracking-tight",className)} {...p} />}
export function CardDesc({className,...p}:React.HTMLAttributes<HTMLParagraphElement>){return <p className={cn("text-[12.5px] leading-5 text-[#57534E]",className)} {...p} />}
export function CardContent({className,...p}:React.HTMLAttributes<HTMLDivElement>){return <div className={cn("p-5 pt-0",className)} {...p} />}
