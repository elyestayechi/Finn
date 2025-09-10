import { useState, useEffect } from 'react';
import { X, Download, ExternalLink } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';

interface PDFPreviewProps {
  isOpen: boolean;
  onClose: () => void;
  documentTitle: string;
  pdfUrl: string;
}

export default function PDFPreview({ isOpen, onClose, documentTitle, pdfUrl }: PDFPreviewProps) {
  const [iframeLoaded, setIframeLoaded] = useState(false);

  const downloadPDF = () => {
    if (pdfUrl) {
      const link = document.createElement('a');
      link.href = pdfUrl;
      link.download = documentTitle || 'document.pdf';
      link.click();
    }
  };

  const openInNewTab = () => {
    window.open(pdfUrl, '_blank');
  };

  useEffect(() => {
    if (isOpen) {
      setIframeLoaded(false);
    }
  }, [isOpen]);

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700 text-gray-900 dark:text-white max-w-6xl w-full h-[90vh] p-0 flex flex-col">
        {/* Header */}
        <div className="px-5 py-4 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
          <DialogTitle className="text-lg font-semibold flex-1 truncate mr-4">
            {documentTitle}
          </DialogTitle>
          <div className="flex items-center space-x-2">
          </div>
        </div>

        {/* PDF Container */}
        <div className="flex-1 overflow-hidden bg-gray-100 dark:bg-gray-900">
          {!iframeLoaded && (
            <div className="flex items-center justify-center h-full">
              <div className="text-gray-500 dark:text-gray-400">Loading PDF...</div>
            </div>
          )}
          <iframe
            src={pdfUrl}
            className="w-full h-full border-none"
            onLoad={() => setIframeLoaded(true)}
            style={{ display: iframeLoaded ? 'block' : 'none' }}
            title="PDF Document"
          />
        </div>

        
      </DialogContent>
    </Dialog>
  );
}