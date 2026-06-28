# Edge AI Platform - Quick Start Guide

## Installation & Setup (5 minutes)

### 1. Install Dependencies

```bash
cd edge-dashboard
npm install
```

### 2. Start Development Server

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

### 3. View the Application

- **Landing Page**: http://localhost:3000
- **Dashboard**: http://localhost:3000/dashboard
- **AI Releases**: http://localhost:3000/ai-releases
- **Economics**: http://localhost:3000/economics
- **Earnings**: http://localhost:3000/earnings
- **Crypto**: http://localhost:3000/crypto
- **MLB**: http://localhost:3000/mlb

## Project Structure at a Glance

```
edge-dashboard/
├── app/                    # Next.js routes & pages
│   ├── page.tsx           # Landing page
│   ├── layout.tsx         # Root layout
│   ├── dashboard/         # Dashboard page
│   └── {vertical}/        # 5 vertical pages
├── components/            # Reusable components
│   ├── Navbar.tsx         # Navigation
│   ├── Card.tsx           # Card wrapper
│   └── shared/            # Shared components
│       ├── Authentication.tsx
│       ├── Bankroll.tsx
│       ├── RiskMetrics.tsx
│       └── AuditLog.tsx
├── types/                 # TypeScript definitions
├── package.json           # Dependencies
├── tailwind.config.js     # Tailwind configuration
├── tsconfig.json          # TypeScript configuration
└── README.md              # Full documentation
```

## Key Features

### Shared Components (Used Across All Verticals)

1. **Authentication** - User login/profile display
2. **Bankroll** - Capital tracking and allocation
3. **Risk Metrics** - Sharpe ratio, drawdown, win rate, VaR
4. **Audit Log** - Transaction history

### 5 Verticals

Each vertical has:
- Prediction management interface
- Real-time statistics
- Shared components integration
- Mobile responsive design

## Common Tasks

### Add a New Prediction (Example)

```tsx
// In any vertical page component
<Card>
  <h2 className="text-2xl font-bold text-trading-text mb-4">
    Create Prediction
  </h2>
  <input 
    type="text" 
    className="trading-input w-full mb-4"
    placeholder="Event name"
  />
  <input 
    type="range" 
    min="0" 
    max="100"
    className="w-full"
  />
  <button className="trading-btn w-full mt-4">
    Create Prediction
  </button>
</Card>
```

### Use a Shared Component

```tsx
import { Bankroll } from '@/components/shared/Bankroll'

<Bankroll 
  total={100000} 
  available={75000} 
  allocated={25000}
/>
```

### Style with Tailwind

```tsx
<div className="trading-card p-6">
  <h3 className="text-trading-accent font-bold">Title</h3>
  <p className="text-gray-400">Description</p>
  <button className="trading-btn mt-4">Action</button>
</div>
```

## Customization

### Change Colors

Edit `tailwind.config.js`:

```js
colors: {
  'trading-bg': '#0a0e27',      // Change these
  'trading-accent': '#00d4ff',  // color values
  // ...
}
```

### Add Vertical Card to Landing Page

Edit `app/page.tsx`:

```tsx
const verticals = [
  // ... existing
  {
    id: 'my-vertical',
    name: 'My Vertical',
    description: 'Description here',
    icon: MyIcon,
    color: 'text-color-400',
    href: '/my-vertical',
  },
]
```

### Update Navigation Menu

Edit `components/Navbar.tsx`:

```tsx
const verticals = [
  // ... existing
  { name: 'My Vertical', href: '/my-vertical' },
]
```

## File Descriptions

### Configuration Files

| File | Purpose |
|------|---------|
| `next.config.js` | Next.js configuration |
| `tailwind.config.js` | Tailwind CSS theme |
| `tsconfig.json` | TypeScript settings |
| `package.json` | Dependencies & scripts |
| `.eslintrc.json` | ESLint rules |
| `.gitignore` | Git ignore patterns |

### App Files

| File | Purpose |
|------|---------|
| `app/page.tsx` | Landing page with hero & cards |
| `app/layout.tsx` | Root layout with navbar |
| `app/globals.css` | Global styles & trading UI |
| `app/dashboard/page.tsx` | Central dashboard |
| `app/{vertical}/page.tsx` | Vertical-specific pages |

### Component Files

| File | Purpose |
|------|---------|
| `components/Navbar.tsx` | Top navigation bar |
| `components/Card.tsx` | Reusable card component |
| `components/VerticalLayout.tsx` | Vertical page wrapper |
| `components/shared/*.tsx` | Shared across verticals |

## Development Workflow

1. **Make changes** to components or pages
2. **Hot reload** - Changes appear instantly in browser
3. **Check browser console** for errors
4. **Test responsive design** - Resize browser window
5. **Test navigation** - Click through all routes

## Building for Production

```bash
npm run build
npm start
```

The build optimizes:
- CSS (Tailwind purges unused styles)
- JavaScript (code splitting, minification)
- Images (optimization, lazy loading)

## Troubleshooting

### Port 3000 Already in Use

```bash
npm run dev -- -p 3001
```

### Styling Not Applied

1. Clear `.next/` folder: `rm -rf .next`
2. Restart dev server: `npm run dev`

### Module Not Found

```bash
rm -rf node_modules
npm install
npm run dev
```

### TypeScript Errors

Errors shown in terminal? Check `tsconfig.json` and type definitions in `types/index.ts`.

## Next Steps

1. **Read ARCHITECTURE.md** - Detailed system design
2. **Read IMPLEMENTATION_EXAMPLES.md** - Code patterns
3. **Add API integration** - Connect to backend
4. **Deploy to Vercel** - One-click deployment
5. **Add authentication** - Real user management

## Useful Links

- [Next.js Documentation](https://nextjs.org/docs)
- [Tailwind CSS](https://tailwindcss.com)
- [React Hooks Guide](https://react.dev/reference/react)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/)

## Commands Reference

```bash
# Development
npm run dev          # Start dev server
npm run build        # Build for production
npm start           # Run production build
npm run lint        # Check code quality

# File Management
npm install         # Install dependencies
npm update          # Update dependencies
npm uninstall       # Remove package
```

## Support & Resources

- Check README.md for full documentation
- Check ARCHITECTURE.md for system design
- Check IMPLEMENTATION_EXAMPLES.md for code patterns

---

**Happy trading! 🚀**
