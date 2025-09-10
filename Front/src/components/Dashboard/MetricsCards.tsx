import { useState, useEffect } from 'react';
import { TrendingUp, CheckCircle, AlertTriangle, BarChart } from 'lucide-react';
import { analysisApi, PDFAnalysis } from '@/lib/api';

interface Metric {
  title: string;
  value: string;
  change: string;
  changeType: 'positive' | 'negative';
  icon: any;
  color: string;
}

interface MetricsData {
  totalAnalyses: number;
  approvalRate: number;
  avgRiskScore: number;
  avgProcessingTime: number;
  previousMetrics?: {
    totalAnalyses: number;
    approvalRate: number;
    avgRiskScore: number;
    avgProcessingTime: number;
  };
}

const colorMap: Record<string, string> = {
  blue: 'from-blue-600 to-blue-700',
  green: 'from-green-500 to-green-600',
  orange: 'from-orange-500 to-orange-600',
  purple: 'from-purple-600 to-purple-700'
};

export default function MetricsCards() {
  const [metrics, setMetrics] = useState<MetricsData>({
    totalAnalyses: 0,
    approvalRate: 0,
    avgRiskScore: 0,
    avgProcessingTime: 0
  });
  const [previousMetrics, setPreviousMetrics] = useState<MetricsData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        // Get current period data (last 30 days)
        const currentAnalyses = await analysisApi.getRecentAnalyses({ limit: 1000 });
        
        // Get previous period data (30-60 days ago)
        const allAnalyses = await analysisApi.getRecentAnalyses({ limit: 2000 });
        const previousPeriodAnalyses = allAnalyses.slice(100);
        
        const currentMetrics = calculateMetrics(currentAnalyses);
        const prevMetrics = calculateMetrics(previousPeriodAnalyses);
        
        setMetrics(currentMetrics);
        setPreviousMetrics(prevMetrics);
      } catch (error) {
        console.error('Failed to fetch metrics:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchMetrics();
  }, []);

  const calculateMetrics = (analyses: PDFAnalysis[]): MetricsData => {
    const approved = analyses.filter(a => a.decision === 'approve').length;
    
    // Filter out analyses with invalid processing times
    const validProcessingAnalyses = analyses.filter(a => {
      if (a.processing_time === 'N/A' || !a.processing_time) return false;
      
      const timeStr = a.processing_time;
      if (timeStr.includes('min')) {
        const minutes = parseFloat(timeStr.replace('min', ''));
        return !isNaN(minutes) && minutes > 0;
      }
      return false;
    });

    const totalProcessingTimes = validProcessingAnalyses.map(a => {
      const timeStr = a.processing_time;
      return parseFloat(timeStr.replace('min', ''));
    });
    
    const avgProcessingTime = totalProcessingTimes.length > 0 
      ? totalProcessingTimes.reduce((a, b) => a + b, 0) / totalProcessingTimes.length
      : 0;
    
    return {
      totalAnalyses: analyses.length,
      approvalRate: analyses.length > 0 ? (approved / analyses.length) * 100 : 0,
      avgRiskScore: analyses.length > 0 
        ? analyses.reduce((sum, a) => sum + a.risk_score, 0) / analyses.length
        : 0,
      avgProcessingTime
    };
  };

  const calculateChange = (current: number, previous: number): { value: string, type: 'positive' | 'negative' } => {
    if (previous === 0) return { value: '+0%', type: 'positive' };
    
    const change = ((current - previous) / previous) * 100;
    const absChange = Math.abs(change);
    
    return {
      value: `${change >= 0 ? '+' : '-'}${absChange.toFixed(1)}%`,
      type: change >= 0 ? 'positive' : 'negative'
    };
  };

  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="bg-white dark:bg-gray-800 rounded-lg p-5 animate-pulse">
            <div className="h-6 bg-gray-300 dark:bg-gray-700 rounded mb-4"></div>
            <div className="h-8 bg-gray-300 dark:bg-gray-700 rounded"></div>
          </div>
        ))}
      </div>
    );
  }

  // Calculate changes based on previous period
  const totalChange = previousMetrics ? 
    calculateChange(metrics.totalAnalyses, previousMetrics.totalAnalyses) : 
    { value: '+0%', type: 'positive' as const };
  
  const approvalChange = previousMetrics ? 
    calculateChange(metrics.approvalRate, previousMetrics.approvalRate) : 
    { value: '+0%', type: 'positive' as const };
  
  const riskChange = previousMetrics ? 
    calculateChange(metrics.avgRiskScore, previousMetrics.avgRiskScore) : 
    { value: '+0%', type: 'positive' as const };
  
  // For processing time, lower is better so we invert the logic
  const processingChange = previousMetrics ? {
    value: metrics.avgProcessingTime <= previousMetrics.avgProcessingTime ? 
      `-${((previousMetrics.avgProcessingTime - metrics.avgProcessingTime) / previousMetrics.avgProcessingTime * 100).toFixed(1)}%` : 
      `+${((metrics.avgProcessingTime - previousMetrics.avgProcessingTime) / previousMetrics.avgProcessingTime * 100).toFixed(1)}%`,
    type: metrics.avgProcessingTime <= previousMetrics.avgProcessingTime ? 'positive' as const : 'negative' as const
  } : { value: '+0%', type: 'positive' as const };

  const metricsData: Metric[] = [
    {
      title: 'Total Analyses',
      value: metrics.totalAnalyses.toLocaleString(),
      change: totalChange.value,
      changeType: totalChange.type,
      icon: BarChart,
      color: 'blue'
    },
    {
      title: 'Approval Rate',
      value: `${metrics.approvalRate.toFixed(1)}%`,
      change: approvalChange.value,
      changeType: approvalChange.type,
      icon: CheckCircle,
      color: 'green'
    },
    {
      title: 'Avg Risk Score',
      value: metrics.avgRiskScore.toFixed(1),
      change: riskChange.value,
      changeType: riskChange.type,
      icon: AlertTriangle,
      color: 'orange'
    },
    {
      title: 'Avg Processing Time',
      value: `${metrics.avgProcessingTime.toFixed(1)}min`,
      change: processingChange.value,
      changeType: processingChange.type,
      icon: TrendingUp,
      color: 'purple'
    }
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      {metricsData.map((metric, index) => {
        const Icon = metric.icon;
        return (
          <div
            key={metric.title}
            className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-5 hover:shadow-md transition-all duration-300 animate-fade-in"
            style={{ animationDelay: `${index * 100}ms` }}
          >
            <div className="flex items-center justify-between mb-4">
              <div className={`w-10 h-10 bg-gradient-to-br ${colorMap[metric.color]} rounded-lg flex items-center justify-center`}>
                <Icon className="w-5 h-5 text-white" />
              </div>
              <div className={`text-xs font-medium ${
                metric.changeType === 'positive' ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'
              }`}>
                {metric.change}
              </div>
            </div>
            <div>
              <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-1">{metric.value}</h3>
              <p className="text-gray-500 dark:text-gray-400 text-sm">{metric.title}</p>
            </div>
          </div>
        );
      })}
    </div>
  );
}