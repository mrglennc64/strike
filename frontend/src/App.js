import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { useAuthStore } from './store/auth';
import { Navbar } from './components/Navbar';
import { LoginPage } from './pages/LoginPage';
import { SignupPage } from './pages/SignupPage';
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
    const token = useAuthStore((state) => state.token);
    const isAuthenticated = !!token;
    return (_jsx(Router, { children: _jsxs("div", { className: "min-h-screen bg-gray-900", children: [isAuthenticated && _jsx(Navbar, {}), _jsx("main", { className: isAuthenticated ? "max-w-7xl mx-auto px-4 py-8" : "", children: _jsxs(Routes, { children: [_jsx(Route, { path: "/", element: isAuthenticated ? _jsx(DashboardPage, {}) : _jsx(LandingPage, {}) }), _jsx(Route, { path: "/dashboard", element: isAuthenticated ? _jsx(DashboardPage, {}) : _jsx(Navigate, { to: "/login" }) }), _jsx(Route, { path: "/verticals/:vertical", element: isAuthenticated ? _jsx(VerticalPage, {}) : _jsx(Navigate, { to: "/login" }) }), _jsx(Route, { path: "/login", element: _jsx(LoginPage, {}) }), _jsx(Route, { path: "/signup", element: _jsx(SignupPage, {}) }), _jsx(Route, { path: "/clv-tracker", element: isAuthenticated ? _jsx(CLVTrackerPage, {}) : _jsx(Navigate, { to: "/login" }) }), _jsx(Route, { path: "/predictions", element: isAuthenticated ? _jsx(PredictionsPage, {}) : _jsx(Navigate, { to: "/login" }) }), _jsx(Route, { path: "/place-bet", element: isAuthenticated ? _jsx(PlaceBetPage, {}) : _jsx(Navigate, { to: "/login" }) }), _jsx(Route, { path: "/positions", element: isAuthenticated ? _jsx(PositionsPage, {}) : _jsx(Navigate, { to: "/login" }) }), _jsx(Route, { path: "/audit", element: isAuthenticated ? _jsx(AuditPage, {}) : _jsx(Navigate, { to: "/login" }) }), _jsx(Route, { path: "/portfolio", element: isAuthenticated ? _jsx(PortfolioPage, {}) : _jsx(Navigate, { to: "/login" }) })] }) })] }) }));
}
export default App;
