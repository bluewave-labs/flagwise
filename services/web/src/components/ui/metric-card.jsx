import * as React from "react"
import { cn } from "../../lib/utils"
import { Card, CardContent, CardHeader, CardTitle } from "./card"

const MetricCard = React.forwardRef(({ className, variant = "default", ...props }, ref) => {
  const variants = {
    default: "bg-slate-50/50 border-slate-100",
    blue: "bg-blue-50/50 border-blue-100", 
    red: "bg-red-50/50 border-red-100",
    green: "bg-green-50/50 border-green-100",
    purple: "bg-purple-50/50 border-purple-100",
    orange: "bg-orange-50/50 border-orange-100",
    yellow: "bg-yellow-50/50 border-yellow-100",
    pink: "bg-pink-50/50 border-pink-100",
    indigo: "bg-indigo-50/50 border-indigo-100",
    teal: "bg-teal-50/50 border-teal-100"
  }

  return (
    <Card
      ref={ref}
      className={cn(
        variants[variant],
        "metric-card-enhanced relative overflow-hidden",
        className
      )}
      {...props}
    />
  )
})
MetricCard.displayName = "MetricCard"

const MetricCardHeader = CardHeader
const MetricCardTitle = CardTitle  
const MetricCardContent = CardContent

export { MetricCard, MetricCardHeader, MetricCardTitle, MetricCardContent }