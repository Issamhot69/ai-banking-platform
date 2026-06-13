import React, { useState } from 'react';

const mockUsers = [
  { id: '1', email: 'demo2@bank.com', first_name: 'Jean', last_name: 'Dupont', is_active: true, kyc_status: 'pending', created_at: '2026-06-13' },
  { id: '2', email: 'marie@bank.com', first_name: 'Marie', last_name: 'Martin', is_active: true, kyc_status: 'pending', created_at: '2026-06-13' },
];

const kycColors: Record<string, string> = {
  pending: 'bg-yellow-900/50 text-yellow-400 border border-yellow-700',
  verified: 'bg-green-900/50 text-green-400 border border-green-700',
  rejected: 'bg-red-900/50 text-red-400 border border-red-700',
};

const Users: React.FC = () => {
  const [users] = useState(mockUsers);

  return (
    <div className="p-6 space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-white">Utilisateurs</h2>
        <p className="text-gray-500 text-sm">{users.length} utilisateurs enregistrés</p>
      </div>

      <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="border-b border-gray-800">
              <th className="text-left px-6 py-4 text-gray-400 text-sm font-medium">Utilisateur</th>
              <th className="text-left px-6 py-4 text-gray-400 text-sm font-medium">Email</th>
              <th className="text-left px-6 py-4 text-gray-400 text-sm font-medium">KYC</th>
              <th className="text-left px-6 py-4 text-gray-400 text-sm font-medium">Statut</th>
              <th className="text-left px-6 py-4 text-gray-400 text-sm font-medium">Inscrit le</th>
            </tr>
          </thead>
          <tbody>
            {users.map((user) => (
              <tr key={user.id} className="border-b border-gray-800/50 hover:bg-gray-800/30 transition-colors">
                <td className="px-6 py-4">
                  <div className="flex items-center gap-3">
                    <div className="w-9 h-9 rounded-full bg-blue-600 flex items-center justify-center font-bold text-sm">
                      {user.first_name[0]}{user.last_name[0]}
                    </div>
                    <span className="text-white font-medium">{user.first_name} {user.last_name}</span>
                  </div>
                </td>
                <td className="px-6 py-4 text-gray-400 text-sm">{user.email}</td>
                <td className="px-6 py-4">
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${kycColors[user.kyc_status]}`}>
                    {user.kyc_status}
                  </span>
                </td>
                <td className="px-6 py-4">
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${user.is_active ? 'bg-green-900/50 text-green-400 border border-green-700' : 'bg-gray-700 text-gray-400'}`}>
                    {user.is_active ? 'Actif' : 'Inactif'}
                  </span>
                </td>
                <td className="px-6 py-4 text-gray-400 text-sm">{user.created_at}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default Users;
