import React, { useEffect, useState } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line } from 'recharts';
import api from '../services/api';

const StatCard = ({ title, value, icon, color }: any) => (
  <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
    <div className="flex items-center justify-between mb-4">
      <span className="text-gray-400 text-sm font-medium">{title}</span>
      <span className="text-2xl">{icon}</span>
    </div>
    <div className={`text-3xl font-bold ${color}`}>{value}</div>
  </div>
);

const Dashboard: React.FC = () => {
  const [transactions, setTransactions] = useState<any[]>([]);
  const [accounts, setAccounts] = useState<any>({ total_accounts: 0 });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        // Récupérer d'abord les comptes
        const accRes = await api.get('http://localhost:8002/api/v1/accounts');
        setAccounts(accRes.data);

        // Récupérer les transactions du premier compte
        if (accRes.data.accounts && accRes.data.accounts.length > 0) {
          const firstAccountId = accRes.data.accounts[0].id;
          const txRes = await api.get('http://localhost:8003/api/v1/transactions', {
            params: { account_id: firstAccountId, per_page: 50 }
          });
          setTransactions(txRes.data.transactions || []);
        }
      } catch (err) {
        console.error('Error:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const totalVolume = transactions.reduce((sum, tx) => sum + parseFloat(tx.amount || 0), 0);
  const flagged = transactions.filter(tx => tx.status === 'flagged').length;

  const chartData = [...transactions].reverse().slice(0, 10).map((tx, i) => ({
    name: `Tx${i + 1}`,
    amount: parseFloat(tx.amount),
    risk: tx.risk_score,
  }));

  if (loading) return (
    <div className="flex items-center justify-center h-64">
      <div className="text-blue-400 text-lg animate-pulse">Chargement...</div>
    </div>
  );

  return (
    <div className="p-6 space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-white mb-1">Dashboard</h2>
        <p className="text-gray-500 text-sm">Vue d'ensemble de la plateforme bancaire</p>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-3 gap-4">
        <StatCard title="Utilisateurs" value="2" icon="👥" color="text-blue-400" />
        <StatCard title="Comptes" value={accounts.total_accounts || 0} icon="🏦" color="text-green-400" />
        <StatCard title="Transactions" value={transactions.length} icon="💸" color="text-purple-400" />
        <StatCard title="Volume Total" value={`${totalVolume.toFixed(2)} EUR`} icon="💰" color="text-yellow-400" />
        <StatCard title="Fraudes Détectées" value={flagged} icon="🚨" color="text-red-400" />
        <StatCard title="Solde Total" value={`${accounts.total_balance || '0'} EUR`} icon="💳" color="text-orange-400" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
          <h3 className="text-white font-semibold mb-4">Volume des transactions</h3>
          {chartData.length > 0 ? (
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis dataKey="name" stroke="#6b7280" fontSize={12} />
                <YAxis stroke="#6b7280" fontSize={12} />
                <Tooltip contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: '8px' }} />
                <Bar dataKey="amount" fill="#3b82f6" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="flex items-center justify-center h-48 text-gray-600">Aucune transaction</div>
          )}
        </div>

        <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
          <h3 className="text-white font-semibold mb-4">Score de risque</h3>
          {chartData.length > 0 ? (
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis dataKey="name" stroke="#6b7280" fontSize={12} />
                <YAxis stroke="#6b7280" fontSize={12} />
                <Tooltip contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: '8px' }} />
                <Line type="monotone" dataKey="risk" stroke="#ef4444" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <div className="flex items-center justify-center h-48 text-gray-600">Aucune donnée</div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
