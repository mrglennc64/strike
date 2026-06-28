# Implementation Examples & Common Patterns

This document provides code examples and patterns for extending the Edge AI platform.

## Adding a New Vertical

### Step 1: Create the Vertical Route

Create `app/new-vertical/page.tsx`:

```tsx
'use client'

import { Card } from '@/components/Card'
import { VerticalLayout } from '@/components/VerticalLayout'
import { Authentication } from '@/components/shared/Authentication'
import { Bankroll } from '@/components/shared/Bankroll'
import { RiskMetrics } from '@/components/shared/RiskMetrics'
import { AuditLog } from '@/components/shared/AuditLog'
import { TrendingUp } from 'lucide-react'

export default function NewVerticalPage() {
  return (
    <VerticalLayout
      title="New Vertical"
      description="Your vertical description here"
    >
      {/* Shared Components Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <Authentication user={{ name: 'John Trader', email: 'john@example.com' }} />
        <Bankroll total={100000} available={75000} allocated={25000} />
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        <div className="lg:col-span-2">
          {/* Your main content here */}
        </div>

        <div>
          {/* Your sidebar here */}
        </div>
      </div>

      {/* Risk & Audit */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <RiskMetrics />
        <AuditLog limit={5} />
      </div>
    </VerticalLayout>
  )
}
```

### Step 2: Add Vertical to Navigation

Edit `components/Navbar.tsx`:

```tsx
const verticals = [
  // ... existing verticals
  { name: 'New Vertical', href: '/new-vertical' },
]
```

### Step 3: Add to Landing Page

Edit `app/page.tsx`:

```tsx
const verticals = [
  // ... existing verticals
  {
    id: 'new-vertical',
    name: 'New Vertical',
    description: 'Your vertical description',
    icon: YourIcon,
    color: 'text-color-400',
    href: '/new-vertical',
  },
]
```

## Creating Custom Components

### Example: Custom Chart Component

Create `components/Chart.tsx`:

```tsx
import { Card } from '@/components/Card'

interface ChartProps {
  title: string
  data: { label: string; value: number }[]
}

export function Chart({ title, data }: ChartProps) {
  const maxValue = Math.max(...data.map(d => d.value))

  return (
    <Card>
      <h3 className="text-lg font-semibold text-trading-text mb-4">
        {title}
      </h3>

      <div className="space-y-3">
        {data.map((item, idx) => (
          <div key={idx}>
            <div className="flex justify-between mb-1">
              <span className="text-gray-400 text-sm">{item.label}</span>
              <span className="text-trading-accent font-bold">
                {item.value}
              </span>
            </div>
            <div className="w-full bg-trading-bg rounded-full h-2 overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-trading-accent to-blue-500"
                style={{ width: `${(item.value / maxValue) * 100}%` }}
              ></div>
            </div>
          </div>
        ))}
      </div>
    </Card>
  )
}
```

Usage:

```tsx
<Chart 
  title="Performance by Asset"
  data={[
    { label: 'BTC', value: 65 },
    { label: 'ETH', value: 42 },
    { label: 'SOL', value: 28 },
  ]}
/>
```

## API Integration Patterns

### Pattern 1: Simple Data Fetching (React Hooks)

```tsx
'use client'

import { useState, useEffect } from 'react'
import { Card } from '@/components/Card'

interface Prediction {
  id: string
  name: string
  confidence: number
}

export function PredictionList() {
  const [predictions, setPredictions] = useState<Prediction[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function fetchPredictions() {
      try {
        const res = await fetch('/api/predictions')
        const data = await res.json()
        setPredictions(data.predictions)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Error fetching')
      } finally {
        setLoading(false)
      }
    }

    fetchPredictions()
  }, [])

  if (loading) return <div>Loading...</div>
  if (error) return <div>Error: {error}</div>

  return (
    <Card>
      <h2 className="text-xl font-bold text-trading-text mb-4">Predictions</h2>
      {predictions.map(pred => (
        <div key={pred.id} className="border-b border-trading-border pb-3 mb-3">
          <h3 className="text-trading-text font-semibold">{pred.name}</h3>
          <div className="mt-1 flex justify-between">
            <span className="text-gray-400 text-sm">Confidence</span>
            <span className="text-trading-accent font-bold">{pred.confidence}%</span>
          </div>
        </div>
      ))}
    </Card>
  )
}
```

### Pattern 2: Form Submission

