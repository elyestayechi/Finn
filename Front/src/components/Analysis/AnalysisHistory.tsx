import { useState, useEffect, useCallback } from 'react';
import { Calendar, Filter, ChevronDown, FileText, Clock, TrendingUp, Search, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Input } from '@/components/ui/input';
import { analysisApi, PDFAnalysis } from '@/lib/api';

const getDecisionColor = (decision: string) => {
  switch (decision) {
    case 'approve': return 'text-green-700 dark:text-green-400 bg-green-100 dark:bg-green-900/30';
    case 'deny': return 'text-red-700 dark:text-red-400 bg-red-100 dark:bg-red-900/30';
    case 'review': return 'text-orange-700 dark:text-orange-400 bg-orange-100 dark:bg-orange-900/30';
    default: return 'text-gray-700 dark:text-gray-400 bg-gray-100 dark:bg-gray-900/30';
  }
};

const getRiskScoreColor = (score: number) => {
  if (score <= 3) return 'text-green-600 dark:text-green-400';
  if (score <= 7) return 'text-orange-600 dark:text-orange-400';
  return 'text-red-600 dark:text-red-400';
};

export default function AnalysisHistory() {
  const [analyses, setAnalyses] = useState<PDFAnalysis[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [expandedItem, setExpandedItem] = useState<string | null>(null);
  const [debouncedSearchTerm, setDebouncedSearchTerm] = useState('');

  // Debounce search term
  useEffect(() => {
    const timerId = setTimeout(() => {
      setDebouncedSearchTerm(searchTerm);
    }, 500);

    return () => {
      clearTimeout(timerId);
    };
  }, [searchTerm]);

  // Fetch recent analyses on component mount
  useEffect(() => {
    fetchAnalyses();
  }, []);

  // Fetch analyses when filters change
  useEffect(() => {
    fetchAnalyses();
  }, [filter, debouncedSearchTerm]);

  const fetchAnalyses = useCallback(async () => {
    setLoading(true);
    try {
      const filters: any = { limit: 50, sort_by: 'date', sort_order: 'desc' };
      if (filter !== 'all') filters.decision = filter;
      if (debouncedSearchTerm) filters.customer_name = debouncedSearchTerm;
      
      const data = await analysisApi.getRecentAnalyses(filters);
      // Filter out analyses with risk score of 0 and sort by customer name
      const filteredData = data
        .filter(item => item.risk_score > 0)
        .sort((a, b) => a.customer_name.localeCompare(b.customer_name));
      
      setAnalyses(filteredData);
    } catch (error) {
      console.error('Failed to fetch analyses:', error);
    } finally {
      setLoading(false);
    }
  }, [filter, debouncedSearchTerm]);

  const clearFilters = () => {
    setFilter('all');
    setSearchTerm('');
    setDebouncedSearchTerm('');
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  if (loading) {
    return (
      <div className="space-y-5">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white">Analysis History</h2>
        </div>
        <div className="flex items-center justify-center h-48">
          <div className="text-gray-500 dark:text-gray-400">Loading analyses...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-5">
      {/* Filters */}
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white">Analysis History</h2>
        <div className="flex items-center space-x-3">
          <Select value={filter} onValueChange={setFilter}>
            <SelectTrigger className="w-40 bg-white dark:bg-gray-800 border-gray-300 dark:border-gray-700 text-gray-900 dark:text-white text-sm">
              <Filter className="w-4 h-4 mr-2" />
              <SelectValue />
            </SelectTrigger>
            <SelectContent className="bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700 text-gray-900 dark:text-white">
              <SelectItem value="all">All Decisions</SelectItem>
              <SelectItem value="approve">Approved</SelectItem>
              <SelectItem value="deny">Rejected</SelectItem>
              <SelectItem value="review">Under Review</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* Search Filter */}
      <div className="grid grid-cols-1 md:grid-cols- gap-3">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w- h-4" />
          <Input
            placeholder="Search customer..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-10 bg-white dark:bg-gray-800 border-gray-300 dark:border-gray-700 text-gray-900 dark:text-white text-sm"
          />
        </div>
        
      </div>

      {/* Timeline */}
      <div className="relative">
        {/* Timeline line */}
        <div className="absolute left-5 top-0 bottom-0 w-0.5 bg-gray-200 dark:bg-gray-700"></div>

        <div className="space-y-4">
          {analyses.map((item, index) => (
            <div key={item.id} className="relative animate-fade-in" style={{ animationDelay: `${index * 100}ms` }}>
              {/* Timeline dot */}
              <div className={`absolute left-3 w-3 h-3 rounded-full border-2 border-white dark:border-gray-900 ${
                item.decision === 'approve' ? 'bg-green-500' :
                item.decision === 'deny' ? 'bg-red-500' : 'bg-orange-500'
              }`}></div>

              {/* Content card */}
              <div className="ml-8 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-5">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center space-x-3">
                    <div className="flex items-center space-x-2">
                      <FileText className="w-4 h-4 text-blue-600 dark:text-blue-400" />
                      <div>
                        <h3 className="font-semibold text-gray-900 dark:text-white text-sm">{item.customer_name}</h3>
                        <p className="text-xs text-gray-500 dark:text-gray-400">Loan ID: {item.loan_id}</p>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2 text-xs text-gray-500 dark:text-gray-400">
                      <Calendar className="w-3 h-3" />
                      <span>{item.date} at {item.time}</span>
                    </div>
                  </div>
                  
                  <button
                    onClick={() => setExpandedItem(expandedItem === item.id ? null : item.id)}
                    className="p-1.5 hover:bg-gray-100 dark:hover:bg-gray-700 rounded transition-colors"
                  >
                    <ChevronDown 
                      className={`w-4 h-4 text-gray-500 dark:text-gray-400 transition-transform ${
                        expandedItem === item.id ? 'rotate-180' : ''
                      }`} 
                    />
                  </button>
                </div>

                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                  <div>
                    <div className="text-gray-500 dark:text-gray-400 text-xs mb-1">Risk Score</div>
                    <div className={`text-lg font-bold ${getRiskScoreColor(item.risk_score)}`}>
                      {item.risk_score.toFixed(1)}
                    </div>
                  </div>
                  <div>
                    <div className="text-gray-500 dark:text-gray-400 text-xs mb-1">Decision</div>
                    <div className={`inline-block px-2 py-1 rounded-full text-xs font-medium capitalize ${getDecisionColor(item.decision)}`}>
                      {item.decision}
                    </div>
                  </div>
                  <div>
                    <div className="text-gray-500 dark:text-gray-400 text-xs mb-1">Confidence</div>
                    <div className="text-gray-900 dark:text-white font-semibold">{item.confidence}%</div>
                  </div>
                  <div>
                    <div className="text-gray-500 dark:text-gray-400 text-xs mb-1">Processing</div>
                    <div className="flex items-center space-x-1 text-gray-900 dark:text-white">
                      <Clock className="w-3 h-3" />
                      <span className="text-xs">{item.processing_time}</span>
                    </div>
                  </div>
                </div>

                {expandedItem === item.id && (
                  <div className="border-t border-gray-200 dark:border-gray-700 pt-4 animate-fade-in">
                    <h4 className="text-gray-900 dark:text-white font-medium mb-3 text-sm">Key Findings</h4>
                    <div className="space-y-2">
                      {item.key_findings.length > 0 ? (
                        item.key_findings.map((finding, findingIndex) => (
                          <div key={findingIndex} className="flex items-start space-x-2">
                            <TrendingUp className="w-4 h-4 text-blue-600 dark:text-blue-400 mt-0.5 flex-shrink-0" />
                            <span className="text-gray-600 dark:text-gray-300 text-sm">{finding}</span>
                          </div>
                        ))
                      ) : (
                        <div className="text-gray-500 dark:text-gray-400 text-sm">
                          No key findings available
                        </div>
                      )}
                    </div>
                    <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
                      <div className="text-xs text-gray-500 dark:text-gray-400">
                        File: {item.file_name} • Size: {formatFileSize(item.file_size)}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      {analyses.length === 0 && (
        <div className="text-center py-12 text-gray-500 dark:text-gray-400">
          <FileText className="w-12 h-12 mx-auto mb-4 opacity-50" />
          <p>No analyses found matching your criteria</p>
          <Button
            onClick={clearFilters}
            variant="ghost"
            className="mt-4 text-blue-600 dark:text-blue-400"
          >
            Clear all filters
          </Button>
        </div>
      )}
    </div>
  );
}