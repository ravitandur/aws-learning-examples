import React from 'react';
import { ChevronRight, Home, Activity, TrendingUp, Settings, User } from 'lucide-react';

export type PageType = 'dashboard' | 'management' | 'analytics' | 'settings' | 'profile' | 'default';

export interface BreadcrumbItem {
  label: string;
  href?: string;
  icon?: React.ReactNode;
}

export interface PageHeaderProps {
  title: string;
  description?: string;
  actions?: React.ReactNode;
  emoji?: string;
  pageType?: PageType;
  breadcrumbs?: BreadcrumbItem[];
  status?: 'active' | 'inactive' | 'loading' | 'error';
  statusText?: string;
  isLoading?: boolean;
}

const getPageTypeStyles = (pageType: PageType) => {
  // Clean, minimalist background with subtle glassmorphism
  const baseBackground = `
    bg-white/70 dark:bg-gray-900/70 
    backdrop-blur-md border border-gray-200/50 dark:border-gray-700/50
    shadow-lg shadow-gray-900/5 dark:shadow-black/10
  `;
  
  switch (pageType) {
    case 'dashboard':
      return {
        background: baseBackground,
        accentColor: 'blue',
        titleAccent: 'text-blue-700 dark:text-blue-300',
        icon: <Home className="w-5 h-5" />,
        iconContainer: 'bg-blue-50/80 dark:bg-blue-900/30 border-blue-200/60 dark:border-blue-700/50',
        accentBar: 'bg-gradient-to-r from-blue-500 to-blue-600',
        hoverAccent: 'hover:shadow-blue-500/10 hover:border-blue-300/60 dark:hover:border-blue-600/50'
      };
    case 'management':
      return {
        background: baseBackground,
        accentColor: 'emerald',
        titleAccent: 'text-emerald-700 dark:text-emerald-300',
        icon: <Settings className="w-5 h-5" />,
        iconContainer: 'bg-emerald-50/80 dark:bg-emerald-900/30 border-emerald-200/60 dark:border-emerald-700/50',
        accentBar: 'bg-gradient-to-r from-emerald-500 to-emerald-600',
        hoverAccent: 'hover:shadow-emerald-500/10 hover:border-emerald-300/60 dark:hover:border-emerald-600/50'
      };
    case 'analytics':
      return {
        background: baseBackground,
        accentColor: 'purple',
        titleAccent: 'text-purple-700 dark:text-purple-300',
        icon: <TrendingUp className="w-5 h-5" />,
        iconContainer: 'bg-purple-50/80 dark:bg-purple-900/30 border-purple-200/60 dark:border-purple-700/50',
        accentBar: 'bg-gradient-to-r from-purple-500 to-purple-600',
        hoverAccent: 'hover:shadow-purple-500/10 hover:border-purple-300/60 dark:hover:border-purple-600/50'
      };
    case 'settings':
      return {
        background: baseBackground,
        accentColor: 'slate',
        titleAccent: 'text-slate-700 dark:text-slate-300',
        icon: <Settings className="w-5 h-5" />,
        iconContainer: 'bg-slate-50/80 dark:bg-slate-900/30 border-slate-200/60 dark:border-slate-700/50',
        accentBar: 'bg-gradient-to-r from-slate-500 to-slate-600',
        hoverAccent: 'hover:shadow-slate-500/10 hover:border-slate-300/60 dark:hover:border-slate-600/50'
      };
    case 'profile':
      return {
        background: baseBackground,
        accentColor: 'amber',
        titleAccent: 'text-amber-700 dark:text-amber-300',
        icon: <User className="w-5 h-5" />,
        iconContainer: 'bg-amber-50/80 dark:bg-amber-900/30 border-amber-200/60 dark:border-amber-700/50',
        accentBar: 'bg-gradient-to-r from-amber-500 to-amber-600',
        hoverAccent: 'hover:shadow-amber-500/10 hover:border-amber-300/60 dark:hover:border-amber-600/50'
      };
    default:
      return {
        background: baseBackground,
        accentColor: 'gray',
        titleAccent: 'text-gray-700 dark:text-gray-300',
        icon: null,
        iconContainer: 'bg-gray-50/80 dark:bg-gray-900/30 border-gray-200/60 dark:border-gray-700/50',
        accentBar: 'bg-gradient-to-r from-gray-500 to-gray-600',
        hoverAccent: 'hover:shadow-gray-500/10 hover:border-gray-300/60 dark:hover:border-gray-600/50'
      };
  }
};

