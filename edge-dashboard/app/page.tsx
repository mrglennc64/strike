'use client'

import Link from 'next/link'
import { Card } from '@/components/Card'
import {
  Zap,
  TrendingUp,
  Briefcase,
  Bitcoin,
  Trophy,
} from 'lucide-react'

const verticals = [
  {
    id: 'ai-releases',
    name: 'AI Releases',
    description: 'Track and predict AI model releases, benchmarks, and performance indicators',
    icon: Zap,
    color: 'text-yellow-400',
    href: '/ai-releases',
  },
  {
    id: 'economics',
    name: 'Economics',
    description: 'Economic indicators, Fed decisions, inflation trends, and market cycles',
    icon: TrendingUp,
    color: 'text-green-400',
    href: '/economics',
  },
  {
    id: 'earnings',
    name: 'Earnings',
    description: 'Corporate earnings predictions, guidance, and analyst sentiment analysis',
    icon: Briefcase,
    color: 'text-blue-400',
    href: '/earnings',
  },
  {
    id: 'crypto',
    name: 'Crypto',
    description: 'Cryptocurrency price predictions, on-chain metrics, and market sentiment',
    icon: Bitcoin,
    color: 'text-orange-400',
    href: '/crypto',
  },
  {
    id: 'mlb',
    name: 'MLB',
    description: 'Baseball strikeout edges, pitcher matchups, and in-game predictions',
    icon: Trophy,
    color: 'text-red-400',
    href: '/mlb',
  },
]

export default function Home() {
  return (
    <main className="min-h-screen bg-trading-bg">
      {/* Hero Section */}
      <section className="relative overflow-hidden pt-20 pb-32 md:pt-32 md:pb-48">
        {/* Background gradient */}
        <div className="absolute inset-0 overflow-hidden">
          <div className="absolute -top-40 -right-40 w-80 h-80 bg-trading-accent opacity-20 rounded-full blur-3xl"></div>
          <div className="absolute top-1/2 -left-40 w-80 h-80 bg-blue-500 opacity-10 rounded-full blur-3xl"></div>
        </div>

        <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <h1 className="text-4xl md:text-6xl font-bold mb-6 gradient-text">
              Edge AI
            </h1>
            <p className="text-2xl md:text-3xl font-semibold text-trading-text mb-4">
              Multi-Vertical Prediction Platform
            </p>
            <p className="text-lg md:text-xl text-gray-400 max-w-2xl mx-auto mb-8">
              Leverage AI-powered predictions across AI releases, economics, earnings, crypto, and sports to discover and capitalize on market edges.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link
                href="/dashboard"
                className="trading-btn px-8 py-3 text-lg"
              >
                Launch Dashboard
              </Link>
              <Link
                href="#verticals"
                className="trading-btn-secondary px-8 py-3 text-lg border-trading-border hover:border-trading-accent"
              >
                Explore Verticals
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Verticals Section */}
      <section id="verticals" className="py-20 md:py-32 bg-gradient-to-b from-trading-bg to-gray-950">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-trading-text mb-4">
              Available Verticals
            </h2>
            <p className="text-gray-400 text-lg">
              Choose your edge. Real-time predictions across five distinct markets.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6 lg:gap-4">
            {verticals.map((vertical) => {
              const IconComponent = vertical.icon
              return (
                <Link key={vertical.id} href={vertical.href}>
                  <Card className="h-full cursor-pointer hover:border-trading-accent transition-colors">
                    <div className="flex flex-col h-full">
                      <div className={`text-5xl mb-4 ${vertical.color}`}>
                        <IconComponent size={48} />
                      </div>
                      <h3 className="text-xl font-bold text-trading-text mb-3">
                        {vertical.name}
                      </h3>
                      <p className="text-gray-400 text-sm flex-grow">
                        {vertical.description}
                      </p>
                      <div className="mt-4 pt-4 border-t border-trading-border">
                        <span className="text-trading-accent text-sm font-semibold">
                          Explore →
                        </span>
                      </div>
                    </div>
                  </Card>
                </Link>
              )
            })}
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20 md:py-32 bg-trading-bg">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-3xl md:text-4xl font-bold text-trading-text mb-12 text-center">
            Shared Platform Features
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
            <div className="trading-card p-6">
              <h3 className="text-trading-accent font-bold text-lg mb-3">
                Authentication
              </h3>
              <p className="text-gray-400 text-sm">
                Secure multi-factor authentication across all verticals
              </p>
            </div>
            <div className="trading-card p-6">
              <h3 className="text-trading-accent font-bold text-lg mb-3">
                Bankroll Management
              </h3>
              <p className="text-gray-400 text-sm">
                Track and manage your capital allocation across verticals
              </p>
            </div>
            <div className="trading-card p-6">
              <h3 className="text-trading-accent font-bold text-lg mb-3">
                Risk Metrics
              </h3>
              <p className="text-gray-400 text-sm">
                Real-time risk assessment, Sharpe ratio, and drawdown analysis
              </p>
            </div>
            <div className="trading-card p-6">
              <h3 className="text-trading-accent font-bold text-lg mb-3">
                Audit Log
              </h3>
              <p className="text-gray-400 text-sm">
                Complete transaction history and decision audit trail
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 md:py-32 bg-gradient-to-r from-trading-accent/10 to-blue-600/10 border-t border-trading-border">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-3xl md:text-4xl font-bold text-trading-text mb-6">
            Ready to Find Your Edge?
          </h2>
          <p className="text-gray-400 text-lg mb-8">
            Join traders and analysts using AI predictions to identify market inefficiencies
          </p>
          <Link href="/dashboard" className="trading-btn px-8 py-3 text-lg inline-block">
            Start Trading Now
          </Link>
        </div>
      </section>
    </main>
  )
}
