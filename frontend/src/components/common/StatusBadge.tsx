// components/common/StatusBadge.tsx — Status badge component
interface StatusBadgeProps {
  status: 'online' | 'offline' | 'starting' | 'error';
  label?: string;
  showDot?: boolean;
  size?: 'sm' | 'md' | 'lg';
}

const statusColors = {
  online: 'bg-green-500',
  offline: 'bg-gray-500',
  starting: 'bg-yellow-500 animate-pulse',
  error: 'bg-red-500',
};

const statusLabels = {
  online: 'Online',
  offline: 'Offline',
  starting: 'Starting',
  error: 'Error',
};

const sizeClasses = {
  sm: 'text-xs px-2 py-0.5',
  md: 'text-sm px-2.5 py-1',
  lg: 'text-base px-3 py-1.5',
};

export default function StatusBadge({ 
  status, 
  label, 
  showDot = true, 
  size = 'md' 
}: StatusBadgeProps) {
  const displayLabel = label || statusLabels[status];
  
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full font-medium ${sizeClasses[size]}`}>
      {showDot && (
        <span className={`w-2 h-2 rounded-full ${statusColors[status]}`} />
      )}
      <span className="capitalize">{displayLabel}</span>
    </span>
  );
}
