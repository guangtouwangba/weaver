"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { cn } from "@/lib/utils"
import { 
  Brain, 
  FolderOpen, 
  BookOpen, 
  Users, 
  Clock, 
  FileText,
  History, 
  Settings, 
  Database,
  Bot,
  BarChart3
} from "lucide-react"

const navigation = [
  {
    name: "研究台",
    href: "/research",
    icon: Brain,
    description: "AI协作研究分析"
  },
  {
    name: "我的项目",
    href: "/research/projects",
    icon: FolderOpen,
    description: "研究项目管理"
  },
  {
    name: "论文库",
    href: "/papers",
    icon: BookOpen,
    description: "论文收藏与管理"
  },
  {
    name: "AI助手",
    href: "/agents",
    icon: Users,
    description: "专业AI代理团队"
  },
  {
    name: "数据管线",
    href: "/jobs",
    icon: Clock,
    description: "任务执行管理"
  },
  {
    name: "分析报告",
    href: "/reports",
    icon: FileText,
    description: "研究成果输出"
  },
  {
    name: "History",
    href: "/history",
    icon: History,
    description: "历史记录"
  },
  {
    name: "Settings",
    href: "/settings",
    icon: Settings,
    description: "系统设置"
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
          const isActive = pathname === item.href || pathname.startsWith(item.href + "/")
          return (
            <Link
              key={item.name}
              href={item.href}
              className={cn(
                "group flex items-center rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                isActive
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
              )}
              title={item.description}
            >
              <item.icon className="mr-3 h-5 w-5" />
              <div className="flex flex-col">
                <span>{item.name}</span>
                {item.description && (
                  <span className="text-xs opacity-60 group-hover:opacity-80">
                    {item.description}
                  </span>
                )}
              </div>
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