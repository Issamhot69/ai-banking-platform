import React, { useState } from 'react';
import api from '../services/api';

const loanTypes = ['personal', 'mortgage', 'auto', 'business', 'education'];

const Loans: React.FC = () => {
  const [amount, setAmount] = useState(10000);
  const [term, setTerm] = useState(24);
  const [loanType, setLoanType] = useState('personal');
  const [simulation, setSimulation] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const simulate = async () => {
    setLoading(true);
    try {
      const res = await api.post('http://localhost:8014/api/v1/loans/simulate', {
        amount,
        term_months: term,
        loan_type: loanType,
      });
      setSimulation(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6 space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-white">Simulateur de Prêts</h2>
        <p className="text-gray-500 text-sm">Calcul des mensualités et taux d'intérêt</p>
      </div>

      <div className="grid grid-cols-2 gap-6">
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 space-y-4">
          <h3 className="text-white font-semibold">Paramètres du prêt</h3>

          <div>
            <label className="text-gray-400 text-sm block mb-1">Type de prêt</label>
            <select
              value={loanType}
              onChange={(e) => setLoanType(e.target.value)}
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-white"
            >
              {loanTypes.map(t => (
                <option key={t} value={t}>{t.charAt(0).toUpperCase() + t.slice(1)}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="text-gray-400 text-sm block mb-1">Montant: {amount.toLocaleString()} EUR</label>
            <input
              type="range" min={1000} max={100000} step={1000}
              value={amount}
              onChange={(e) => setAmount(Number(e.target.value))}
              className="w-full accent-blue-500"
            />
            <div className="flex justify-between text-xs text-gray-500 mt-1">
              <span>1,000 EUR</span><span>100,000 EUR</span>
            </div>
          </div>

          <div>
            <label className="text-gray-400 text-sm block mb-1">Durée: {term} mois</label>
            <input
              type="range" min={6} max={84} step={6}
              value={term}
              onChange={(e) => setTerm(Number(e.target.value))}
              className="w-full accent-blue-500"
            />
            <div className="flex justify-between text-xs text-gray-500 mt-1">
              <span>6 mois</span><span>84 mois</span>
            </div>
          </div>

          <button
            onClick={simulate}
            disabled={loading}
            className="w-full bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-semibold py-3 rounded-lg"
          >
            {loading ? 'Calcul...' : 'Simuler le prêt'}
          </button>
        </div>

        {simulation ? (
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 space-y-4">
            <h3 className="text-white font-semibold">Résultat de simulation</h3>
            <div className="grid grid-cols-2 gap-4">
              {[
                { label: 'Mensualité', value: `${parseFloat(simulation.monthly_payment).toFixed(2)} EUR`, color: 'text-blue-400' },
                { label: 'Taux annuel', value: `${parseFloat(simulation.interest_rate).toFixed(2)}%`, color: 'text-yellow-400' },
                { label: 'Total remboursé', value: `${parseFloat(simulation.total_repayment).toFixed(2)} EUR`, color: 'text-white' },
                { label: 'Coût du crédit', value: `${parseFloat(simulation.total_interest).toFixed(2)} EUR`, color: 'text-red-400' },
              ].map((item) => (
                <div key={item.label} className="bg-gray-800 rounded-lg p-4">
                  <p className="text-gray-400 text-xs mb-1">{item.label}</p>
                  <p className={`text-xl font-bold ${item.color}`}>{item.value}</p>
                </div>
              ))}
            </div>

            <div>
              <h4 className="text-white font-medium mb-3">Échéancier (3 premières mensualités)</h4>
              <div className="space-y-2">
                {simulation.schedule?.slice(0, 3).map((item: any) => (
                  <div key={item.installment} className="flex justify-between items-center bg-gray-800 rounded-lg px-4 py-3">
                    <span className="text-gray-400 text-sm">Mois {item.installment} — {item.due_date}</span>
                    <div className="flex gap-4 text-sm">
                      <span className="text-blue-400">Capital: {parseFloat(item.principal).toFixed(2)}</span>
                      <span className="text-yellow-400">Intérêts: {parseFloat(item.interest).toFixed(2)}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        ) : (
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 flex items-center justify-center">
            <p className="text-gray-500">Lance une simulation pour voir les résultats</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default Loans;
