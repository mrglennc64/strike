import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { DashboardPage } from './pages/DashboardPage'
import { CLVTrackerPage } from './pages/CLVTrackerPage'
import { PredictionsPage } from './pages/PredictionsPage'
import { PlaceBetPage } from './pages/PlaceBetPage'
import { PositionsPage } from './pages/PositionsPage'
import { AuditPage } from './pages/AuditPage'
import { LandingPage } from './pages/LandingPage'
import { VerticalPage } from './pages/VerticalPage'
import { PortfolioPage } from './pages/PortfolioPage'
import { MLBStrikeoutPredictor } from './components/MLBStrikeoutPredictor'

function App() {
  return (
    <Router basename="/">
      <div className="min-h-screen bg-gray-900">
        <main>
          <Routes>
            <Route path="/" element={<LandingPage />} />
            <Route path="/verticals/mlb" element={<MLBStrikeoutPredictor />} />
            <Route path="/verticals/:vertical" element={<VerticalPage />} />
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/clv-tracker" element={<CLVTrackerPage />} />
            <Route path="/predictions" element={<PredictionsPage />} />
            <Route path="/place-bet" element={<PlaceBetPage />} />
            <Route path="/positions" element={<PositionsPage />} />
            <Route path="/audit" element={<AuditPage />} />
            <Route path="/portfolio" element={<PortfolioPage />} />
          </Routes>
        </main>
      </div>
    </Router>
  )
}

export default App
