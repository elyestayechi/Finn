import { useState, useEffect, useCallback } from 'react';
import { toast } from '@/hooks/use-toast';

interface WebSocketMessage {
  type: 'status' | 'progress' | 'result' | 'error';
  message?: string;
  progress?: number;
  data?: any;
}

export const useAnalysisWebSocket = (analysisId: string | null) => {
  const [socket, setSocket] = useState<WebSocket | null>(null);
  const [status, setStatus] = useState<string>('');
  const [progress, setProgress] = useState<number>(0);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!analysisId) return;

    const ws = new WebSocket(`ws://localhost:8000/ws/analysis/${analysisId}`);
    
    ws.onopen = () => {
      console.log('WebSocket connected');
      setSocket(ws);
    };

    ws.onmessage = (event) => {
      const message: WebSocketMessage = JSON.parse(event.data);
      
      switch (message.type) {
        case 'status':
          setStatus(message.message || '');
          break;
        case 'progress':
          setStatus(message.message || '');
          setProgress(message.progress || 0);
          break;
        case 'result':
          setResult(message.data);
          setProgress(100);
          toast({
            title: 'Analysis complete',
            description: 'Your loan analysis has been processed successfully.',
          });
          break;
        case 'error':
          setError(message.message || 'An error occurred');
          toast({
            title: 'Analysis failed',
            description: message.message || 'An error occurred during processing.',
            variant: 'destructive',
          });
          break;
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      setError('Connection error');
    };

    ws.onclose = () => {
      console.log('WebSocket disconnected');
      setSocket(null);
    };

    return () => {
      ws.close();
    };
  }, [analysisId]);

  return { socket, status, progress, result, error };
};