```tsx
'use client'

import { useState } from 'react'
import { Card } from '@/components/Card'

export function CreatePredictionForm() {
  const [formData, setFormData] = useState({
    event: '',
    prediction: '',
    confidence: 50,
  })
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState('')

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true)
    setMessage('')

    try {
      const res = await fetch('/api/predictions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
      })

      if (!res.ok) throw new Error('Failed to create prediction')

      setMessage('Prediction created successfully!')
      setFormData({ event: '', prediction: '', confidence: 50 })
    } catch (error) {
      setMessage(
        `Error: ${error instanceof Error ? error.message : 'Unknown error'}`
      )
    } finally {
      setLoading(false)
    }
  }

  return (
    <Card>
      <h2 className="text-xl font-bold text-trading-text mb-4">
        New Prediction
      </h2>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-gray-400 text-sm mb-2">Event</label>
          <input
            type="text"
            className="trading-input w-full"
            value={formData.event}
            onChange={e => setFormData({ ...formData, event: e.target.value })}
            required
          />
        </div>

        <div>
          <label className="block text-gray-400 text-sm mb-2">Prediction</label>
          <input
            type="text"
            className="trading-input w-full"
            value={formData.prediction}
            onChange={e =>
              setFormData({ ...formData, prediction: e.target.value })
            }
            required
          />
        </div>

        <div>
          <label className="block text-gray-400 text-sm mb-2">
            Confidence: {formData.confidence}%
          </label>
          <input
            type="range"
            min="0"
            max="100"
            className="w-full"
            value={formData.confidence}
            onChange={e =>
              setFormData({ ...formData, confidence: Number(e.target.value) })
            }
          />
        </div>

        <button
          type="submit"
          disabled={loading}
          className="trading-btn w-full disabled:opacity-50"
        >
          {loading ? 'Creating...' : 'Create Prediction'}
        </button>

        {message && (
          <p
            className={`text-sm ${
              message.includes('successfully')
                ? 'text-trading-success'
                : 'text-trading-danger'
            }`}
          >
            {message}
          </p>
        )}
      </form>
    </Card>
  )
}
```

### Pattern 3: Real-time Updates with useEffect

```tsx
'use client'

import { useEffect, useState } from 'react'

interface Price {
  symbol: string
  price: number
  change: number
}

export function LivePrices() {
  const [prices, setPrices] = useState<Price[]>([])

  useEffect(() => {
    // Initial fetch
    fetchPrices()

    // Set up polling interval
    const interval = setInterval(fetchPrices, 5000) // Update every 5 seconds

    // Cleanup
    return () => clearInterval(interval)
  }, [])

  async function fetchPrices() {
    try {
      const res = await fetch('/api/prices')
      const data = await res.json()
      setPrices(data)
    } catch (error) {
      console.error('Error fetching prices:', error)
    }
  }

  return (
    <div className="space-y-2">
      {prices.map(p => (
        <div
          key={p.symbol}
          className="flex justify-between p-2 bg-trading-card rounded"
        >
          <span className="text-trading-accent font-bold">{p.symbol}</span>
          <div className="text-right">
            <p className="text-trading-text">${p.price.toFixed(2)}</p>
            <p className={p.change > 0 ? 'text-trading-success' : 'text-trading-danger'}>
              {p.change > 0 ? '+' : ''}{p.change.toFixed(2)}%
            </p>
          </div>
        </div>
      ))}
    </div>
  )
}
```

## Utility Functions

### Create `lib/api.ts`:

