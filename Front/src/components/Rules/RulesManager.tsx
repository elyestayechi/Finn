// RulesManager.tsx
import React, { useState, useEffect, useMemo } from 'react';
import { Shield, Save, RefreshCw, Edit, X, Search, ChevronDown, ChevronUp } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { useTheme } from '@/components/contexts/ThemeContext';

interface Rule {
  Category: string;
  Item: string;
  Weight: string;
}

interface EditingRule {
  category: string;
  originalItem: string;
  item: string;
  weight: string;
}

const RulesManager: React.FC = () => {
  const [rules, setRules] = useState<Rule[]>([]);
  const [editingRule, setEditingRule] = useState<EditingRule | null>(null);
  const [groupedRules, setGroupedRules] = useState<{ [key: string]: Rule[] }>({});
  const [openDialog, setOpenDialog] = useState(false);
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [expandedCategories, setExpandedCategories] = useState<Set<string>>(new Set());
  const [sortConfig, setSortConfig] = useState<{ key: 'Item' | 'Weight'; direction: 'asc' | 'desc' } | null>(null);
  const { theme } = useTheme();

  // Fetch rules on component mount
  useEffect(() => {
    fetchRules();
  }, []);

  // Group rules by category whenever rules change
  useEffect(() => {
    const grouped = rules.reduce((acc, rule) => {
      if (!acc[rule.Category]) {
        acc[rule.Category] = [];
      }
      acc[rule.Category].push(rule);
      return acc;
    }, {} as { [key: string]: Rule[] });
    
    setGroupedRules(grouped);
    
    // Start with ALL categories COLLAPSED by default
    setExpandedCategories(new Set());
  }, [rules]);

  // Filter and sort rules
  const filteredAndSortedRules = useMemo(() => {
    const result: { [key: string]: Rule[] } = {};
    
    Object.entries(groupedRules).forEach(([category, categoryRules]) => {
      // Filter by search term
      let filtered = categoryRules.filter(rule =>
        rule.Item.toLowerCase().includes(searchTerm.toLowerCase()) ||
        rule.Category.toLowerCase().includes(searchTerm.toLowerCase()) ||
        rule.Weight.includes(searchTerm)
      );

      // Sort if sortConfig is set
      if (sortConfig) {
        filtered = filtered.sort((a, b) => {
          const aValue = a[sortConfig.key];
          const bValue = b[sortConfig.key];
          
          if (sortConfig.key === 'Weight') {
            const numA = parseFloat(aValue);
            const numB = parseFloat(bValue);
            return sortConfig.direction === 'asc' ? numA - numB : numB - numA;
          } else {
            return sortConfig.direction === 'asc' 
              ? aValue.localeCompare(bValue) 
              : bValue.localeCompare(aValue);
          }
        });
      }

      if (filtered.length > 0) {
        result[category] = filtered;
      }
    });

    return result;
  }, [groupedRules, searchTerm, sortConfig]);

  const fetchRules = async () => {
    try {
      setLoading(true);
      const response = await fetch('http://localhost:8000/api/rules');
      
      const contentType = response.headers.get('content-type');
      if (!contentType || !contentType.includes('application/json')) {
        throw new Error('Server returned non-JSON response');
      }
      
      const data = await response.json();
      setRules(data);
    } catch (error) {
      console.error('Error fetching rules:', error);
      showSnackbar('Error fetching rules. Make sure backend is running on port 8000.', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleEditClick = (rule: Rule) => {
    setEditingRule({
      category: rule.Category,
      originalItem: rule.Item,
      item: rule.Item,
      weight: rule.Weight
    });
  };

  const handleSaveClick = async () => {
    if (editingRule) {
      try {
        setSaving(true);
        
        const updatedRules = rules.map(rule => {
          // If this is the rule we're editing
          if (rule.Category === editingRule.category && rule.Item === editingRule.originalItem) {
            return {
              ...rule,
              Item: editingRule.item,
              Weight: editingRule.weight
            };
          }
          return rule;
        });
        
        const response = await fetch('http://localhost:8000/api/rules', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(updatedRules),
        });

        if (response.ok) {
          setRules(updatedRules);
          setEditingRule(null);
          showSnackbar('Rule updated successfully', 'success');
        } else {
          throw new Error('Failed to update rule');
        }
      } catch (error) {
        console.error('Error updating rule:', error);
        showSnackbar('Error updating rule', 'error');
      } finally {
        setSaving(false);
      }
    }
  };

  const handleCancelEdit = () => {
    setEditingRule(null);
  };

  const handleResetRules = async () => {
    try {
      setSaving(true);
      const response = await fetch('http://localhost:8000/api/rules/reset', {
        method: 'POST',
      });

      if (response.ok) {
        fetchRules();
        setOpenDialog(false);
        showSnackbar('Rules reset to default successfully', 'success');
      } else {
        throw new Error('Failed to reset rules');
      }
    } catch (error) {
      console.error('Error resetting rules:', error);
      showSnackbar('Error resetting rules', 'error');
    } finally {
      setSaving(false);
    }
  };

  const toggleCategory = (category: string) => {
    setExpandedCategories(prev => {
      const newSet = new Set(prev);
      if (newSet.has(category)) {
        newSet.delete(category);
      } else {
        newSet.add(category);
      }
      return newSet;
    });
  };

  // Add this function to expand all categories
  const expandAllCategories = () => {
    const categories = Object.keys(groupedRules);
    setExpandedCategories(new Set(categories));
  };

  // Add this function to collapse all categories
  const collapseAllCategories = () => {
    setExpandedCategories(new Set());
  };

  const handleSort = (key: 'Item' | 'Weight') => {
    setSortConfig(current => {
      if (current?.key === key) {
        return {
          key,
          direction: current.direction === 'asc' ? 'desc' : 'asc'
        };
      }
      return { key, direction: 'asc' };
    });
  };

  const showSnackbar = (message: string, severity: string) => {
    setSnackbar({ open: true, message, severity });
  };

  const handleCloseSnackbar = () => {
    setSnackbar({ ...snackbar, open: false });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-48">
        <div className="text-gray-500 dark:text-gray-400">Loading rules...</div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div className="flex items-center space-x-3">
          <Shield className="w-6 h-6 text-blue-600 dark:text-blue-400" />
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white">Rules Management</h2>
        </div>
        <div className="flex items-center space-x-3">
          <div className="relative flex-1 sm:flex-initial">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
            <Input
              placeholder="Search rules..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10 bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600 text-sm"
            />
          </div>
          <Button
            onClick={expandAllCategories}
            variant="outline"
            size="sm"
            className="hidden sm:flex"
          >
            Expand All
          </Button>
          <Button
            onClick={collapseAllCategories}
            variant="outline"
            size="sm"
            className="hidden sm:flex"
          >
            Collapse All
          </Button>
          <Button
            onClick={() => setOpenDialog(true)}
            disabled={saving}
            variant="outline"
            className="flex items-center space-x-2"
          >
            <RefreshCw className="w-4 h-4" />
            <span className="hidden sm:inline">Reset</span>
          </Button>
        </div>
      </div>

      {/* Mobile buttons */}
      <div className="flex sm:hidden space-x-2">
        <Button onClick={expandAllCategories} variant="outline" size="sm" className="flex-1">
          Expand All
        </Button>
        <Button onClick={collapseAllCategories} variant="outline" size="sm" className="flex-1">
          Collapse All
        </Button>
      </div>

      {/* Category summary */}
      <div className="text-sm text-gray-600 dark:text-gray-400">
        {Object.keys(filteredAndSortedRules).length} categories, {rules.length} total rules 
      </div>

      {/* Rules Table */}
      <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
        {/* Table Header */}
        <div className="grid grid-cols-[1fr_100px_120px] bg-gray-50 dark:bg-gray-700 px-4 py-3 border-b border-gray-200 dark:border-gray-600">
          <button
            onClick={() => handleSort('Item')}
            className="text-left text-sm font-medium text-gray-900 dark:text-white flex items-center hover:text-blue-600 dark:hover:text-blue-400"
          >
            Rule
            {sortConfig?.key === 'Item' && (
              sortConfig.direction === 'asc' ? <ChevronUp className="w-4 h-4 ml-1" /> : <ChevronDown className="w-4 h-4 ml-1" />
            )}
          </button>
          <button
            onClick={() => handleSort('Weight')}
            className="text-left text-sm font-medium text-gray-900 dark:text-white flex items-center hover:text-blue-600 dark:hover:text-blue-400"
          >
            Weight
            {sortConfig?.key === 'Weight' && (
              sortConfig.direction === 'asc' ? <ChevronUp className="w-4 h-4 ml-1" /> : <ChevronDown className="w-4 h-4 ml-1" />
            )}
          </button>
          <div className="text-right text-sm font-medium text-gray-900 dark:text-white">
            Actions
          </div>
        </div>

        {/* Table Body */}
        <div className="max-h-[600px] overflow-y-auto">
          {Object.entries(filteredAndSortedRules).map(([category, categoryRules]) => (
            <div key={category}>
              {/* Category Header */}
              <div 
                className="bg-blue-50 dark:bg-blue-900/30 px-4 py-3 border-b border-gray-200 dark:border-gray-600 cursor-pointer hover:bg-blue-100 dark:hover:bg-blue-900/50 transition-colors"
                onClick={() => toggleCategory(category)}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    {expandedCategories.has(category) ? (
                      <ChevronUp className="w-4 h-4 text-blue-600" />
                    ) : (
                      <ChevronDown className="w-4 h-4 text-blue-600" />
                    )}
                    <span className="font-medium text-blue-800 dark:text-blue-200">
                      {category}
                    </span>
                  </div>
                  <span className="text-xs text-blue-600 dark:text-blue-300 bg-blue-100 dark:bg-blue-800/30 px-2 py-1 rounded-full">
                    {categoryRules.length} rule{categoryRules.length !== 1 ? 's' : ''}
                  </span>
                </div>
              </div>

              {/* Category Rules - Only show if expanded */}
              {expandedCategories.has(category) && categoryRules.map((rule, index) => {
                const isEditing = editingRule?.category === rule.Category && editingRule.originalItem === rule.Item;
                
                return (
                  <div
                    key={`${rule.Category}-${rule.Item}-${index}`}
                    className="grid grid-cols-[1fr_100px_120px] px-4 py-3 border-b border-gray-100 dark:border-gray-700 last:border-b-0 even:bg-gray-50 dark:even:bg-gray-700/50 hover:bg-gray-100 dark:hover:bg-gray-700/70 transition-colors"
                  >
                    {/* Rule Item */}
                    <div className="flex items-center">
                      {isEditing ? (
                        <Input
                          value={editingRule.item}
                          onChange={(e) => setEditingRule(prev => prev ? {...prev, item: e.target.value} : null)}
                          className="bg-white dark:bg-gray-600 border-gray-300 dark:border-gray-500 text-sm h-8"
                        />
                      ) : (
                        <span className="text-sm text-gray-900 dark:text-white">
                          {rule.Item}
                        </span>
                      )}
                    </div>

                    {/* Rule Weight */}
                    <div className="flex items-center">
                      {isEditing ? (
                        <Input
                          type="number"
                          value={editingRule.weight}
                          onChange={(e) => setEditingRule(prev => prev ? {...prev, weight: e.target.value} : null)}
                          className="bg-white dark:bg-gray-600 border-gray-300 dark:border-gray-500 text-sm h-8 w-20"
                        />
                      ) : (
                        <span className={`text-sm font-medium ${
                          parseFloat(rule.Weight) > 10 
                            ? 'text-red-600 dark:text-red-400' 
                            : parseFloat(rule.Weight) > 5 
                            ? 'text-orange-600 dark:text-orange-400' 
                            : 'text-green-600 dark:text-green-400'
                        }`}>
                          {rule.Weight}
                        </span>
                      )}
                    </div>

                    {/* Actions */}
                    <div className="flex items-center justify-end space-x-2">
                      {isEditing ? (
                        <>
                          <Button
                            onClick={handleSaveClick}
                            disabled={saving}
                            size="sm"
                            className="h-7 bg-green-600 hover:bg-green-700"
                          >
                            <Save className="w-3 h-3" />
                          </Button>
                          <Button
                            onClick={handleCancelEdit}
                            disabled={saving}
                            size="sm"
                            variant="outline"
                            className="h-7"
                          >
                            <X className="w-3 h-3" />
                          </Button>
                        </>
                      ) : (
                        <Button
                          onClick={() => handleEditClick(rule)}
                          disabled={saving || editingRule !== null}
                          size="sm"
                          variant="outline"
                          className="h-7"
                        >
                          <Edit className="w-3 h-3" />
                        </Button>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          ))}
        </div>
      </div>

      {/* Empty State */}
      {Object.keys(filteredAndSortedRules).length === 0 && (
        <div className="text-center py-12 text-gray-500 dark:text-gray-400">
          <Shield className="w-12 h-12 mx-auto mb-4 opacity-50" />
          <p>No rules found matching your search criteria</p>
        </div>
      )}

      {/* Reset Confirmation Dialog */}
      {openDialog && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Reset Rules</h3>
            <p className="text-gray-600 dark:text-gray-300 mb-6">
              Are you sure you want to reset all rules to their default values? This action cannot be undone.
            </p>
            <div className="flex justify-end space-x-3">
              <Button
                onClick={() => setOpenDialog(false)}
                disabled={saving}
                variant="outline"
              >
                Cancel
              </Button>
              <Button
                onClick={handleResetRules}
                disabled={saving}
                className="bg-red-600 hover:bg-red-700"
              >
                {saving ? 'Resetting...' : 'Reset'}
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Snackbar Notification */}
      {snackbar.open && (
        <div className={`fixed bottom-4 right-4 px-4 py-3 rounded-lg shadow-lg z-50 ${
          snackbar.severity === 'error' 
            ? 'bg-red-600 text-white' 
            : 'bg-green-600 text-white'
        }`}>
          <div className="flex items-center justify-between">
            <span>{snackbar.message}</span>
            <button
              onClick={handleCloseSnackbar}
              className="ml-4 hover:opacity-70"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default RulesManager;