# Edge AI Platform - Architecture & Implementation Guide

## Overview

Edge AI is a multi-vertical prediction platform built with Next.js 14, TypeScript, and Tailwind CSS. It provides a unified interface for managing AI-driven predictions across five distinct market verticals.

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Landing Page                             │
│              (Hero + 5 Vertical Cards)                       │
└──────────────────────┬──────────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┬──────────────┐
        │              │              │              │
        ▼              ▼              ▼              ▼
    ┌────────┐   ┌─────────┐   ┌────────┐   ┌─────────┐
    │Vertical│   │Vertical │   │Vertical│   │Vertical │
    │Pages   │   │Pages    │   │Pages   │   │Pages    │
    │(Routes)│   │(Routes) │   │(Routes)│   │(Routes) │
    └────────┘   └─────────┘   └────────┘   └─────────┘
        │              │              │              │
        └──────────────┼──────────────┴──────────────┘
                       │
        ┌──────────────▼──────────────┐
        │   Shared Components Layer   │
        ├─────────────────────────────┤
        │ • Authentication            │
        │ • Bankroll Management       │
        │ • Risk Metrics              │
        │ • Audit Log                 │
        └──────────────┬──────────────┘
                       │
        ┌──────────────▼──────────────┐
        │    Backend API Layer        │
        ├─────────────────────────────┤
        │ • User Management           │
        │ • Portfolio Tracking        │
        │ • Prediction Engine         │
        │ • Data Aggregation          │
        └─────────────────────────────┘