```typescript
const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:3001'

type RequestInit = RequestInit | undefined

interface APIOptions extends RequestInit {
  timeout?: number
}

async function apiCall(
  endpoint: string,
  options: APIOptions = {}
): Promise<any> {
  const { timeout = 30000, ...fetchOptions } = options

  const controller = new AbortController()
  const timeoutId = setTimeout(() => controller.abort(), timeout)

  try {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      ...fetchOptions,
      signal: controller.signal,
    })

    if (!response.ok) {
      throw new Error(`API error: ${response.status}`)
    }

    return await response.json()
  } finally {
    clearTimeout(timeoutId)
  }
}

export const api = {
  // Auth endpoints
  auth: {
    login: (email: string, password: string) =>
      apiCall('/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      }),
    logout: () => apiCall('/auth/logout', { method: 'POST' }),
    profile: () => apiCall('/auth/profile'),
  },

  // Bankroll endpoints
  bankroll: {
    balance: () => apiCall('/bankroll/balance'),
    allocate: (vertical: string, amount: number) =>
      apiCall('/bankroll/allocate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ vertical, amount }),
      }),
  },

  // Predictions endpoints
  predictions: {
    list: (vertical: string) => apiCall(`/${vertical}/predictions`),
    create: (vertical: string, data: any) =>
      apiCall(`/${vertical}/predictions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      }),
    update: (vertical: string, id: string, data: any) =>
      apiCall(`/${vertical}/predictions/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      }),
    delete: (vertical: string, id: string) =>
      apiCall(`/${vertical}/predictions/${id}`, { method: 'DELETE' }),
  },

  // Metrics endpoints
  metrics: {
    performance: () => apiCall('/metrics/performance'),
    risk: () => apiCall('/metrics/risk'),
  },

  // Audit endpoints
  audit: {
    transactions: (limit?: number) =>
      apiCall(`/audit/transactions${limit ? `?limit=${limit}` : ''}`),
  },
}
```

### Create `lib/formatting.ts`:

```typescript
export function formatCurrency(value: number, currency = 'USD'): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency,
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
  }).format(value)
}

export function formatPercentage(value: number, decimals = 1): string {
  return `${(value > 0 ? '+' : '')}${value.toFixed(decimals)}%`
}

export function formatDate(date: Date | string): string {
  return new Intl.DateTimeFormat('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  }).format(typeof date === 'string' ? new Date(date) : date)
}

export function formatDateTime(date: Date | string): string {
  return new Intl.DateTimeFormat('en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(typeof date === 'string' ? new Date(date) : date)
}
```

## Type Safety Examples

### Using TypeScript for API Integration

```tsx
import type { User, Prediction } from '@/types'
import { api } from '@/lib/api'

async function loadUserData(): Promise<{
  user: User
  predictions: Prediction[]
}> {
  const [userRes, predictionsRes] = await Promise.all([
    api.auth.profile(),
    api.predictions.list('ai-releases'),
  ])

  return {
    user: userRes.data as User,
    predictions: predictionsRes.data as Prediction[],
  }
}
```

## Mobile-Responsive Component Example

```tsx
export function ResponsiveGrid({ children }: { children: React.ReactNode }) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 md:gap-6">
      {children}
    </div>
  )
}

// Usage
<ResponsiveGrid>
  <Card>Item 1</Card>
  <Card>Item 2</Card>
  <Card>Item 3</Card>
</ResponsiveGrid>
```

## Context API for Global State (Optional)

Create `context/ThemeContext.tsx`:

```tsx
'use client'

import { createContext, useContext, useState } from 'react'

type Theme = 'dark' | 'light'

interface ThemeContextType {
  theme: Theme
  setTheme: (theme: Theme) => void
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined)

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [theme, setTheme] = useState<Theme>('dark')

  return (
    <ThemeContext.Provider value={{ theme, setTheme }}>
      {children}
    </ThemeContext.Provider>
  )
}

export function useTheme() {
  const context = useContext(ThemeContext)
  if (!context) {
    throw new Error('useTheme must be used within ThemeProvider')
  }
  return context
}
```

## Testing Example

Create `__tests__/components/Card.test.tsx`:

```tsx
import { render, screen } from '@testing-library/react'
import { Card } from '@/components/Card'

describe('Card Component', () => {
  it('renders children correctly', () => {
    render(<Card>Test Content</Card>)
    expect(screen.getByText('Test Content')).toBeInTheDocument()
  })

  it('applies custom className', () => {
    const { container } = render(
      <Card className="custom-class">Content</Card>
    )
    expect(container.querySelector('.custom-class')).toBeInTheDocument()
  })
})
```

## Best Practices

1. **Always use TypeScript** - Define types for all props and API responses
2. **Component composition** - Build large features from small, reusable components
3. **Error handling** - Always handle errors gracefully with user-friendly messages
4. **Loading states** - Show loading indicators during async operations
5. **Mobile first** - Design mobile layout first, then enhance for larger screens
6. **Accessibility** - Use semantic HTML and proper ARIA labels
7. **Performance** - Use React.memo for expensive components, avoid unnecessary re-renders
8. **Caching** - Consider caching API responses to reduce server load
9. **Logging** - Log API calls and errors for debugging
10. **Testing** - Write tests for critical components and functions
