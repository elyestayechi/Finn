import { toast } from '@/hooks/use-toast';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export interface PDFReport {
  id: number;
  loan_id: string;
  file_name: string;
  file_path: string;
  file_size?: number;
  generated_at: string;
}

export interface Feedback {
  id: number;
  loan_id: string;
  agent_recommendation: string;
  human_decision: string;
  rating: number;
  comments?: string;
  created_at: string;
}

export interface AnalysisData {
  summary: string;
  recommendation: string;
  key_findings: string[];
  conditions: string[];
}

export interface PDFAnalysis {
  id: string;
  loan_id: string;
  file_name: string;
  customer_name: string;
  risk_score: number;
  decision: string;
  key_findings: string[];
  processing_time: string;
  confidence: number;
  date: string;
  time: string;
  file_size: number;
  generated_at: string;
}

export interface AnalysisFilters {
  decision?: string;
  customer_name?: string;
  start_date?: string;
  end_date?: string;
  skip?: number;
  limit?: number;
  sort_by?: string; 
  sort_order?: string; 
}

export interface Rule {
  Category: string;
  Item: string;
  Weight: string;
}

// Analysis API
export const analysisApi = {
  getAnalysis: async (loanId: string): Promise<AnalysisData> => {
    const response = await fetch(`${API_BASE_URL}/api/analysis/${loanId}`);
    if (!response.ok) {
      if (response.status === 404) {
        throw new Error('Analysis not found for this loan ID. Please check if the PDF exists.');
      }
      throw new Error('Failed to fetch analysis');
    }
    return response.json();
  },

  getRecentAnalyses: async (filters: AnalysisFilters = {}): Promise<PDFAnalysis[]> => {
    const params = new URLSearchParams();
    
    if (filters.decision) params.append('decision', filters.decision);
    if (filters.customer_name) params.append('customer_name', filters.customer_name);
    if (filters.start_date) params.append('start_date', filters.start_date);
    if (filters.end_date) params.append('end_date', filters.end_date);
    if (filters?.skip) params.append('skip', filters.skip.toString());
    if (filters.limit) params.append('limit', filters.limit.toString());
    
    const response = await fetch(`${API_BASE_URL}/api/analyses/recent?${params}`);
    if (!response.ok) {
      throw new Error('Failed to fetch analyses');
    }
    return response.json();
  },

  createAnalysis: async (loanData: { loan_id?: string; external_id?: string; notes?: string }): Promise<{ analysis_id: string }> => {
    const response = await fetch(`${API_BASE_URL}/api/analyses`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(loanData),
    });

    if (!response.ok) throw new Error('Failed to create analysis');
    
    return response.json();
  }
};

// PDF Reports API
export const pdfApi = {
  getAll: async (): Promise<PDFReport[]> => {
    const response = await fetch(`${API_BASE_URL}/pdf-reports/`);
    if (!response.ok) throw new Error('Failed to fetch PDF reports');
    return response.json();
  },

  getByLoanId: async (loanId: string): Promise<PDFReport> => {
    const response = await fetch(`${API_BASE_URL}/pdf-reports/loan/${loanId}`);
    if (!response.ok) throw new Error('PDF report not found');
    return response.json();
  }
};

// Feedback API - UPDATED FOR JSON RESPONSE
export const feedbackApi = {
  getAll: async (): Promise<any[]> => {
    const response = await fetch(`${API_BASE_URL}/feedback/`);
    if (!response.ok) throw new Error('Failed to fetch feedback');
    return response.json();
  },

  getByLoanId: async (loanId: string): Promise<any[]> => {
    const response = await fetch(`${API_BASE_URL}/feedback/loan/${loanId}`);
    if (!response.ok) throw new Error('Feedback not found');
    return response.json();
  },

  create: async (feedback: any): Promise<any> => {
    const response = await fetch(`${API_BASE_URL}/feedback/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(feedback),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || 'Failed to submit feedback');
    }
    
    const result = await response.json();
    
    toast({
      title: 'Feedback submitted',
      description: 'Thank you for your feedback!',
    });
    
    return result;
  }
};

// Utility to get PDF URL
export const getPDFUrl = (fileName: string): string => {
  return `${API_BASE_URL}/pdfs/${fileName}`;
};

export const rulesApi = {
  getAll: async (): Promise<Rule[]> => {
    const response = await fetch(`${API_BASE_URL}/api/rules`);
    if (!response.ok) {
      throw new Error('Failed to fetch rules');
    }
    return response.json();
  },

  update: async (rules: Rule[]): Promise<{ message: string }> => {
    const response = await fetch(`${API_BASE_URL}/api/rules`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(rules),
    });

    if (!response.ok) {
      throw new Error('Failed to update rules');
    }
    return response.json();
  },

  reset: async (): Promise<{ message: string }> => {
    const response = await fetch(`${API_BASE_URL}/api/rules/reset`, {
      method: 'POST',
    });

    if (!response.ok) {
      throw new Error('Failed to reset rules');
    }
    return response.json();
  }
};

// Export the createAnalysis function directly for backward compatibility
export const createAnalysis = analysisApi.createAnalysis;