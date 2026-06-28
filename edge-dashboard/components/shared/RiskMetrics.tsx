'use client'

import { Card } from '@/components/Card'
import { AlertCircle, TrendingDown, Zap } from 'lucide-react'

interface Metric {
  label: string
  value: string | number
  unit?: string
  status?: 'good' | 'warning' | 'danger'
}

interface RiskMetricsProps {
  metrics?: Metric[]
}

const defaultMetrics: Metric[] = [
  {
    label: 'Sharpe Ratio',
    value: 1.24,
    status: 'good',
  },
  {
    label: 'Max Drawdown',
    value: -12.5,
    unit: '%',
    status: 'warning',
  },
  {
    label: 'Win Rate',
    value: 58.3,
    unit: '%',
    status: 'good',
  },
  {
    label: 'Value at Risk (95%)',
    value: -8500,
    unit: 'USD',
    status: 'warning',
  },
]

function getStatusColor(status?: string) {
  switch (status) {
    case 'good':
      return 'text-trading-success'
    case 'warning':
      return 'text-trading-warning'
    case 'danger':
      return 'text-trading-danger'
    default:
      return 'text-trading-accent'
  }
}

function getStatusIcon(status?: string) {
  switch (status) {
    case 'good':
      return <Zap size={16} className="text-trading-success" />
    case 'warning':
      return <AlertCircle size={16} className="text-trading-warning" />
    case 'danger':
      return <AlertCircle size={16} className="text-trading-danger" />
    default:
      return null
  }
}

export function RiskMetrics({ metrics = defaultMetrics }: RiskMetricsProps) {
  return (
    <Card>
      <h3 className="text-lg font-semibold text-trading-text mb-4">Risk Metrics</h3>

      <div className="space-y-3">
        {metrics.map((metric, index) => (
          <div key={index} className="flex items-center justify-between p-3 bg-trading-bg rounded border border-trading-border">
            <div className="flex items-center space-x-2">
              {getStatusIcon(metric.status)}
              <span className="text-gray-400 text-sm">{metric.label}</span>
            </div>
            <span className={`font-semibold ${getStatusColor(metric.status)}`}>
              {metric.value}{metric.unit || ''}
            </span>
          </div>
        ))}
      </div>

      <div className="mt-4 p-3 bg-trading-warning/10 border border-trading-warning/30 rounded">
        <p className="text-trading-warning text-xs">
          These metrics are calculated from your trading history. Monitor regularly.
        </p>
      </div>
    </Card>
  )
}
