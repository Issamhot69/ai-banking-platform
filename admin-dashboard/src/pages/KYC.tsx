import React, { useEffect, useState } from 'react';
import api from '../services/api';

const statusColors: Record<string, string> = {
  verified: 'bg-green-900/50 text-green-400 border border-green-700',
  in_review: 'bg-yellow-900/50 text-yellow-400 border border-yellow-700',
  pending: 'bg-blue-900/50 text-blue-400 border border-blue-700',
  rejected: 'bg-red-900/50 text-red-400 border border-red-700',
};

const KYC: React.FC = () => {
  const [applications, setApplications] = useState<any[]>([]);
  const [stats, setStats] = useState<any>({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api.get('http://localhost:8008/api/v1/kyc/admin/applications'),
      api.get('http://localhost:8008/api/v1/kyc/admin/stats'),
    ]).then(([appsRes, statsRes]) => {
      setApplications(appsRes.data || []);
      setStats(statsRes.data || {});
    }).catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const handleReview = async (id: string, action: string) => {
    try {
      await api.post(`http://localhost:8008/api/v1/kyc/admin/applications/${id}/review`, { action });
      const res = await api.get('http://localhost:8008/api/v1/kyc/admin/applications');
      setApplications(res.data || []);
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="p-6 space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-white">Gestion KYC</h2>
        <p className="text-gray-500 text-sm">Vérification d'identité des clients</p>
      </div>

      <div className="grid grid-cols-4 gap-4">
        {[
          { label: 'Total', value: stats.total || 0, color: 'text-white' },
          { label: 'En attente', value: stats.pending || 0, color: 'text-blue-400' },
          { label: 'Vérifiés', value: stats.verified || 0, color: 'text-green-400' },
          { label: 'Rejetés', value: stats.rejected || 0, color: 'text-red-400' },
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
        <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-800">
                <th className="text-left px-6 py-4 text-gray-400 text-sm">Client</th>
                <th className="text-left px-6 py-4 text-gray-400 text-sm">Document</th>
                <th className="text-left px-6 py-4 text-gray-400 text-sm">Statut</th>
                <th className="text-left px-6 py-4 text-gray-400 text-sm">AI Score</th>
                <th className="text-left px-6 py-4 text-gray-400 text-sm">Date</th>
                <th className="text-left px-6 py-4 text-gray-400 text-sm">Actions</th>
              </tr>
            </thead>
            <tbody>
              {applications.map((app) => (
                <tr key={app.id} className="border-b border-gray-800/50 hover:bg-gray-800/30">
                  <td className="px-6 py-4">
                    <p className="text-white font-medium">{app.first_name} {app.last_name}</p>
                  </td>
                  <td className="px-6 py-4">
                    <span className="text-gray-400 text-sm capitalize">{app.document_type}</span>
                  </td>
                  <td className="px-6 py-4">
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${statusColors[app.status] || statusColors.pending}`}>
                      {app.status}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    <span className="text-gray-400 text-sm">
                      {app.ai_verification_result?.confidence_score || 'N/A'}%
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    <span className="text-gray-400 text-sm">
                      {new Date(app.created_at).toLocaleDateString('fr-FR')}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    {app.status === 'in_review' && (
                      <div className="flex gap-2">
                        <button
                          onClick={() => handleReview(app.id, 'approve')}
                          className="px-3 py-1 bg-green-700 hover:bg-green-600 text-white text-xs rounded-lg"
                        >
                          Approuver
                        </button>
                        <button
                          onClick={() => handleReview(app.id, 'reject')}
                          className="px-3 py-1 bg-red-700 hover:bg-red-600 text-white text-xs rounded-lg"
                        >
                          Rejeter
                        </button>
                      </div>
                    )}
                  </td>
                </tr>
              ))}
              {applications.length === 0 && (
                <tr><td colSpan={6} className="text-center py-12 text-gray-500">Aucune demande KYC</td></tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

export default KYC;
