import React, { useEffect, useState } from 'react';
import api from '../services/api';

const statusColors: Record<string, string> = {
  active: 'bg-green-900/50 text-green-400 border border-green-700',
  frozen: 'bg-blue-900/50 text-blue-400 border border-blue-700',
  cancelled: 'bg-red-900/50 text-red-400 border border-red-700',
};

const Cards: React.FC = () => {
  const [cards, setCards] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get('http://localhost:8010/api/v1/cards')
      .then(res => setCards(res.data || []))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="p-6 space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-white">Cartes Virtuelles</h2>
        <p className="text-gray-500 text-sm">{cards.length} cartes émises</p>
      </div>

      <div className="grid grid-cols-3 gap-4">
        {[
          { label: 'Total cartes', value: cards.length, color: 'text-white' },
          { label: 'Actives', value: cards.filter(c => c.status === 'active').length, color: 'text-green-400' },
          { label: 'Gelées', value: cards.filter(c => c.status === 'frozen').length, color: 'text-blue-400' },
        ].map((s) => (
          <div key={s.label} className="bg-gray-900 border border-gray-800 rounded-xl p-5">
            <p className="text-gray-400 text-sm">{s.label}</p>
            <p className={`text-3xl font-bold mt-1 ${s.color}`}>{s.value}</p>
          </div>
        ))}
      </div>

      {loading ? (
        <div className="text-blue-400 animate-pulse">Chargement...</div>
      ) : (
        <div className="grid grid-cols-1 gap-4">
          {cards.map((card) => (
            <div key={card.id} className="bg-gray-900 border border-gray-800 rounded-xl p-6">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className={`w-12 h-8 rounded-md flex items-center justify-center text-xs font-bold text-white ${card.card_type === 'visa' ? 'bg-blue-700' : 'bg-red-700'}`}>
                    {card.card_type?.toUpperCase()}
                  </div>
                  <div>
                    <p className="text-white font-mono text-lg">{card.card_number_masked}</p>
                    <p className="text-gray-400 text-sm">{card.card_holder_name}</p>
                  </div>
                </div>
                <div className="flex items-center gap-6">
                  <div className="text-right">
                    <p className="text-gray-400 text-xs">Limite journalière</p>
                    <p className="text-white font-semibold">{parseFloat(card.daily_limit).toFixed(0)} EUR</p>
                  </div>
                  <div className="text-right">
                    <p className="text-gray-400 text-xs">Expiry</p>
                    <p className="text-white font-semibold">{card.expiry_month}/{card.expiry_year}</p>
                  </div>
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${statusColors[card.status] || statusColors.active}`}>
                    {card.status}
                  </span>
                </div>
              </div>
            </div>
          ))}
          {cards.length === 0 && (
            <div className="bg-gray-900 border border-gray-800 rounded-xl p-12 text-center text-gray-500">
              💳 Aucune carte émise
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default Cards;
