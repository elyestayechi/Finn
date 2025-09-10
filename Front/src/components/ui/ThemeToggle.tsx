import { useState, useEffect } from 'react';
import { useTheme } from '@/components/contexts/ThemeContext';

const ThemeToggle = () => {
  const { theme, toggleTheme } = useTheme();
  const [isMounted, setIsMounted] = useState(false);

  useEffect(() => {
    setIsMounted(true);
  }, []);

  const handleToggle = () => {
    toggleTheme();
  };

  // Prevent flash of incorrect theme before component mounts
  if (!isMounted) {
    return (
      <div className="w-16 h-8 rounded-full bg-gray-300 dark:bg-gray-700"></div>
    );
  }

  return (
    <button
      onClick={handleToggle}
      className={`relative w-16 h-8 rounded-full transition-all duration-500 ease-in-out overflow-hidden ${
        theme === 'light' 
          ? 'bg-gradient-to-br from-blue-400 to-blue-600' 
          : 'bg-gradient-to-br from-indigo-900 to-black'
      }`}
      aria-label={`Switch to ${theme === 'light' ? 'dark' : 'light'} mode`}
    >
      {/* Sun/Moon */}
      <div
        className={`absolute top-1 w-6 h-6 rounded-full transition-all duration-500 ease-in-out ${
          theme === 'light'
            ? 'left-1 bg-yellow-300 shadow-[0_0_10px_2px_rgba(255,204,0,0.6)]'
            : 'left-9 bg-gray-200 shadow-[0_0_8px_2px_rgba(255,255,255,0.4)]'
        }`}
      >
        {/* Moon craters */}
        {theme === 'dark' && (
          <>
            <div className="absolute top-5 left-3 w-1 h-1 rounded-full bg-gray-400 opacity-70"></div>
            <div className="absolute top-3 left-5 w-2 h-2 rounded-full bg-gray-400 opacity-70"></div>
            <div className="absolute top-2 left-2 w-1 h-1 rounded-full bg-gray-400 opacity-70"></div>
          </>
        )}
      </div>

      {/* Clouds - Light Mode */}
      <div
        className={`absolute transition-opacity duration-500 ease-in-out ${
          theme === 'light' ? 'opacity-100' : 'opacity-0'
        }`}
      >
        <div className="absolute top-3 left-10 w-6 h-4 bg-white rounded-full"></div>
        <div className="absolute top-5 left-12 w-4 h-3 bg-white rounded-full"></div>
        <div className="absolute top-2 left-7 w-5 h-3 bg-white rounded-full"></div>
      </div>

      {/* Stars - Dark Mode */}
      <div
        className={`absolute transition-opacity duration-500 ease-in-out ${
          theme === 'dark' ? 'opacity-100' : 'opacity-0'
        }`}
      >
        <div className="absolute top-2 left-4 w-1 h-1 bg-white rounded-full"></div>
        <div className="absolute top-5 left-6 w-0.5 h-0.5 bg-white rounded-full"></div>
        <div className="absolute top-3 left-2 w-0.5 h-0.5 bg-white rounded-full"></div>
        <div className="absolute top-1 left-8 w-1 h-1 bg-white rounded-full"></div>
        <div className="absolute top-6 left-3 w-0.5 h-0.5 bg-white rounded-full"></div>
      </div>

      {/* Darker Clouds - Dark Mode */}
      <div
        className={`absolute transition-opacity duration-500 ease-in-out ${
          theme === 'dark' ? 'opacity-70' : 'opacity-0'
        }`}
      >
        <div className="absolute top-4 left-9 w-5 h-3 bg-gray-400 rounded-full"></div>
        <div className="absolute top-6 left-11 w-3 h-2 bg-gray-400 rounded-full"></div>
      </div>
    </button>
  );
};

export default ThemeToggle;