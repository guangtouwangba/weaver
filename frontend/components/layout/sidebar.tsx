"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { cn } from "@/lib/utils"
import { 
  LayoutDashboard, 
  Clock, 
  History, 
  Settings, 
  Database,
  Bot,
  BarChart3
} from "lucide-react"

const navigation = [
  {
    name: "Dashboard",
    href: "/",
    icon: LayoutDashboard,
  },
  {
    name: "Jobs",
    href: "/jobs",
    icon: Clock,
  },
  {
    name: "History",
    href: "/history",
    icon: History,
  },
  {
    name: "Analytics",
    href: "/analytics", 
    icon: BarChart3,
  },
  {
    name: "Providers",
    href: "/providers",
    icon: Database,
  },
  {
    name: "Settings",
    href: "/settings",
    icon: Settings,
  },
]

export function Sidebar() {
  const pathname = usePathname()

  return (
    <div className="flex h-full w-64 flex-col bg-card border-r">
      {/* Logo */}
      <div className="flex h-16 items-center border-b px-6">
        <Bot className="h-8 w-8 text-primary" />
        <span className="ml-2 text-xl font-bold">Research Agent</span>
      </div>

      {/* Navigation */}
      <nav className="flex-1 space-y-1 px-4 py-6">
        {navigation.map((item) => {
          const isActive = pathname === item.href
          return (
            <Link
              key={item.name}
              href={item.href}
              className={cn(
                "flex items-center rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                isActive
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
              )}
            >
              <item.icon className="mr-3 h-5 w-5" />
              {item.name}
            </Link>
          )
        })}
      </nav>

      {/* Status indicator */}
      <div className="border-t p-4">
        <div className="flex items-center">
          <div className="h-2 w-2 rounded-full bg-green-500" />
          <span className="ml-2 text-xs text-muted-foreground">
            System Online
          </span>
        </div>
      </div>
    </div>
  )
}