import { ReactNode } from 'react'
import { Card } from '@/components/Card'

interface VerticalLayoutProps {
  title: string
  description: string
  children: ReactNode
}

export function VerticalLayout({
  title,
  description,
  children,
}: VerticalLayoutProps) {
  return (
    <main className="min-h-screen bg-trading-bg">
      {/* Header */}
      <section className="border-b border-trading-border py-8 md:py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h1 className="text-4xl md:text-5xl font-bold text-trading-text mb-4">
            {title}
          </h1>
          <p className="text-gray-400 text-lg max-w-2xl">
            {description}
          </p>
        </div>
      </section>

      {/* Content */}
      <section className="py-12 md:py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          {children}
        </div>
      </section>
    </main>
  )
}
