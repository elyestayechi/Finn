import { useState, useEffect } from 'react';
import { TrendingUp, TrendingDown, AlertTriangle, CheckCircle } from 'lucide-react';
import { analysisApi, PDFAnalysis } from '@/lib/api';

interface RiskScoreDashboardProps {
  currentScore?: number;
  historicalData?: number[];
}

// Function to normalize scores to a 0-10 scale for visualization
const normalizeScore = (score: number, min: number = 20, max: number = 80): number => {
  return Math.max(0, Math.min(10, ((score - min) / (max - min)) * 10));
};

export default function RiskScoreDashboard({ currentScore, historicalData }: RiskScoreDashboardProps) {
  const [animatedScore, setAnimatedScore] = useState(0);
  const [analyses, setAnalyses] = useState<PDFAnalysis[]>([]);
  const [loading, setLoading] = useState(true);
  const [scoreRange, setScoreRange] = useState({ min: 20, max: 80 });

  useEffect(() => {
    fetchRecentAnalyses();
  }, []);

  const fetchRecentAnalyses = async () => {
    try {
      const data = await analysisApi.getRecentAnalyses({ limit: 6, sort_by: 'date', sort_order: 'desc' });
      // Filter out analyses with risk score of 0
      const filteredData = data.filter(item => item.risk_score > 0);
      setAnalyses(filteredData);
      
      // Calculate min and max from the data for better normalization
      if (filteredData.length > 0) {
        const scores = filteredData.map(a => a.risk_score);
        const minScore = Math.min(...scores) - 5; // Add some padding
        const maxScore = Math.max(...scores) + 5; // Add some padding
        setScoreRange({ min: Math.max(0, minScore), max: maxScore });
      }
    } catch (error) {
      console.error('Failed to fetch analyses:', error);
    } finally {
      setLoading(false);
    }
  };

  // Calculate current score and historical data from real analyses
  const calculatedCurrentScore = currentScore !== undefined ? currentScore : 
    analyses.length > 0 ? analyses[0].risk_score : 0;
  
  const calculatedHistoricalData = historicalData || 
    analyses.slice(0, 5).map(analysis => analysis.risk_score).reverse();

  // Normalize scores for visualization
  const normalizedCurrentScore = normalizeScore(calculatedCurrentScore, scoreRange.min, scoreRange.max);
  const normalizedHistoricalData = calculatedHistoricalData.map(score => 
    normalizeScore(score, scoreRange.min, scoreRange.max)
  );

  useEffect(() => {
    const timer = setTimeout(() => {
      setAnimatedScore(normalizedCurrentScore);
    }, 500);
    return () => clearTimeout(timer);
  }, [normalizedCurrentScore]);

  const getScoreColor = (score: number) => {
    // Use the original score for color determination, not normalized
    if (calculatedCurrentScore <= 35) return '#10B981'; // Low risk
    if (calculatedCurrentScore <= 55) return '#F59E0B'; // Medium risk
    return '#EF4444'; // High risk
  };

  const getScoreStatus = (score: number) => {
    // Use the original score for status determination, not normalized
    if (calculatedCurrentScore <= 35) return { label: 'Low Risk', icon: CheckCircle, color: '#10B981' };
    if (calculatedCurrentScore <= 55) return { label: 'Medium Risk', icon: AlertTriangle, color: '#F59E0B' };
    return { label: 'High Risk', icon: AlertTriangle, color: '#EF4444' };
  };

  const status = getScoreStatus(calculatedCurrentScore);
  const Icon = status.icon;
  const circumference = 2 * Math.PI * 70;
  const strokeDasharray = circumference;
  const strokeDashoffset = circumference - (animatedScore / 10) * circumference;

  if (loading) {
    return (
      <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-5 animate-pulse">
        <div className="h-6 bg-gray-300 dark:bg-gray-700 rounded mb-5"></div>
        <div className="h-40 bg-gray-300 dark:bg-gray-700 rounded mb-5"></div>
        <div className="h-16 bg-gray-300 dark:bg-gray-700 rounded"></div>
      </div>
    );
  }

  if (analyses.length === 0) {
    return (
      <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-5">
        <div className="flex items-center justify-between mb-5">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Risk Score Dashboard</h2>
        </div>
        <div className="text-center py-8 text-gray-500 dark:text-gray-400">
          No analysis data available
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-5">
      <div className="flex items-center justify-between mb-5">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Current Risk Score</h2>
        <div className="flex items-center space-x-2">
          <Icon className="w-4 h-4" style={{ color: status.color }} />
          <span className="text-xs font-medium" style={{ color: status.color }}>
            {status.label}
          </span>
        </div>
      </div>

      <div className="flex items-center justify-center mb-6">
        <div className="relative w-40 h-40">
          <svg className="w-full h-full transform -rotate-90" viewBox="0 0 200 200">
            {/* Background circle */}
            <circle
              cx="100"
              cy="100"
              r="70"
              fill="none"
              stroke="#E5E7EB"
              strokeWidth="8"
              className="dark:stroke-gray-700"
            />
            {/* Progress circle */}
            <circle
              cx="100"
              cy="100"
              r="70"
              fill="none"
              stroke={getScoreColor(calculatedCurrentScore)}
              strokeWidth="8"
              strokeDasharray={strokeDasharray}
              strokeDashoffset={strokeDashoffset}
              strokeLinecap="round"
              className="transition-all duration-1000 ease-out"
            />
          </svg>
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <div 
              className="text-3xl font-bold mb-1"
              style={{ color: getScoreColor(calculatedCurrentScore) }}
            >
              {calculatedCurrentScore.toFixed(0)}
            </div>
            <div className="text-gray-500 dark:text-gray-400 text-xs">risk score</div>
          </div>
        </div>
      </div>

      {/* Historical Comparison */}
      <div className="space-y-4">
        <h3 className="text-base font-medium text-gray-900 dark:text-white">Historical Comparison</h3>
        <div className="flex items-end justify-between h-16 space-x-2">
          {calculatedHistoricalData.map((score, index) => (
            <div key={index} className="flex-1 flex flex-col items-center">
              <div
                className="w-full rounded-t transition-all duration-500"
                style={{
                  height: `${(normalizedHistoricalData[index] / 10) * 48}px`,
                  backgroundColor: getScoreColor(score),
                  opacity: index === calculatedHistoricalData.length - 1 ? 1 : 0.6
                }}
              />
              <div className="text-xs text-gray-500 dark:text-gray-400 mt-2">{score.toFixed(0)}</div>
            </div>
          ))}
        </div>
        <div className="flex justify-between text-xs text-gray-500 dark:text-gray-400">
          <span>{calculatedHistoricalData.length > 1 ? `${calculatedHistoricalData.length} analyses ago` : 'Previous'}</span>
          <span>Current</span>
        </div>
      </div>
    </div>
  );
}