import { useState } from 'react';
import { X, Upload, Search, HelpCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { createAnalysis } from '@/lib/api';

interface AnalysisData {
  type: 'loan-id' | 'external-id';
  value: string;
  notes: string;
}

interface AnalysisModalProps {
  isOpen: boolean;
  onClose: () => void;
  onAnalysisStarted: (analysisId: string) => void;
}

export default function AnalysisModal({ isOpen, onClose, onAnalysisStarted }: AnalysisModalProps) {
  const [inputType, setInputType] = useState<'loan-id' | 'external-id'>('loan-id');
  const [inputValue, setInputValue] = useState('');
  const [notes, setNotes] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputValue.trim()) return;

    setIsLoading(true);
    
    try {
      const loanData = {
        [inputType === 'loan-id' ? 'loan_id' : 'external_id']: inputValue,
        notes
      };
      
      const response = await createAnalysis(loanData);
      onAnalysisStarted(response.analysis_id);
      onClose();
      
      // Reset form
      setInputValue('');
      setNotes('');
    } catch (error) {
      console.error('Failed to start analysis:', error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700 text-gray-900 dark:text-white max-w-md p-5">
        <DialogHeader className="mb-4">
          <DialogTitle className="text-lg font-semibold">New Loan Analysis</DialogTitle>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-5">
          {/* Input Type Selection */}
          <div className="space-y-2">
            <Label className="text-sm font-medium text-gray-900 dark:text-white">Analysis Input</Label>
            <div className="grid grid-cols-2 gap-2">
              <button
                type="button"
                onClick={() => setInputType('loan-id')}
                className={`p-3 rounded-md border transition-all text-sm ${
                  inputType === 'loan-id'
                    ? 'bg-blue-600 border-blue-600 text-white'
                    : 'bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:border-blue-500 dark:hover:border-blue-400'
                }`}
              >
                <Search className="w-4 h-4 mx-auto mb-1" />
                <div className="text-xs">Loan ID</div>
              </button>
              <button
                type="button"
                onClick={() => setInputType('external-id')}
                className={`p-3 rounded-md border transition-all text-sm ${
                  inputType === 'external-id'
                    ? 'bg-blue-600 border-blue-600 text-white'
                    : 'bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:border-blue-500 dark:hover:border-blue-400'
                }`}
              >
                <Upload className="w-4 h-4 mx-auto mb-1" />
                <div className="text-xs">External ID</div>
              </button>
            </div>
          </div>

          {/* Input Field */}
          <div className="space-y-2">
            <div className="flex items-center space-x-2">
              <Label htmlFor="input-value" className="text-sm font-medium text-gray-900 dark:text-white">
                {inputType === 'loan-id' ? 'Loan ID' : 'External ID'}
              </Label>
              <div className="group relative">
                <HelpCircle className="w-4 h-4 text-gray-400 dark:text-gray-500 cursor-help" />
                <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 hidden group-hover:block">
                  <div className="bg-gray-900 dark:bg-gray-700 text-white dark:text-gray-200 text-xs rounded-md p-2 whitespace-nowrap shadow-lg">
                    {inputType === 'loan-id' 
                      ? 'Enter the internal loan identifier (e.g., LN-2024-001)'
                      : 'Enter the external system reference ID'
                    }
                  </div>
                </div>
              </div>
            </div>
            <Input
              id="input-value"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              placeholder={inputType === 'loan-id' ? 'LN-2024-001' : 'EXT-REF-12345'}
              className="bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:border-blue-500 dark:focus:border-blue-400 text-sm"
              required
            />
          </div>

          {/* Notes */}
          <div className="space-y-2">
            <Label htmlFor="notes" className="text-sm font-medium text-gray-900 dark:text-white">
              Analysis Notes (Optional)
            </Label>
            <Textarea
              id="notes"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Add any specific requirements or notes for this analysis..."
              className="bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:border-blue-500 dark:focus:border-blue-400 min-h-[80px] text-sm"
              rows={3}
            />
          </div>

          {/* Action Buttons */}
          <div className="flex space-x-3 pt-4">
            <Button
              type="button"
              onClick={onClose}
              variant="outline"
              className="flex-1 bg-transparent border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 text-sm"
            >
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={!inputValue.trim() || isLoading}
              className="flex-1 bg-blue-600 hover:bg-blue-700 text-white text-sm"
            >
              {isLoading ? (
                <div className="flex items-center space-x-2">
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                  <span>Starting...</span>
                </div>
              ) : (
                'Start Analysis'
              )}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}