import { Bell, Search, Plus } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import ThemeToggle from '@/components/ui/ThemeToggle';

interface TopNavigationProps {
  onNewAnalysis: () => void;
  onSearchChange: (searchTerm: string) => void;
  searchTerm: string;
}

export default function TopNavigation({ onNewAnalysis, onSearchChange, searchTerm }: TopNavigationProps) {
  return (
    <div className="h-14 bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-800 flex items-center justify-between px-5">
      {/* Search */}
      <div className="flex items-center space-x-4 flex-1 max-w-md">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 dark:text-gray-500 w-4 h-4" />
          <Input
            placeholder="Search PDF reports by name..."
            value={searchTerm}
            onChange={(e) => onSearchChange(e.target.value)}
            className="pl-10 bg-gray-50 dark:bg-gray-800 border-gray-200 dark:border-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:border-blue-500 dark:focus:border-blue-400 text-sm"
          />
        </div>
      </div>

      {/* Actions */}
      <div className="flex items-center space-x-3">
        {/* Theme Toggle */}
        <ThemeToggle />

        {/* Notifications */}
        <button className="relative p-1.5 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-md transition-colors">
          <Bell className="w-5 h-5 text-gray-600 dark:text-gray-400" />
          <span className="absolute -top-0.5 -right-0.5 w-2 h-2 bg-red-500 rounded-full"></span>
        </button>

        {/* New Analysis Button */}
        <Button
          onClick={onNewAnalysis}
          className="bg-blue-600 hover:bg-blue-700 text-white flex items-center space-x-2 px-3 py-2 text-sm"
        >
          <Plus className="w-4 h-4" />
          <span>New Analysis</span>
        </Button>
      </div>
    </div>
  );
}