import React, { useState } from 'react';
import { useCalls, useCallDetail, useDashboardStats } from '../hooks/useAnalysis';
import CallLogTable from '../components/CallLogTable';
import RiskGauge from '../components/RiskGauge';
import SignalBreakdownChart from '../components/SignalBreakdown';
import { CallRecord } from '../api/types';
import { X, PhoneCall, ShieldAlert, Activity, UserCheck } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';

const AnalystDashboard: React.FC = () => {
  const [page, setPage] = useState(1);
  const [riskFilter, setRiskFilter] = useState('');
  const [selectedCallId, setSelectedCallId] = useState<string | null>(null);

  const { data: callsData, isLoading: callsLoading } = useCalls(page, 10, riskFilter);
  const { data: callDetail, isLoading: detailLoading } = useCallDetail(selectedCallId || '', !!selectedCallId);
  const { data: statsData, isLoading: statsLoading, isError: statsError } = useDashboardStats();

  const handleRowClick = (call: CallRecord) => {
    setSelectedCallId(call.id);
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center mb-2">
        <h1 className="text-2xl font-bold text-white">Analyst Dashboard</h1>
      </div>

      {/* Stats Row */}
      {statsLoading ? (
        <div className="h-24 flex items-center justify-center glass-card">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-electric-blue"></div>
        </div>
      ) : statsError ? (
        <div className="bg-red-500/10 border border-red-500/50 rounded-lg p-4 text-red-400">
          Failed to load dashboard statistics.
        </div>
      ) : statsData ? (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <StatCard title="Total Monitored" value={statsData.total_monitored.toString()} icon={<PhoneCall className="w-5 h-5 text-electric-blue" />} />
          <StatCard title="Flagged High Risk" value={`${statsData.flagged_high_risk_percentage.toFixed(1)}%`} icon={<ShieldAlert className="w-5 h-5 text-red-500" />} />
          <StatCard title="Avg Risk Score" value={statsData.average_risk_score.toFixed(1)} icon={<Activity className="w-5 h-5 text-amber-500" />} />
          <StatCard title="Challenges Passed" value={`${statsData.challenges_passed_percentage.toFixed(1)}%`} icon={<UserCheck className="w-5 h-5 text-green-500" />} />
        </div>
      ) : null}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Content Area */}
        <div className="lg:col-span-2 space-y-6">
          <div className="glass-card p-4 h-64 flex flex-col">
            <h3 className="text-sm font-semibold text-gray-300 mb-4">Risk Score Distribution (7d)</h3>
            <div className="flex-1 min-h-0">
              {statsLoading ? (
                <div className="h-full flex items-center justify-center">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-electric-blue"></div>
                </div>
              ) : statsError || !statsData ? (
                <div className="h-full flex items-center justify-center text-red-400 text-sm">
                  Distribution data unavailable.
                </div>
              ) : (
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={statsData.risk_distribution} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                    <XAxis dataKey="name" stroke="#4b5563" fontSize={12} tickLine={false} axisLine={false} />
                    <YAxis stroke="#4b5563" fontSize={12} tickLine={false} axisLine={false} allowDecimals={false} />
                    <Tooltip 
                      cursor={{ fill: '#1f2937' }}
                      contentStyle={{ backgroundColor: '#0a0e27', borderColor: '#1f2937', color: '#fff' }}
                    />
                    <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                      {statsData.risk_distribution.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              )}
            </div>
          </div>

          {callsLoading ? (
            <div className="h-64 flex items-center justify-center glass-card">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-electric-blue"></div>
            </div>
          ) : (
            <CallLogTable 
              calls={callsData?.items || []}
              total={callsData?.total || 0}
              page={page}
              pageSize={10}
              onPageChange={setPage}
              onRiskFilter={setRiskFilter}
              onRowClick={handleRowClick}
            />
          )}
        </div>

        {/* Side Panel */}
        <div className="lg:col-span-1">
          {selectedCallId ? (
            <div className="glass-card p-5 h-full flex flex-col overflow-hidden animate-in slide-in-from-right-8 duration-300">
              <div className="flex justify-between items-center mb-6 pb-4 border-b border-white/10">
                <h3 className="font-semibold text-white">Call Details</h3>
                <button 
                  onClick={() => setSelectedCallId(null)}
                  className="text-gray-400 hover:text-white p-1 rounded hover:bg-white/10 transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {detailLoading ? (
                 <div className="flex-1 flex items-center justify-center">
                   <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-electric-blue"></div>
                 </div>
              ) : callDetail ? (
                <div className="flex-1 overflow-y-auto pr-2 space-y-6 pb-4">
                  <div className="flex justify-center">
                    <RiskGauge score={callDetail.composite_risk_score} riskLevel={callDetail.risk_level} size={160} />
                  </div>
                  
                  {callDetail.signal_breakdown && (
                    <SignalBreakdownChart 
                      breakdown={callDetail.signal_breakdown} 
                      matchedPatterns={callDetail.matched_patterns}
                    />
                  )}

                  {callDetail.transcript && (
                    <div className="pt-4 border-t border-white/10">
                      <h4 className="text-sm font-semibold text-gray-300 mb-4">Transcript</h4>
                      <p className="text-gray-400 text-sm leading-relaxed whitespace-pre-wrap max-h-32 overflow-y-auto">{callDetail.transcript}</p>
                    </div>
                  )}
                </div>
              ) : (
                <div className="flex-1 flex items-center justify-center text-gray-500">
                  Failed to load details
                </div>
              )}
            </div>
          ) : (
            <div className="glass-card p-6 h-full flex flex-col items-center justify-center text-center text-gray-500 border-dashed">
              <PhoneCall className="w-12 h-12 mb-4 opacity-20" />
              <p>Select a call from the log to view detailed analysis, signals, and timeline.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

const StatCard = ({ title, value, icon }: { title: string, value: string, icon: React.ReactNode }) => (
  <div className="glass-card p-4 flex items-center justify-between">
    <div>
      <p className="text-xs text-gray-400 font-medium uppercase tracking-wider mb-1">{title}</p>
      <p className="text-2xl font-bold text-white">{value}</p>
    </div>
    <div className="p-3 bg-white/5 rounded-lg border border-white/5">
      {icon}
    </div>
  </div>
);

export default AnalystDashboard;
