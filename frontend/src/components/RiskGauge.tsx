import React from 'react';

interface RiskGaugeProps {
  score: number; // 0.0 to 1.0
  riskLevel: string;
  size?: number;
}

const RiskGauge: React.FC<RiskGaugeProps> = ({ score, riskLevel, size = 200 }) => {
  const normalizedScore = Math.min(Math.max(score, 0), 1);
  const percentage = Math.round(normalizedScore * 100);
  
  const strokeWidth = size * 0.1;
  const radius = (size - strokeWidth) / 2;
  const circumference = radius * 2 * Math.PI;
  // Arc represents 75% of a circle
  const arcLength = circumference * 0.75;
  const strokeDashoffset = arcLength - (normalizedScore * arcLength);

  let color = '#22c55e'; // Green
  let glowColor = 'rgba(34, 197, 94, 0.5)';
  if (normalizedScore > 0.6) {
    color = '#ef4444'; // Red
    glowColor = 'rgba(239, 68, 68, 0.5)';
  } else if (normalizedScore > 0.3) {
    color = '#f59e0b'; // Amber
    glowColor = 'rgba(245, 158, 11, 0.5)';
  }

  return (
    <div className="relative flex flex-col items-center justify-center" style={{ width: size, height: size }}>
      <svg
        width={size}
        height={size}
        viewBox={`0 0 ${size} ${size}`}
        className="transform rotate-135"
        style={{ transform: 'rotate(135deg)' }}
      >
        {/* Background track */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="transparent"
          stroke="#1f2937"
          strokeWidth={strokeWidth}
          strokeDasharray={`${arcLength} ${circumference}`}
          strokeLinecap="round"
        />
        {/* Value arc */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="transparent"
          stroke={color}
          strokeWidth={strokeWidth}
          strokeDasharray={`${arcLength} ${circumference}`}
          strokeDashoffset={strokeDashoffset}
          strokeLinecap="round"
          className="gauge-fill"
          style={{ filter: `drop-shadow(0 0 8px ${glowColor})` }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center pt-4">
        <span className="text-4xl font-bold text-white tracking-tighter">{percentage}</span>
        <span 
          className="text-xs uppercase font-bold tracking-widest mt-1"
          style={{ color }}
        >
          {riskLevel}
        </span>
      </div>
    </div>
  );
};

export default RiskGauge;
