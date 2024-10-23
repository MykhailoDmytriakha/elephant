import React from 'react';
import { Clock, CheckCircle2, AlertCircle, Ban } from 'lucide-react';

const StatusBadge = ({ status }) => {
  const getStatusStyles = () => {
    switch (status?.toLowerCase()) {
      case 'completed':
        return 'bg-green-100 text-green-700 border-green-200';
      case 'in_progress':
        return 'bg-blue-100 text-blue-700 border-blue-200';
      case 'failed':
        return 'bg-red-100 text-red-700 border-red-200';
      case 'cancelled':
        return 'bg-gray-100 text-gray-700 border-gray-200';
      case 'pending':
        return 'bg-yellow-100 text-yellow-700 border-yellow-200';
      default:
        return 'bg-gray-100 text-gray-700 border-gray-200';
    }
  };

  const getStatusIcon = () => {
    switch (status?.toLowerCase()) {
      case 'completed':
        return <CheckCircle2 className="w-4 h-4" />;
      case 'in_progress':
        return <Clock className="w-4 h-4" />;
      case 'failed':
        return <AlertCircle className="w-4 h-4" />;
      case 'cancelled':
        return <Ban className="w-4 h-4" />;
      case 'pending':
        return <Clock className="w-4 h-4" />;
      default:
        return <Clock className="w-4 h-4" />;
    }
  };

  return (
    <div className={`flex items-center gap-1.5 px-3 py-1 rounded-full border ${getStatusStyles()}`}>
      {getStatusIcon()}
      <span className="text-sm font-medium capitalize">{status?.replace('_', ' ') || 'Unknown'}</span>
    </div>
  );
};

export default StatusBadge;