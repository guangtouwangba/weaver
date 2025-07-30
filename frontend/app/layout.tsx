import type { Metadata } from 'next'
import './globals.css'
import { Toaster } from 'sonner'

export const metadata: Metadata = {
  title: 'Research Agent - Cronjob Management',
  description: 'Automated research paper collection and processing system',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className="font-sans antialiased">
        <div className="bg-background">
          {children}
        </div>
        <Toaster />
      </body>
    </html>
  )
}