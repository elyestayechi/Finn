import { useState, useEffect } from 'react';
import { Star, ThumbsUp, MessageSquare, Send, Download, FileText, AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { cn } from '@/lib/utils';
import { feedbackApi, analysisApi } from '@/lib/api';

interface AnalysisData {
  summary: string;
  recommendation: string;
  key_findings: string[];
  conditions: string[];
}

export default function FeedbackSystem() {
  const [loanId, setLoanId] = useState('');
  const [analysis, setAnalysis] = useState<AnalysisData | null>(null);
  const [rating, setRating] = useState(0);
  const [humanDecision, setHumanDecision] = useState('review');
  const [comment, setComment] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchAnalysis = async () => {
    if (!loanId.trim()) return;
    
    setLoading(true);
    setError(null);
    setAnalysis(null);
    
    try {
      const data = await analysisApi.getAnalysis(loanId);
      setAnalysis(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch analysis. Please check the loan ID and ensure the PDF exists.');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async () => {
    if (rating === 0 || !analysis) return;
    
    setIsSubmitting(true);
    setError(null);
    
    try {
      await feedbackApi.create({
        loan_id: loanId,
        agent_recommendation: analysis.recommendation,
        human_decision: humanDecision,
        rating,
        comments: comment
      });
      setSubmitted(true);
    } catch (err) {
      setError('Failed to submit feedback. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const resetForm = () => {
    setLoanId('');
    setAnalysis(null);
    setRating(0);
    setHumanDecision('review');
    setComment('');
    setSubmitted(false);
    setError(null);
  };

  const getRecommendationColor = (recommendation: string) => {
    switch (recommendation) {
      case 'approve': return 'text-green-700 dark:text-green-400 bg-green-100 dark:bg-green-900/30';
      case 'reject': return 'text-red-700 dark:text-red-400 bg-red-100 dark:bg-red-900/30';
      case 'review': return 'text-orange-700 dark:text-orange-400 bg-orange-100 dark:bg-orange-900/30';
      default: return 'text-gray-700 dark:text-gray-400 bg-gray-100 dark:bg-gray-900/30';
    }
  };

  if (submitted) {
    return (
      <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6 text-center">
        <div className="w-14 h-14 bg-green-500 rounded-full flex items-center justify-center mx-auto mb-4">
          <ThumbsUp className="w-6 h-6 text-white" />
        </div>
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">Feedback Submitted</h2>
        <p className="text-gray-500 dark:text-gray-400 mb-5">Thank you for helping improve our AI model</p>
        <div className="flex space-x-3 justify-center">
          <Button onClick={resetForm} className="bg-blue-600 hover:bg-blue-700 text-white text-sm">
            Submit Another
          </Button>
          <Button 
            onClick={() => window.open(`/pdfs/loan_assessment_${loanId}_*.pdf`, '_blank')}
            className="bg-transparent border border-blue-600 text-blue-600 hover:bg-blue-600 hover:text-white flex items-center space-x-2 text-sm"
          >
            <Download className="w-4 h-4" />
            <span>Download PDF</span>
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-5">
      <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-5">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-5">Loan Analysis Feedback System</h2>
        
        <div className="space-y-4">
          <div>
            <Label htmlFor="loanId" className="text-sm font-medium text-gray-900 dark:text-white mb-2 block">
              Enter Loan ID
            </Label>
            <div className="flex space-x-2">
              <Input
                id="loanId"
                value={loanId}
                onChange={(e) => setLoanId(e.target.value)}
                placeholder="e.g., 32383"
                className="bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600 text-gray-900 dark:text-white flex-1 text-sm"
                onKeyPress={(e) => e.key === 'Enter' && fetchAnalysis()}
              />
              <Button 
                onClick={fetchAnalysis}
                disabled={!loanId.trim() || loading}
                className="bg-blue-600 hover:bg-blue-700 text-white text-sm"
              >
                {loading ? (
                  <div className="flex items-center space-x-2">
                    <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                    <span>Loading...</span>
                  </div>
                ) : (
                  'Fetch Analysis'
                )}
              </Button>
            </div>
          </div>

          {error && (
            <div className="text-red-600 dark:text-red-400 text-sm p-3 bg-red-100 dark:bg-red-900/30 rounded-md flex items-center space-x-2">
              <AlertCircle className="w-4 h-4" />
              <span>{error}</span>
            </div>
          )}
        </div>
      </div>

      {analysis && (
        <>
          {/* Analysis Display */}
          <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-5">
            <h3 className="text-base font-semibold text-gray-900 dark:text-white mb-4 flex items-center space-x-2">
              <FileText className="w-4 h-4 text-blue-600 dark:text-blue-400" />
              <span>AI Analysis Summary</span>
            </h3>

            <div className="space-y-5">
              {/* Summary */}
              <div>
                <h4 className="text-gray-500 dark:text-gray-400 text-xs font-medium mb-2">Summary</h4>
                <p className="text-gray-900 dark:text-white text-sm leading-relaxed whitespace-pre-wrap">{analysis.summary}</p>
              </div>

              {/* Recommendation */}
              <div>
                <h4 className="text-gray-500 dark:text-gray-400 text-xs font-medium mb-2">Recommendation</h4>
                <div className={`inline-block px-2.5 py-1 rounded-full text-xs font-medium capitalize ${getRecommendationColor(analysis.recommendation)}`}>
                  {analysis.recommendation.toUpperCase()}
                </div>
              </div>

              {/* Key Findings */}
              {analysis.key_findings && analysis.key_findings.length > 0 && (
                <div>
                  <h4 className="text-gray-500 dark:text-gray-400 text-xs font-medium mb-2">Key Findings</h4>
                  <ul className="space-y-2">
                    {analysis.key_findings.map((finding, index) => (
                      <li key={index} className="text-gray-900 dark:text-white text-sm flex items-start space-x-2">
                        <span className="text-gray-500 dark:text-gray-400 mt-1">-</span>
                        <span className="leading-relaxed">{finding}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Conditions */}
              {analysis.conditions && analysis.conditions.length > 0 && (
                <div>
                  <h4 className="text-gray-500 dark:text-gray-400 text-xs font-medium mb-2">Conditions</h4>
                  <ul className="space-y-2">
                    {analysis.conditions.map((condition, index) => (
                      <li key={index} className="text-gray-900 dark:text-white text-sm flex items-start space-x-2">
                        <span className="text-gray-500 dark:text-gray-400 mt-1">-</span>
                        <span className="leading-relaxed">{condition}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>

          {/* Feedback Form */}
          <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-5">
            <h3 className="text-base font-semibold text-gray-900 dark:text-white mb-5 flex items-center space-x-2">
              <MessageSquare className="w-4 h-4 text-blue-600 dark:text-blue-400" />
              <span>Provide Feedback</span>
            </h3>

            <div className="space-y-5">
              {/* Decision Selection */}
              <div>
                <Label className="text-sm font-medium text-gray-900 dark:text-white mb-2 block">
                  What was the final decision?
                </Label>
                <Select value={humanDecision} onValueChange={setHumanDecision}>
                  <SelectTrigger className="bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600 text-gray-900 dark:text-white text-sm">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent className="bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700 text-gray-900 dark:text-white">
                    <SelectItem value="approve">Approve</SelectItem>
                    <SelectItem value="reject">Reject</SelectItem>
                    <SelectItem value="review">Review</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              {/* Rating */}
              <div>
                <Label className="text-sm font-medium text-gray-900 dark:text-white mb-2 block">
                  Rate the AI's analysis (1-5)
                </Label>
                <div className="flex items-center space-x-2">
                  {[1, 2, 3, 4, 5].map((star) => (
                    <button
                      key={star}
                      onClick={() => setRating(star)}
                      className="transition-all duration-200 hover:scale-110"
                    >
                      <Star
                        className={cn(
                          "w-6 h-6",
                          rating >= star
                            ? "fill-amber-500 text-amber-500"
                            : "text-gray-300 dark:text-gray-600"
                        )}
                      />
                    </button>
                  ))}
                  <span className="ml-4 text-gray-500 dark:text-gray-400 text-sm">
                    {rating === 0 ? 'No rating' : `${rating} star${rating !== 1 ? 's' : ''}`}
                  </span>
                </div>
              </div>

              {/* Comments */}
              <div>
                <Label htmlFor="comments" className="text-sm font-medium text-gray-900 dark:text-white mb-2 block">
                  Provide detailed feedback (what was good/bad, what to improve)
                </Label>
                <Textarea
                  id="comments"
                  value={comment}
                  onChange={(e) => setComment(e.target.value)}
                  placeholder="Share your thoughts on the AI's performance, any specific concerns, or suggestions for improvement..."
                  className="bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:border-blue-500 dark:focus:border-blue-400 min-h-[100px] text-sm"
                  rows={4}
                />
              </div>

              {/* Submit Button */}
              <Button
                onClick={handleSubmit}
                disabled={rating === 0 || isSubmitting}
                className="bg-blue-600 hover:bg-blue-700 text-white w-full flex items-center justify-center space-x-2 text-sm"
              >
                {isSubmitting ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                    <span>Submitting...</span>
                  </>
                ) : (
                  <>
                    <Send className="w-4 h-4" />
                    <span>Submit Feedback</span>
                  </>
                )}
              </Button>
            </div>
          </div>
        </>
      )}
    </div>
  );
}