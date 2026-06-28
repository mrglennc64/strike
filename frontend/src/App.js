import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { DashboardPage } from './pages/DashboardPage';
import { CLVTrackerPage } from './pages/CLVTrackerPage';
import { PredictionsPage } from './pages/PredictionsPage';
import { PlaceBetPage } from './pages/PlaceBetPage';
import { PositionsPage } from './pages/PositionsPage';
import { AuditPage } from './pages/AuditPage';
import { LandingPage } from './pages/LandingPage';
import { VerticalPage } from './pages/VerticalPage';
import { PortfolioPage } from './pages/PortfolioPage';
function App() {
    return (_jsx(Router, { children: _jsx("div", { className: "min-h-screen bg-gray-900", children: _jsx("main", { children: _jsxs(Routes, { children: [_jsx(Route, { path: "/", element: _jsx(LandingPage, {}) }), _jsx(Route, { path: "/verticals/:vertical", element: _jsx(VerticalPage, {}) }), _jsx(Route, { path: "/dashboard", element: _jsx(DashboardPage, {}) }), _jsx(Route, { path: "/clv-tracker", element: _jsx(CLVTrackerPage, {}) }), _jsx(Route, { path: "/predictions", element: _jsx(PredictionsPage, {}) }), _jsx(Route, { path: "/place-bet", element: _jsx(PlaceBetPage, {}) }), _jsx(Route, { path: "/positions", element: _jsx(PositionsPage, {}) }), _jsx(Route, { path: "/audit", element: _jsx(AuditPage, {}) }), _jsx(Route, { path: "/portfolio", element: _jsx(PortfolioPage, {}) })] }) }) }) }));
}
export default App;
