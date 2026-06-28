// Authentication Types
export interface User {
  id: string
  name: string
  email: string
  avatar?: string
  createdAt: Date
}

export interface AuthResponse {
  user: User
  token: string
}

// Bankroll Types
export interface Bankroll {
  userId: string
  total: number
  available: number
  allocated: number
  currency: string
  lastUpdated: Date
}

export interface BankrollAdjustment {
  vertical: string
  amount: number
  reason: string
  timestamp: Date
}

// Risk Metrics Types
export interface RiskMetric {
  label: string
  value: number | string
  unit?: string
  status?: 'good' | 'warning' | 'danger'
}

export interface PerformanceMetrics {
  sharpeRatio: number
  maxDrawdown: number
  winRate: number
  valueAtRisk: number
  returnYTD: number
  totalReturn: number
}

// Audit Log Types
export interface AuditLogEntry {
  id: string
  timestamp: Date
  action: string
  vertical: string
  result?: 'Win' | 'Loss' | 'Pending'
  amount?: number
  userId: string
}

// Prediction Types
export interface BasePrediction {
  id: string
  userId: string
  vertical: string
  createdAt: Date
  updatedAt: Date
  confidence: number
  status: 'active' | 'resolved' | 'cancelled'
}

// AI Releases Vertical
export interface AIReleasePrediction extends BasePrediction {
  vertical: 'ai-releases'
  event: string
  prediction: string
  impact: 'High' | 'Medium' | 'Low'
  stake: number
}

// Economics Vertical
export interface EconomicPrediction extends BasePrediction {
  vertical: 'economics'
  indicator: string
  date: Date
  forecast: string
  prediction: string
  direction: 'up' | 'down' | 'neutral'
  stake: number
}

// Earnings Vertical
export interface EarningsPrediction extends BasePrediction {
  vertical: 'earnings'
  ticker: string
  company: string
  date: Date
  epsForecast: number
  epsPrediction: number
  expectedMove: number
  stake: number
}

// Crypto Vertical
export interface CryptoPrediction extends BasePrediction {
  vertical: 'crypto'
  symbol: string
  name: string
  currentPrice: number
  prediction: number
  direction: 'up' | 'down'
  positionSize: number
  entryPrice: number
  timeframe: string
  stake: number
}

// MLB Vertical
export interface MLBPrediction extends BasePrediction {
  vertical: 'mlb'
  pitcher: string
  team: string
  opponent: string
  date: Date
  ksPrediction: number
  ksLine: number
  edge: 'OVER' | 'UNDER'
  impliedOdds: string
  stake: number
}

// Union type for all predictions
export type Prediction =
  | AIReleasePrediction
  | EconomicPrediction
  | EarningsPrediction
  | CryptoPrediction
  | MLBPrediction

// API Response Types
export interface APIResponse<T> {
  success: boolean
  data: T
  error?: string
  timestamp: Date
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  pageSize: number
  hasMore: boolean
}

// Vertical Statistics
export interface VerticalStats {
  vertical: string
  activePredictions: number
  totalCapital: number
  unrealizedPNL: number
  realizedPNL: number
  winRate: number
  roi: number
  hitRate: number
  return: number
}

export interface PortfolioStats {
  totalAssets: number
  unrealizedPNL: number
  realizedPNL: number
  ytdReturn: number
  activePositions: number
  overallWinRate: number
  verticalStats: VerticalStats[]
}

// Event Types
export interface MarketEvent {
  id: string
  date: Date
  event: string
  impact: 'High' | 'Medium' | 'Low'
  vertical: string
}

export interface UpcomingEvent extends MarketEvent {
  prediction?: string
  confidence?: number
}
