import React, { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Transactions from './pages/Transactions';
import Users from './pages/Users';
import KYC from './pages/KYC';
import Cards from './pages/Cards';
import Crypto from './pages/Crypto';
import Loans from './pages/Loans';
import './index.css';

const App: React.FC = () => {
  const [token, setToken] = useState<string | null>(null);
  const [activePage, setActivePage] = useState('dashboard');

  useEffect(() => {
    const saved = localStorage.getItem('admin_token');
    if (saved) setToken(saved);
  }, []);

  const handleLogin = (t: string) => setToken(t);

  const handleLogout = () => {
    localStorage.removeItem('admin_token');
    setToken(null);
  };

  if (!token) return <Login onLogin={handleLogin} />;

  const renderPage = () => {
    switch (activePage) {
      case 'dashboard': return <Dashboard />;
      case 'transactions': return <Transactions />;
      case 'users': return <Users />;
      case 'kyc': return <KYC />;
      case 'cards': return <Cards />;
      case 'crypto': return <Crypto />;
      case 'loans': return <Loans />;
      case 'accounts': return (
        <div className="p-6">
          <h2 className="text-2xl font-bold text-white mb-4">Comptes Bancaires</h2>
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-8 text-center text-gray-500">
            🏦 Section comptes — en cours de développement
          </div>
        </div>
      );
      case 'fraud': return (
        <div className="p-6">
          <h2 className="text-2xl font-bold text-white mb-4">Détection de Fraude</h2>
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-8 text-center text-gray-500">
            🚨 Section fraude — en cours de développement
          </div>
        </div>
      );
      case 'swift': return (
        <div className="p-6">
          <h2 className="text-2xl font-bold text-white mb-4">Virements SWIFT</h2>
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-8 text-center text-gray-500">
            🌍 Section SWIFT MT103 — en cours de développement
          </div>
        </div>
      );
      case 'sepa': return (
        <div className="p-6">
          <h2 className="text-2xl font-bold text-white mb-4">Virements SEPA</h2>
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-8 text-center text-gray-500">
            🇪🇺 Section SEPA SCT/SCT Inst — en cours de développement
          </div>
        </div>
      );
      default: return <Dashboard />;
    }
  };

  return (
    <div className="flex min-h-screen bg-gray-950">
      <Sidebar activePage={activePage} setActivePage={setActivePage} />
      <div className="flex-1 flex flex-col">
        <header className="bg-gray-900 border-b border-gray-800 px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-green-400 animate-pulse"></div>
            <span className="text-green-400 text-sm font-medium">Système opérationnel</span>
          </div>
          <button
            onClick={handleLogout}
            className="text-gray-400 hover:text-white text-sm transition-colors"
          >
            Déconnexion →
          </button>
        </header>
        <main className="flex-1 overflow-auto">
          {renderPage()}
        </main>
      </div>
    </div>
  );
};

export default App;
