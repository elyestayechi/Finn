import { useState, useEffect } from 'react';
import { Terminal, Play, Check } from 'lucide-react';
import { useAnalysisWebSocket } from '@/hooks/useAnalysisWebSocket';

interface ProcessingPanelProps {
  analysisId: string | null;
  onCompletion: (result: any) => void;
}

export default function ProcessingPanel({ analysisId, onCompletion }: ProcessingPanelProps) {
  const { status, progress, result, error } = useAnalysisWebSocket(analysisId);
  const [logs, setLogs] = useState<string[]>([]);

  useEffect(() => {
    if (status) {
      setLogs(prev => [...prev, status]);
    }
  }, [status]);

  useEffect(() => {
    if (result) {
      onCompletion(result);
    }
  }, [result, onCompletion]);

  if (!analysisId) {
    return (
      <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-5">
        <div className="flex items-center justify-between mb-5">
          <div className="flex items-center space-x-2">
            <Terminal className="w-4 h-4 text-blue-600 dark:text-blue-400" />
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Real-Time Processing</h2>
          </div>
        </div>
        <div className="text-gray-500 dark:text-gray-400 italic text-center py-6">
          Start an analysis to see real-time processing...
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-5">
      <div className="flex items-center justify-between mb-5">
        <div className="flex items-center space-x-2">
          <Terminal className="w-4 h-4 text-blue-600 dark:text-blue-400" />
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Real-Time Processing</h2>
        </div>
        <div className="text-sm text-gray-500 dark:text-gray-400">
          {Math.round(progress)}% Complete
        </div>
      </div>

      <div className="terminal-output min-h-[160px] max-h-[240px] overflow-y-auto bg-gray-50 dark:bg-gray-900 rounded-md p-3 text-xs">
        {logs.map((log, index) => (
          <div key={index} className="flex items-center space-x-2 mb-1 animate-fade-in">
            {log.includes('complete') || log.includes('✅') ? (
              <Check className="w-3 h-3 text-green-600 dark:text-green-400 flex-shrink-0" />
            ) : (
              <div className="w-1.5 h-1.5 bg-green-500 rounded-full animate-pulse-slow flex-shrink-0 mt-1"></div>
            )}
            <span className="text-gray-700 dark:text-gray-300">{log}</span>
          </div>
        ))}
        
        {progress < 100 && !error && (
          <div className="flex items-center space-x-2 animate-pulse">
            <div className="w-1.5 h-1.5 bg-green-500 rounded-full"></div>
            <span className="text-gray-500 dark:text-gray-400">Processing...</span>
          </div>
        )}
        
        {error && (
          <div className="text-red-600 dark:text-red-400 text-sm">
            Error: {error}
          </div>
        )}
      </div>

      {progress > 0 && (
        <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
          <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-1.5">
            <div 
              className="bg-blue-600 h-1.5 rounded-full transition-all duration-300"
              style={{ width: `${progress}%` }}
            ></div>
          </div>
        </div>
      )}
    </div>
  );
}