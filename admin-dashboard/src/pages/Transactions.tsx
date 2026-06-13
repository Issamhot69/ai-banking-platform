import React, { useEffect, useState } from 'react';
import { statsService } from '../services/api';
import { Transaction } from '../types';

const statusColors: Record<string, string> = {
  completed: 'bg-green-900/50 text-green-400 border border-green-700',
  pending: 'bg-yellow-900/50 text-yellow-400 border border-yellow-700',
  flagged: 'bg-red-900/50 text-red-400 border border-red-700',
  reversed: 'bg-gray-700/50 text-gray-400 border border-gray-600',
};

const Transactions: React.FC = () => {
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');

  useEffect(() => {
    statsService.getTransactions()
      .then(res => setTransactions(res.data.transactions || []))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const filtered = filter === 'all' ? transactions : transactions.filter(t => t.status === filter);

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white">Transactions</h2>
          <p className="text-gray-500 text-sm">{transactions.length} transactions au total</p>
        </div>
        <div className="flex gap-2">
          {['all', 'completed', 'flagged', 'reversed'].map(f => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                filter === f ? 'bg-blue-600 text-white' : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
              }`}
            >
              {f === 'all' ? 'Toutes' : f.charAt(0).toUpperCase() + f.slice(1)}
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <div className="text-blue-400 animate-pulse">Chargement...</div>
      ) : (
        <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-800">
                <th className="text-left px-6 py-4 text-gray-400 text-sm font-medium">Référence</th>
                <th className="text-left px-6 py-4 text-gray-400 text-sm font-medium">Type</th>
                <th className="text-left px-6 py-4 text-gray-400 text-sm font-medium">Montant</th>
                <th className="text-left px-6 py-4 text-gray-400 text-sm font-medium">Statut</th>
                <th className="text-left px-6 py-4 text-gray-400 text-sm font-medium">Risque</th>
                <th className="text-left px-6 py-4 text-gray-400 text-sm font-medium">Date</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((tx) => (
                <tr key={tx.id} className="border-b border-gray-800/50 hover:bg-gray-800/30 transition-colors">
                  <td className="px-6 py-4">
                    <span className="font-mono text-xs text-blue-400">{tx.reference}</span>
                  </td>
                  <td className="px-6 py-4">
                    <span className="text-white text-sm capitalize">{tx.type}</span>
                  </td>
                  <td className="px-6 py-4">
                    <span className="text-white font-semibold">{parseFloat(tx.amount).toFixed(2)} {tx.currency}</span>
                  </td>
                  <td className="px-6 py-4">
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${statusColors[tx.status] || statusColors.pending}`}>
                      {tx.status}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-2">
                      <div className="w-16 bg-gray-700 rounded-full h-1.5">
                        <div
                          className={`h-1.5 rounded-full ${tx.risk_score > 70 ? 'bg-red-500' : tx.risk_score > 30 ? 'bg-yellow-500' : 'bg-green-500'}`}
                          style={{ width: `${tx.risk_score}%` }}
                        />
                      </div>
                      <span className="text-xs text-gray-400">{tx.risk_score}</span>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <span className="text-gray-400 text-sm">{new Date(tx.created_at).toLocaleDateString('fr-FR')}</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {filtered.length === 0 && (
            <div className="text-center py-12 text-gray-500">Aucune transaction trouvée</div>
          )}
        </div>
      )}
    </div>
  );
};

export default Transactions;
