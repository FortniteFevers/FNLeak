import type { Metadata } from 'next'
import { ClerkProvider } from '@clerk/nextjs'
import { Analytics } from '@vercel/analytics/next'
import './globals.css'

export const metadata: Metadata = {
  title: 'World Cup Field Guide',
  description: 'A complete field guide for following the 2026 World Cup.',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <ClerkProvider>{children}</ClerkProvider>
        <Analytics />
      </body>
    </html>
  )
}
