import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuthStore } from '../store/auth';
export const LoginPage = () => {
    const navigate = useNavigate();
    const login = useAuthStore((state) => state.login);
    const error = useAuthStore((state) => state.error);
    const isLoading = useAuthStore((state) => state.isLoading);
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            await login(email, password);
            navigate('/dashboard');
        }
        catch (err) {
            // Error is handled by store
        }
    };
    return (_jsx("div", { className: "min-h-screen flex items-center justify-center bg-gray-900", children: _jsxs("div", { className: "bg-gray-800 p-8 rounded-lg shadow-lg max-w-md w-full", children: [_jsx("h1", { className: "text-2xl font-bold text-white mb-6", children: "Login" }), error && _jsx("div", { className: "bg-red-600 text-white p-3 rounded mb-4", children: error }), _jsxs("form", { onSubmit: handleSubmit, className: "space-y-4", children: [_jsxs("div", { children: [_jsx("label", { className: "block text-gray-300 mb-2", children: "Email" }), _jsx("input", { type: "email", value: email, onChange: (e) => setEmail(e.target.value), className: "w-full px-4 py-2 bg-gray-700 text-white rounded border border-gray-600", required: true })] }), _jsxs("div", { children: [_jsx("label", { className: "block text-gray-300 mb-2", children: "Password" }), _jsx("input", { type: "password", value: password, onChange: (e) => setPassword(e.target.value), className: "w-full px-4 py-2 bg-gray-700 text-white rounded border border-gray-600", required: true })] }), _jsx("button", { type: "submit", disabled: isLoading, className: "w-full bg-blue-600 hover:bg-blue-700 text-white py-2 rounded font-medium disabled:opacity-50", children: isLoading ? 'Loading...' : 'Login' })] }), _jsxs("p", { className: "text-gray-400 mt-4 text-center", children: ["Don't have an account?", ' ', _jsx(Link, { to: "/signup", className: "text-blue-500 hover:text-blue-400", children: "Sign up" })] })] }) }));
};
