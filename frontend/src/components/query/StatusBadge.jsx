import React from 'react';
import { Clock, CheckCircle2, AlertCircle, Ban, Loader2, Play, Pause } from 'lucide-react';

const StatusBadge = ({ status, size = 'md', showPulse = false }) => {
  const getStatusConfig = () => {
    switch (status?.toLowerCase()) {
      case 'completed':
        return {
          className: 'badge-success',
          icon: CheckCircle2,
          label: 'Completed',
          pulseClass: 'animate-none'
        };
      case 'in_progress':
        return {
          className: 'badge-info',
          icon: Play,
          label: 'In Progress',
          pulseClass: showPulse ? 'animate-pulse' : 'animate-none'
        };
      case 'failed':
        return {
          className: 'badge-danger',
          icon: AlertCircle,
          label: 'Failed',
          pulseClass: 'animate-none'
        };
      case 'cancelled':
        return {
          className: 'badge-neutral',
          icon: Ban,
          label: 'Cancelled',
          pulseClass: 'animate-none'
        };
      case 'pending':
        return {
          className: 'badge-warning',
          icon: Pause,
          label: 'Pending',
          pulseClass: showPulse ? 'animate-pulse' : 'animate-none'
        };
      case 'processing':
        return {
          className: 'badge-info',
          icon: Loader2,
          label: 'Processing',
          pulseClass: 'animate-spin'
        };
      default:
        return {
          className: 'badge-neutral',
          icon: Clock,
          label: 'Unknown',
          pulseClass: 'animate-none'
        };
    }
  };

  const getSizeClasses = () => {
    switch (size) {
      case 'sm':
        return {
          badge: 'px-2 py-1 text-xs gap-1',
          icon: 'w-3 h-3'
        };
      case 'lg':
        return {
          badge: 'px-4 py-2 text-base gap-2',
          icon: 'w-5 h-5'
        };
      default: // md
        return {
          badge: 'px-3 py-1.5 text-sm gap-1.5',
          icon: 'w-4 h-4'
        };
    }
  };

  const statusConfig = getStatusConfig();
  const sizeClasses = getSizeClasses();
  const IconComponent = statusConfig.icon;

  return (
    <div className={`badge ${statusConfig.className} ${sizeClasses.badge} transition-all duration-200 hover:scale-105`}>
      <IconComponent 
        className={`${sizeClasses.icon} ${statusConfig.pulseClass}`} 
        aria-hidden="true"
      />
      <span className="font-medium">{statusConfig.label}</span>
    </div>
  );
};

export default StatusBadge;