```

## Directory Structure & File Purposes

### `/app` - Next.js App Router

#### Root Layout & Pages
- **`layout.tsx`** - Root layout with Navbar, global setup
- **`page.tsx`** - Landing page with hero and 5 vertical cards
- **`globals.css`** - Global styles and custom trading UI components

#### Dashboard
- **`dashboard/page.tsx`** - Central hub for all verticals, showing portfolio overview and quick links

#### Vertical Routes
Each vertical follows the same structure:
- **`/{vertical}/page.tsx`** - Main vertical page with:
  - Authentication component
  - Bankroll tracker
  - Vertical-specific predictions/data
  - Risk metrics
  - Audit log

Verticals:
- `/ai-releases` - AI model releases and benchmarks
- `/economics` - Economic indicators and Fed decisions
- `/earnings` - Corporate earnings predictions
- `/crypto` - Cryptocurrency trading
- `/mlb` - Baseball strikeout predictions

### `/components` - Reusable React Components

#### Layout Components
- **`Navbar.tsx`** - Navigation bar with:
  - Brand logo
  - Desktop navigation menu
  - Mobile menu toggle
  - Vertical selector
  - User menu

- **`Card.tsx`** - Reusable trading card wrapper
- **`VerticalLayout.tsx`** - Layout wrapper for vertical pages (header + content area)

#### Shared Components (`/components/shared`)
These components are used across all verticals:

- **`Authentication.tsx`**
  - Displays user login status
  - Shows profile info (name, email)
  - Logout functionality
  - Props: `user` (optional)

- **`Bankroll.tsx`**
  - Tracks total capital, available funds, allocated capital
  - Shows allocation percentage
  - Adjust allocation button
  - Props: `total`, `available`, `allocated`, `currency`

- **`RiskMetrics.tsx`**
  - Displays Sharpe ratio, max drawdown, win rate, VaR
  - Color-coded status (good, warning, danger)
  - Default metrics provided
  - Props: `metrics` (optional array)

- **`AuditLog.tsx`**
  - Shows transaction history
  - Displays action, result, amount, timestamp
  - Color-coded by result type
  - Props: `entries` (optional), `limit` (number)

### `/types` - TypeScript Definitions

**`types/index.ts`** - Central type definitions for:
- User & authentication
- Bankroll tracking
- Risk metrics
- All prediction types (by vertical)
- API response schemas
- Portfolio statistics

## Component Composition Pattern

Each vertical page follows this structure:

```tsx
export default function VerticalPage() {
  return (
    <VerticalLayout title="..." description="...">
      {/* Shared Components Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <Authentication user={...} />
        <Bankroll total={...} available={...} allocated={...} />
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        <div className="lg:col-span-2">
          {/* Primary content: predictions, analysis, etc. */}
        </div>
        <div>
          {/* Statistics & upcoming events */}
        </div>
      </div>

      {/* Risk & Audit Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <RiskMetrics />
        <AuditLog limit={5} />
      </div>
    </VerticalLayout>
  )
}
```

## Styling System

### Tailwind Configuration

Custom color palette defined in `tailwind.config.js`:

```javascript
colors: {
  'trading-bg': '#0a0e27',      // Dark background
  'trading-card': '#141829',    // Card background
  'trading-border': '#2a2f4a',  // Border color
  'trading-text': '#e0e6ff',    // Text color
  'trading-accent': '#00d4ff',  // Primary accent (cyan)
  'trading-success': '#00c853', // Success (green)
  'trading-danger': '#ff3838',  // Error (red)
  'trading-warning': '#ffa500', // Warning (orange)
}
```

### CSS Classes (`globals.css`)

- `.trading-card` - Base card styling with hover effects
- `.trading-input` - Input field styling
- `.trading-btn` - Primary button (cyan background)
- `.trading-btn-secondary` - Secondary button (outline style)
- `.gradient-text` - Gradient text effect

### Responsive Design

- Mobile-first approach
- Breakpoints:
  - `sm:` 640px (small screens)
  - `md:` 768px (tablets)
  - `lg:` 1024px (desktops)

Grid layouts:
- Mobile: 1 column
- Tablet: 2 columns
- Desktop: 3-5 columns (varies by section)

## Data Flow & State Management

### Current Implementation (Demo)

The application uses mock data defined directly in components. Each component accepts props for data:

```tsx
<Bankroll 
  total={100000} 
  available={75000} 
  allocated={25000} 
/>

<RiskMetrics 
  metrics={[
    { label: 'Sharpe Ratio', value: 1.24, status: 'good' },
    // ...
  ]}
/>
```

### Backend Integration (Next Steps)

To integrate with a backend API:

1. **Create API client** (`lib/api.ts`):
```tsx
export const api = {
  auth: {
    login: (email, password) => fetch(`${API_BASE_URL}/auth/login`, ...),
    logout: () => fetch(`${API_BASE_URL}/auth/logout`, ...),
    getProfile: () => fetch(`${API_BASE_URL}/auth/profile`, ...),
  },
  bankroll: {
    getBalance: () => fetch(`${API_BASE_URL}/bankroll/balance`, ...),
    allocate: (amount) => fetch(`${API_BASE_URL}/bankroll/allocate`, ...),
  },
  // ... other endpoints
}
```

2. **Use React hooks** (e.g., `useEffect`, `useState`):
```tsx
const [bankroll, setBankroll] = useState(null)
const [loading, setLoading] = useState(true)

useEffect(() => {
  api.bankroll.getBalance()
    .then(data => setBankroll(data))
    .finally(() => setLoading(false))
}, [])
```

3. **Consider state management**:
   - Small app: Use React hooks + Context API
   - Medium app: Use Zustand or Jotai
   - Large app: Use TanStack Query (React Query)

## Routing Structure

```
/                          - Landing page
/dashboard                 - Portfolio dashboard
/ai-releases              - AI Releases vertical
/economics                - Economics vertical
/earnings                 - Earnings vertical
/crypto                   - Crypto vertical
/mlb                      - MLB vertical
```

## Mobile Responsiveness

### Breakpoint Strategy

- **Mobile (< 768px)**
  - Single column layouts
  - Hamburger menu navigation
  - Larger touch targets
  - Stacked components

- **Tablet (768px - 1024px)**
  - Two column layouts
  - Horizontal menu
  - Condensed spacing

- **Desktop (> 1024px)**
  - Multi-column layouts (3-5 columns)
  - Full navigation
  - Optimized spacing

### Navigation Menu

Mobile navigation uses `<Menu>` and `<X>` icons from Lucide React to toggle a dropdown menu.

## Color Coding & User Feedback

### Status Indicators

- **Green (`text-trading-success`)** - Positive results, wins, bullish
- **Red (`text-trading-danger`)** - Losses, bearish, errors
- **Orange (`text-trading-warning`)** - Caution, pending, review needed
- **Cyan (`text-trading-accent`)** - Primary action, accent, neutral

### Confidence Visualization

Progress bars indicate confidence levels:
- **70%+** - Green (high confidence)
- **50-70%** - Orange (medium confidence)
- **<50%** - Red (low confidence)

## Configuration Files

### `next.config.js`
- React strict mode enabled
- Default Next.js configuration

### `tailwind.config.js`
- Custom color palette
- Extended theme configuration
- Content paths for Tailwind scanning

### `postcss.config.js`
- Tailwind CSS plugin
- Autoprefixer for browser compatibility

### `tsconfig.json`
- TypeScript compiler options
- Path aliases (`@/*`)
- Strict type checking enabled

### `.eslintrc.json`
- ESLint configuration for Next.js
- Core web vitals rules

## Performance Considerations

1. **Code Splitting**
   - Next.js automatically code-splits at route level
   - Each vertical loads only its necessary code

2. **Image Optimization**
   - Use Next.js Image component for images
   - Automatic optimization and lazy loading

3. **CSS Optimization**
   - Tailwind purges unused styles
   - Only loads CSS for present classes

4. **Component Optimization**
   - Use `'use client'` directive for interactive components
   - Memoize expensive computations

## API Integration Points

### Required Backend Endpoints

**Authentication**
- `POST /api/auth/login` - User login
- `POST /api/auth/logout` - User logout
- `GET /api/auth/profile` - Get current user

**Bankroll**
- `GET /api/bankroll/balance` - Get balance
- `POST /api/bankroll/allocate` - Adjust allocation

**Predictions**
- `GET /api/{vertical}/predictions` - List predictions
- `POST /api/{vertical}/predictions` - Create prediction
- `GET /api/{vertical}/predictions/{id}` - Get prediction details
- `PUT /api/{vertical}/predictions/{id}` - Update prediction
- `DELETE /api/{vertical}/predictions/{id}` - Delete prediction

**Risk Metrics**
- `GET /api/metrics/performance` - Get performance metrics
- `GET /api/metrics/risk` - Get risk metrics

**Audit Log**
- `GET /api/audit/transactions` - List transactions
- `GET /api/audit/transactions/{id}` - Get transaction details

## Testing Strategy

### Component Testing
- Use Jest + React Testing Library
- Test component rendering and interactions
- Mock API responses

### Integration Testing
- Test data flow between components
- Test navigation between verticals
- Test responsive behavior

### E2E Testing
- Use Playwright or Cypress
- Test full user workflows
- Test API integration

## Deployment

### Vercel (Recommended for Next.js)

1. Connect GitHub repository
2. Configure environment variables
3. Deploy from `main` branch

### Docker

```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build
EXPOSE 3000
CMD ["npm", "start"]
```

### Environment Variables

- `NEXT_PUBLIC_API_BASE_URL` - Backend API URL
- `NEXT_PUBLIC_ENVIRONMENT` - Environment name

## Future Enhancements

1. **Real-time Updates**
   - WebSocket integration for live predictions
   - Push notifications for alerts

2. **Advanced Analytics**
   - Custom dashboards
   - Report generation
   - Performance attribution

3. **Machine Learning Integration**
   - Model prediction integration
   - Feature engineering pipeline

4. **Social Features**
   - Share predictions
   - Community leaderboards
   - Discussion forums

5. **Mobile App**
   - React Native version
   - Push notifications
   - Offline support

## Troubleshooting

### Common Issues

**Port 3000 already in use**
```bash
npm run dev -- -p 3001
```

**Module not found errors**
```bash
rm -rf .next node_modules
npm install
npm run dev
```

**Styling not applied**
- Clear browser cache
- Rebuild Tailwind: `npm run build`
- Check tailwind.config.js content paths

## Contributing

1. Create feature branch: `git checkout -b feature/your-feature`
2. Make changes following the established patterns
3. Test responsive design on multiple breakpoints
4. Submit pull request with description

## Resources

- [Next.js Documentation](https://nextjs.org/docs)
- [Tailwind CSS Documentation](https://tailwindcss.com/docs)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/)
- [React Documentation](https://react.dev)
