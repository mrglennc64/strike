# Edge AI - Multi-Vertical Prediction Platform

A modern Next.js application for managing AI-driven predictions across five distinct verticals: AI Releases, Economics, Earnings, Crypto, and MLB.

## Features

### Core Features
- **Multi-Vertical Dashboard**: Unified interface for managing predictions across 5 independent verticals
- **Landing Page**: Hero section with card-based vertical overview
- **Responsive Design**: Fully mobile-responsive dark trading UI theme
- **Tailwind CSS**: Modern utility-first styling

### Shared Components (Available Across All Verticals)
- **Authentication**: User login/logout with profile display
- **Bankroll Management**: Track total capital, available funds, and allocation percentages
- **Risk Metrics**: Real-time Sharpe ratio, max drawdown, win rate, and VaR calculations
- **Audit Log**: Complete transaction history and decision audit trail

### Vertical Pages
1. **AI Releases** - Track AI model releases, benchmarks, and performance indicators
2. **Economics** - Economic calendar, Fed decisions, inflation, GDP predictions
3. **Earnings** - Corporate earnings predictions, guidance, analyst sentiment
4. **Crypto** - Bitcoin, Ethereum, altcoin positions and on-chain signals
5. **MLB** - Strikeout edges, pitcher matchups, in-game predictions

### Dashboard
- Central hub with vertical quick links
- Portfolio summary and performance metrics
- Capital allocation breakdown across verticals
- Recent alerts and activity feed

## Project Structure

```
edge-dashboard/
├── app/
│   ├── layout.tsx              # Root layout with Navbar
│   ├── page.tsx                # Landing page
│   ├── globals.css             # Global styles
│   ├── dashboard/
│   │   └── page.tsx            # Central dashboard
│   ├── ai-releases/
│   │   └── page.tsx            # AI Releases vertical
│   ├── economics/
│   │   └── page.tsx            # Economics vertical
│   ├── earnings/
│   │   └── page.tsx            # Earnings vertical
│   ├── crypto/
│   │   └── page.tsx            # Crypto vertical
│   └── mlb/
│       └── page.tsx            # MLB vertical
├── components/
│   ├── Navbar.tsx              # Navigation bar with vertical selector
│   ├── Card.tsx                # Reusable card component
│   ├── VerticalLayout.tsx       # Layout wrapper for vertical pages
│   └── shared/
│       ├── Authentication.tsx   # Auth component
│       ├── Bankroll.tsx         # Bankroll tracker
│       ├── RiskMetrics.tsx      # Risk metrics dashboard
│       └── AuditLog.tsx         # Audit log viewer
├── package.json
├── next.config.js
├── tailwind.config.js
├── postcss.config.js
└── README.md
```

## Getting Started

### Prerequisites
- Node.js 18+ and npm or yarn

### Installation

1. Install dependencies:
```bash
npm install
```

2. Start the development server:
```bash
npm run dev
```

3. Open [http://localhost:3000](http://localhost:3000) in your browser

### Build for Production

```bash
npm run build
npm start
```

## Color Theme

The application uses a dark trading UI theme with custom colors:

- **Background**: `#0a0e27` (trading-bg)
- **Card**: `#141829` (trading-card)
- **Border**: `#2a2f4a` (trading-border)
- **Text**: `#e0e6ff` (trading-text)
- **Accent**: `#00d4ff` (trading-accent)
- **Success**: `#00c853` (trading-success)
- **Danger**: `#ff3838` (trading-danger)
- **Warning**: `#ffa500` (trading-warning)

## Component Usage

### Using Shared Components in Custom Pages

```tsx
import { Card } from '@/components/Card'
import { Authentication } from '@/components/shared/Authentication'
import { Bankroll } from '@/components/shared/Bankroll'
import { RiskMetrics } from '@/components/shared/RiskMetrics'
import { AuditLog } from '@/components/shared/AuditLog'

export default function CustomPage() {
  return (
    <div>
      <Authentication user={{ name: 'John Doe', email: 'john@example.com' }} />
      <Bankroll total={100000} available={75000} allocated={25000} />
      <RiskMetrics />
      <AuditLog />
    </div>
  )
}
```

## API Integration Points

The application is structured to easily integrate with backend APIs:

- **Authentication**: `/api/auth/login`, `/api/auth/logout`, `/api/auth/profile`
- **Bankroll**: `/api/bankroll/balance`, `/api/bankroll/allocate`
- **Risk Metrics**: `/api/metrics/performance`, `/api/metrics/risk`
- **Audit Log**: `/api/audit/transactions`
- **Predictions**: `/api/{vertical}/predictions`, `/api/{vertical}/predictions/{id}`

## Customization

### Adding a New Vertical

1. Create a new route: `app/[vertical-name]/page.tsx`
2. Use the `VerticalLayout` wrapper component
3. Include shared components (Authentication, Bankroll, RiskMetrics, AuditLog)
4. Add the vertical to the navigation in `components/Navbar.tsx`
5. Add the vertical card to the landing page

### Modifying Theme Colors

Edit `tailwind.config.js` to customize the color palette:

```js
colors: {
  'trading-bg': '#0a0e27',
  'trading-card': '#141829',
  // ... other colors
}
```

## Technologies Used

- **Next.js 14+** - React framework with App Router
- **TypeScript** - Type-safe development
- **Tailwind CSS** - Utility-first CSS framework
- **Lucide React** - Icon library
- **React 18** - Latest React features

## Performance Optimizations

- Server-side rendering with Next.js
- Optimized images and assets
- CSS-in-JS with Tailwind for minimal bundle
- Lazy loading of route components

## License

Private use only. All rights reserved.

## Support

For questions or issues, contact the development team.
