import React from 'react';
import { Plus, Search, Filter, Download, RefreshCw, BookOpen, Settings, HelpCircle } from 'lucide-react';

const QuickActions = ({ onCreateClick, onRefresh, isLoading }) => {
  const quickActions = [
    {
      icon: Plus,
      label: 'New Query',
      description: 'Create a new task query',
      action: onCreateClick,
      className: 'bg-primary-600 hover:bg-primary-700 text-white',
      shortcut: '⌘N'
    },
    {
      icon: RefreshCw,
      label: 'Refresh',
      description: 'Reload all queries',
      action: onRefresh,
      className: 'bg-gray-100 hover:bg-gray-200 text-gray-700',
      shortcut: '⌘R',
      loading: isLoading
    },
    {
      icon: Download,
      label: 'Export',
      description: 'Download query data',
      action: () => console.log('Export clicked'),
      className: 'bg-gray-100 hover:bg-gray-200 text-gray-700',
      shortcut: '⌘E'
    }
  ];

  const helpLinks = [
    {
      icon: BookOpen,
      label: 'Documentation',
      href: '#',
      description: 'Learn how to use the platform'
    },
    {
      icon: HelpCircle,
      label: 'Support',
      href: '#',
      description: 'Get help from our team'
    },
    {
      icon: Settings,
      label: 'Settings',
      href: '#',
      description: 'Customize your experience'
    }
  ];

  return (
    <div className="space-y-6">
      {/* Quick Actions */}
      <div className="card p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h3>
        <div className="space-y-3">
          {quickActions.map((action, index) => (
            <button
              key={action.label}
              onClick={action.action}
              disabled={action.loading}
              className={`w-full flex items-center gap-3 p-3 rounded-xl transition-all duration-200 ${action.className} ${
                action.loading ? 'opacity-50 cursor-not-allowed' : ''
              }`}
            >
              <action.icon className={`w-5 h-5 ${action.loading ? 'animate-spin' : ''}`} />
              <div className="flex-1 text-left">
                <div className="font-medium">{action.label}</div>
                <div className="text-sm opacity-80">{action.description}</div>
              </div>
              <kbd className="text-xs opacity-60 bg-black/10 px-2 py-1 rounded">
                {action.shortcut}
              </kbd>
            </button>
          ))}
        </div>
      </div>

      {/* Quick Stats */}
      <div className="card p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Today's Activity</h3>
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-600">Queries Created</span>
            <span className="text-lg font-semibold text-gray-900">3</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-600">Tasks Completed</span>
            <span className="text-lg font-semibold text-success-600">12</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-600">Active Sessions</span>
            <span className="text-lg font-semibold text-primary-600">5</span>
          </div>
        </div>
      </div>

      {/* Help & Support */}
      <div className="card p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Help & Support</h3>
        <div className="space-y-2">
          {helpLinks.map((link) => (
            <a
              key={link.label}
              href={link.href}
              className="flex items-center gap-3 p-2 rounded-lg hover:bg-gray-50 transition-colors group"
            >
              <link.icon className="w-4 h-4 text-gray-400 group-hover:text-gray-600" />
              <div className="flex-1">
                <div className="text-sm font-medium text-gray-900">{link.label}</div>
                <div className="text-xs text-gray-500">{link.description}</div>
              </div>
            </a>
          ))}
        </div>
      </div>

      {/* Tips */}
      <div className="card p-6 bg-gradient-to-br from-primary-50 to-primary-100 border-primary-200">
        <div className="flex items-start gap-3">
          <div className="w-8 h-8 bg-primary-600 rounded-lg flex items-center justify-center flex-shrink-0">
            <HelpCircle className="w-4 h-4 text-white" />
          </div>
          <div>
            <h4 className="font-semibold text-gray-900 mb-1">Pro Tip</h4>
            <p className="text-sm text-gray-600 leading-relaxed">
              Use keyboard shortcuts to navigate faster. Press <kbd className="bg-white px-1 py-0.5 rounded text-xs">⌘K</kbd> to open quick search.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default QuickActions; 