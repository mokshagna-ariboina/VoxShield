import React from 'react';
import { SignalBreakdown, MatchedPattern } from '../api/types';
import { AlertTriangle, Tag } from 'lucide-react';

interface SignalBreakdownProps {
  breakdown: SignalBreakdown;
  matchedPatterns?: MatchedPattern[];
}

const SignalBreakdownChart: React.FC<SignalBreakdownProps> = ({ breakdown, matchedPatterns = [] }) => {
  const signalConfigs = [
    { key: 'clone_probability', label: 'AI Voice Clone', color: 'bg-red-500' },
    { key: 'social_engineering_score', label: 'Social Engineering', color: 'bg-orange-500' },
    { key: 'speaker_mismatch_score', label: 'Speaker Mismatch', color: 'bg-purple-500' },
    { key: 'trust_novelty_score', label: 'Trust Novelty', color: 'bg-blue-500' },
    { key: 'transaction_risk_score', label: 'Transaction Risk', color: 'bg-yellow-500' },
  ];

  return (
    <div className="space-y-6">
      <div className="space-y-4">
        <h3 className="text-sm font-semibold text-gray-300 uppercase tracking-wider mb-4">Signal Contributions</h3>
        {signalConfigs.map(({ key, label, color }) => {
          const value = breakdown[key] || 0;
          const percentage = Math.round(value * 100);
          const isHigh = value > 0.5;
          return (
            <div key={key} className="space-y-1">
              <div className="flex justify-between text-xs">
                <span className={`font-medium ${isHigh ? 'text-white' : 'text-gray-400'}`}>{label}</span>
                <span className="text-gray-400">{percentage}%</span>
              </div>
              <div className="h-2 bg-navy-dark rounded-full overflow-hidden">
                <div 
                  className={`h-full ${color} transition-all duration-1000 ease-out`}
                  style={{ width: `${percentage}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>

      {matchedPatterns.length > 0 && (
        <div className="pt-4 border-t border-white/10">
          <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wider flex items-center mb-3">
            <AlertTriangle className="w-3 h-3 mr-2" />
            Detected Patterns
          </h4>
          <div className="flex flex-wrap gap-2">
            {matchedPatterns.map((pattern, idx) => (
              <div 
                key={idx}
                className="flex items-center px-2 py-1 rounded bg-navy-light border border-white/5 text-xs text-gray-300"
                title={`Weight: ${pattern.weight.toFixed(2)}`}
              >
                <Tag className="w-3 h-3 mr-1 text-electric-blue" />
                {pattern.category}: {pattern.phrase}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default SignalBreakdownChart;
