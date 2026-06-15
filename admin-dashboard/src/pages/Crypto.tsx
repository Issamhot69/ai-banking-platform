import React, { useEffect, useState } from 'react';
import api from '../services/api';

const cryptoColors: Record<string, string> = {
  BTC: 'bg-orange-600',
  ETH: 'bg-blue-600',
  USDT: 'bg-green-600',
  BNB: 'bg-yellow-600',
  SOL: 'bg-purple-600',
  MAD_COIN: 'bg-red-600',
};

const Crypto: React.FC = () => {
  const [prices, setPrices] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get('http://localhost:8015/api/v1/crypto/prices')
      .then(res => setPrices(res.data || []))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="p-6 space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-white">Crypto Wallet</h2>
        <p className="text-gray-500 text-sm">Prix en temps réel — BTC, ETH, SOL, BNB, USDT</p>
      </div>

      {loading ? (
        <div className="text-blue-400 animate-pulse">Chargement des prix...</div>
      ) : (
        <div className="grid grid-cols-3 gap-4">
          {prices.map((crypto) => (
            <div key={crypto.currency} className="bg-gray-900 border border-gray-800 rounded-xl p-6">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div className={`w-10 h-10 rounded-full ${cryptoColors[crypto.currency] || 'bg-gray-600'} flex items-center justify-center text-white text-xs font-bold`}>
                    {crypto.currency.slice(0, 3)}
                  </div>
                  <span className="text-white font-semibold">{crypto.currency}</span>
                </div>
                <span className={`text-sm font-medium ${parseFloat(crypto.change_24h) >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                  {parseFloat(crypto.change_24h) >= 0 ? '+' : ''}{parseFloat(crypto.change_24h).toFixed(2)}%
                </span>
              </div>
              <p className="text-2xl font-bold text-white">{parseFloat(crypto.price_eur).toLocaleString('fr-FR')} EUR</p>
              <p className="text-gray-500 text-sm mt-1">{parseFloat(crypto.price_usd).toLocaleString('fr-FR')} USD</p>
            </div>
          ))}
        </div>
      )}

      <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
        <h3 className="text-white font-semibold mb-4">Cryptos supportées</h3>
        <div className="grid grid-cols-6 gap-3">
          {['BTC', 'ETH', 'USDT', 'BNB', 'SOL', 'MAD_COIN'].map((c) => (
            <div key={c} className="text-center">
              <div className={`w-12 h-12 rounded-full ${cryptoColors[c] || 'bg-gray-600'} flex items-center justify-center text-white text-xs font-bold mx-auto mb-2`}>
                {c.slice(0, 3)}
              </div>
              <p className="text-gray-400 text-xs">{c}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default Crypto;
