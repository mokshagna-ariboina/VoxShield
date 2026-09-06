import React from 'react';
import { TimelineEvent } from '../api/types';
import { Activity, Cpu, FileText, AlertTriangle, Calculator, ShieldQuestion, ShieldCheck, ShieldAlert, Circle } from 'lucide-react';

interface RiskTimelineProps {
  events: TimelineEvent[];
}

const RiskTimeline: React.FC<RiskTimelineProps> = ({ events }) => {
  const getIcon = (type: string, status: string) => {
    if (status === 'failed') return <ShieldAlert className="w-4 h-4 text-red-500" />;
    
    switch (type.toLowerCase()) {
      case 'audio_received': return <Activity className="w-4 h-4 text-blue-400" />;
      case 'aasist_analysis': return <Cpu className="w-4 h-4 text-purple-400" />;
      case 'transcript_generated': return <FileText className="w-4 h-4 text-gray-400" />;
      case 'patterns_detected': return <AlertTriangle className="w-4 h-4 text-amber-400" />;
      case 'risk_computed': return <Calculator className="w-4 h-4 text-green-400" />;
      case 'challenge_issued': return <ShieldQuestion className="w-4 h-4 text-amber-500" />;
      case 'challenge_verified': return <ShieldCheck className="w-4 h-4 text-green-500" />;
      case 'escalated': return <ShieldAlert className="w-4 h-4 text-red-500" />;
      default: return <Circle className="w-4 h-4 text-gray-500" />;
    }
  };

  return (
    <div className="relative pl-6 border-l border-white/10 space-y-6">
      {events.map((event, idx) => (
        <div key={idx} className="relative">
          <div className="absolute -left-[35px] bg-navy p-1 rounded-full border border-white/10">
            {getIcon(event.event_type, event.status)}
          </div>
          <div className="flex flex-col">
            <div className="flex items-center space-x-2">
              <span className="text-sm font-medium text-gray-200 capitalize">
                {event.event_type.replace(/_/g, ' ')}
              </span>
              <span className={`text-[10px] px-1.5 py-0.5 rounded uppercase font-bold tracking-wider ${
                event.status === 'complete' ? 'bg-green-500/20 text-green-400' :
                event.status === 'failed' ? 'bg-red-500/20 text-red-400' :
                'bg-gray-500/20 text-gray-400'
              }`}>
                {event.status}
              </span>
            </div>
            <p className="text-xs text-gray-400 mt-1">{event.description}</p>
            <span className="text-[10px] text-gray-500 mt-1 font-mono">
              {new Date(event.timestamp).toLocaleTimeString()}
            </span>
          </div>
        </div>
      ))}
      {events.length === 0 && (
        <p className="text-sm text-gray-500">No events recorded yet.</p>
      )}
    </div>
  );
};

export default RiskTimeline;