const getStatusIndicator = (status?: string, statusText?: string) => {
  if (!status) return null;

  const statusConfig = {
    active: {
      color: 'bg-green-100 text-green-800 border-green-200 dark:bg-green-900/20 dark:text-green-200 dark:border-green-800/30',
      dot: 'bg-green-500',
      text: statusText || 'Active'
    },
    inactive: {
      color: 'bg-gray-100 text-gray-800 border-gray-200 dark:bg-gray-900/20 dark:text-gray-200 dark:border-gray-800/30',
      dot: 'bg-gray-400',
      text: statusText || 'Inactive'
    },
    loading: {
      color: 'bg-blue-100 text-blue-800 border-blue-200 dark:bg-blue-900/20 dark:text-blue-200 dark:border-blue-800/30',
      dot: 'bg-blue-500 animate-pulse',
      text: statusText || 'Loading'
    },
    error: {
      color: 'bg-red-100 text-red-800 border-red-200 dark:bg-red-900/20 dark:text-red-200 dark:border-red-800/30',
      dot: 'bg-red-500',
      text: statusText || 'Error'
    }
  };

  const config = statusConfig[status as keyof typeof statusConfig];
  if (!config) return null;

  return (
    <div className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium border ${config.color}`}>
      <div className={`w-2 h-2 rounded-full ${config.dot}`}></div>
      {config.text}
    </div>
  );
};

const Breadcrumbs: React.FC<{ items: BreadcrumbItem[] }> = ({ items }) => {
  if (!items.length) return null;

  return (
    <nav className="flex items-center space-x-2 text-sm text-gray-500 dark:text-gray-400 mb-3" aria-label="Breadcrumb">
      {items.map((item, index) => (
        <React.Fragment key={index}>
          <div className="flex items-center gap-1.5">
            {item.icon && <span className="text-gray-400 dark:text-gray-500">{item.icon}</span>}
            {item.href ? (
              <button 
                className="hover:text-gray-700 dark:hover:text-gray-200 transition-colors focus:outline-none focus:underline"
                onClick={() => {/* Navigation would be handled by router */}}
              >
                {item.label}
              </button>
            ) : (
              <span className="text-gray-700 dark:text-gray-200 font-medium">{item.label}</span>
            )}
          </div>
          {index < items.length - 1 && (
            <ChevronRight className="w-4 h-4 text-gray-300 dark:text-gray-600" />
          )}
        </React.Fragment>
      ))}
    </nav>
  );
};

const PageHeader: React.FC<PageHeaderProps> = ({ 
  title, 
  description, 
  actions, 
  emoji,
  pageType = 'default',
  breadcrumbs = [],
  status,
  statusText,
  isLoading = false
}) => {
  const styles = getPageTypeStyles(pageType);

  // Loading skeleton
  if (isLoading) {
    return (
      <div className="mb-4">
        <div className="bg-white/70 dark:bg-gray-900/70 backdrop-blur-md border border-gray-200/50 dark:border-gray-700/50 rounded-xl p-4 animate-pulse">
          <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
            <div className="flex-1">
              <div className="flex items-center gap-3 mb-3">
                <div className="w-10 h-10 bg-gray-200 dark:bg-gray-700 rounded-lg"></div>
                <div>
                  <div className="h-6 bg-gray-200 dark:bg-gray-700 rounded w-48 mb-2"></div>
                  <div className="h-1 bg-gray-200 dark:bg-gray-700 rounded w-12"></div>
                </div>
              </div>
              <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-96 mb-2"></div>
              <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-80"></div>
            </div>
            <div className="flex gap-2">
              <div className="w-24 h-9 bg-gray-200 dark:bg-gray-700 rounded-lg"></div>
              <div className="w-20 h-9 bg-gray-200 dark:bg-gray-700 rounded-lg"></div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="mb-4">
      <div className={`rounded-xl ${styles.background} ${styles.hoverAccent} p-4 transition-all duration-200`}>
        {/* Breadcrumbs */}
        <Breadcrumbs items={breadcrumbs} />

        <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
          <div className="flex-1 min-w-0">
            {/* Title Row with Status */}
            <div className="flex items-center gap-3 mb-3 flex-wrap">
              <div className="flex items-center gap-3">
                {styles.icon && (
                  <div className={`p-2.5 rounded-lg ${styles.iconContainer} ${styles.titleAccent} border transition-colors duration-200`}>
                    {styles.icon}
                  </div>
                )}
                <div>
                  <h1 className="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
                    {emoji && <span>{emoji}</span>}
                    {title}
                  </h1>
                  {/* Clean accent line under title */}
                  <div className={`h-0.5 w-12 ${styles.accentBar} rounded-full mt-1.5 transition-all duration-300`}></div>
                </div>
              </div>
              {getStatusIndicator(status, statusText)}
            </div>

            {/* Description */}
            {description && (
              <p className="text-gray-600 dark:text-gray-300 max-w-3xl leading-relaxed">
                {description}
              </p>
            )}

            {/* Activity Indicator */}
            {status === 'loading' && (
              <div className="flex items-center gap-2 mt-4 text-sm text-gray-500 dark:text-gray-400">
                <Activity className="w-4 h-4 animate-pulse" />
                <span>Processing...</span>
              </div>
            )}
          </div>

          {/* Actions */}
          {actions && (
            <div className="flex flex-col sm:flex-row gap-3 sm:items-start sm:shrink-0">
              <div className="flex flex-wrap gap-2">
                {actions}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default PageHeader;