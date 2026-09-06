import React from 'react';
import { CallRecord } from '../api/types';
import { ChevronLeft, ChevronRight, ShieldAlert, ShieldCheck, Shield } from 'lucide-react';

interface CallLogTableProps {
  calls: CallRecord[];
  total: number;
  page: number;
  pageSize: number;
  onPageChange: (page: number) => void;
  onRiskFilter: (level: string) => void;
  onRowClick: (call: CallRecord) => void;
}

const CallLogTable: React.FC<CallLogTableProps> = ({
  calls,
  total,
  page,
  pageSize,
  onPageChange,
  onRiskFilter,
  onRowClick,
}) => {
  const totalPages = Math.ceil(total / pageSize);

  const getRiskBadge = (level: string) => {
    switch (level.toLowerCase()) {
      case 'escalate':
        return <span className="px-2 py-1 rounded text-xs font-medium bg-red-500/20 text-red-400 border border-red-500/20 flex items-center w-max"><ShieldAlert className="w-3 h-3 mr-1"/> Escalate</span>;
      case 'challenge':
        return <span className="px-2 py-1 rounded text-xs font-medium bg-amber-500/20 text-amber-400 border border-amber-500/20 flex items-center w-max"><Shield className="w-3 h-3 mr-1"/> Challenge</span>;
      case 'pass':
      default:
        return <span className="px-2 py-1 rounded text-xs font-medium bg-green-500/20 text-green-400 border border-green-500/20 flex items-center w-max"><ShieldCheck className="w-3 h-3 mr-1"/> Pass</span>;
    }
  };

  return (
    <div className="w-full bg-navy-light/40 border border-white/5 rounded-xl overflow-hidden flex flex-col">
      <div className="p-4 border-b border-white/5 flex justify-between items-center">
        <h3 className="font-semibold text-white">Recent Interactions</h3>
        <select 
          className="bg-navy border border-white/10 rounded-md text-sm text-gray-300 py-1.5 px-3 focus:outline-none focus:border-electric-blue"
          onChange={(e) => onRiskFilter(e.target.value)}
        >
          <option value="">All Risk Levels</option>
          <option value="escalate">Escalate</option>
          <option value="challenge">Challenge</option>
          <option value="pass">Pass</option>
        </select>
      </div>
      
      <div className="overflow-x-auto flex-1">
        <table className="w-full text-left text-sm text-gray-400">
          <thead className="bg-navy/50 text-xs uppercase text-gray-500 border-b border-white/5">
            <tr>
              <th className="px-4 py-3 font-medium">Time</th>
              <th className="px-4 py-3 font-medium">Caller ID</th>
              <th className="px-4 py-3 font-medium">Risk Level</th>
              <th className="px-4 py-3 font-medium">Score</th>
              <th className="px-4 py-3 font-medium">Transcript Snippet</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/5">
            {calls.map((call) => (
              <tr 
                key={call.id} 
                onClick={() => onRowClick(call)}
                className="hover:bg-white/5 cursor-pointer transition-colors"
              >
                <td className="px-4 py-3 whitespace-nowrap">
                  {new Date(call.created_at).toLocaleString(undefined, {
                    month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'
                  })}
                </td>
                <td className="px-4 py-3 font-medium text-gray-300">
                  {call.caller_id || 'Unknown'}
                </td>
                <td className="px-4 py-3">
                  {getRiskBadge(call.risk_level)}
                </td>
                <td className="px-4 py-3">
                  <span className={`font-mono ${
                    call.composite_risk_score > 0.6 ? 'text-red-400' : call.composite_risk_score > 0.3 ? 'text-amber-400' : 'text-green-400'
                  }`}>
                    {(call.composite_risk_score * 100).toFixed(1)}
                  </span>
                </td>
                <td className="px-4 py-3 max-w-xs truncate">
                  {call.transcript || '-'}
                </td>
              </tr>
            ))}
            {calls.length === 0 && (
              <tr>
                <td colSpan={5} className="px-4 py-8 text-center text-gray-500">
                  No records found
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <div className="p-3 border-t border-white/5 flex items-center justify-between text-xs text-gray-500">
        <span>Showing {calls.length} of {total} results</span>
        <div className="flex space-x-1">
          <button 
            onClick={() => onPageChange(page - 1)}
            disabled={page === 1}
            className="p-1 rounded hover:bg-white/10 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>
          <span className="px-2 py-1 bg-navy-dark rounded text-gray-400">
            Page {page} of {totalPages || 1}
          </span>
          <button 
            onClick={() => onPageChange(page + 1)}
            disabled={page >= totalPages}
            className="p-1 rounded hover:bg-white/10 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
};

export default CallLogTable;
