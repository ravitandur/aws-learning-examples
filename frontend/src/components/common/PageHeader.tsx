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
  // Unified modern background
  const unifiedBackground = `
    bg-gradient-to-br from-white via-gray-50/60 to-slate-100/40 
    dark:from-gray-900 dark:via-gray-800/80 dark:to-gray-900
    backdrop-blur-xl border border-white/30 dark:border-gray-700/40
    shadow-2xl shadow-slate-900/5 dark:shadow-black/25
    relative overflow-hidden
  `;
  
  switch (pageType) {
    case 'dashboard':
      return {
        gradient: unifiedBackground,
        titleAccent: 'text-blue-700 dark:text-blue-300',
        icon: <Home className="w-5 h-5" />,
        accentClasses: {
          iconBg: 'bg-blue-500/10 border-blue-200/50 dark:border-blue-700/50',
          iconShadow: 'shadow-blue-500/20',
          underline: 'from-blue-500 to-blue-600',
          overlay: 'from-blue-500/3 via-transparent to-blue-600/3',
          orb1: 'bg-blue-400/8',
          orb2: 'bg-blue-300/5'
        }
      };
    case 'management':
      return {
        gradient: unifiedBackground,
        titleAccent: 'text-emerald-700 dark:text-emerald-300',
        icon: <Settings className="w-5 h-5" />,
        accentClasses: {
          iconBg: 'bg-emerald-500/10 border-emerald-200/50 dark:border-emerald-700/50',
          iconShadow: 'shadow-emerald-500/20',
          underline: 'from-emerald-500 to-emerald-600',
          overlay: 'from-emerald-500/3 via-transparent to-emerald-600/3',
          orb1: 'bg-emerald-400/8',
          orb2: 'bg-emerald-300/5'
        }
      };
    case 'analytics':
      return {
        gradient: unifiedBackground,
        titleAccent: 'text-purple-700 dark:text-purple-300',
        icon: <TrendingUp className="w-5 h-5" />,
        accentClasses: {
          iconBg: 'bg-purple-500/10 border-purple-200/50 dark:border-purple-700/50',
          iconShadow: 'shadow-purple-500/20',
          underline: 'from-purple-500 to-purple-600',
          overlay: 'from-purple-500/3 via-transparent to-purple-600/3',
          orb1: 'bg-purple-400/8',
          orb2: 'bg-purple-300/5'
        }
      };
    case 'settings':
      return {
        gradient: unifiedBackground,
        titleAccent: 'text-slate-700 dark:text-slate-300',
        icon: <Settings className="w-5 h-5" />,
        accentClasses: {
          iconBg: 'bg-slate-500/10 border-slate-200/50 dark:border-slate-700/50',
          iconShadow: 'shadow-slate-500/20',
          underline: 'from-slate-500 to-slate-600',
          overlay: 'from-slate-500/3 via-transparent to-slate-600/3',
          orb1: 'bg-slate-400/8',
          orb2: 'bg-slate-300/5'
        }
      };
    case 'profile':
      return {
        gradient: unifiedBackground,
        titleAccent: 'text-amber-700 dark:text-amber-300',
        icon: <User className="w-5 h-5" />,
        accentClasses: {
          iconBg: 'bg-amber-500/10 border-amber-200/50 dark:border-amber-700/50',
          iconShadow: 'shadow-amber-500/20',
          underline: 'from-amber-500 to-amber-600',
          overlay: 'from-amber-500/3 via-transparent to-amber-600/3',
          orb1: 'bg-amber-400/8',
          orb2: 'bg-amber-300/5'
        }
      };
    default:
      return {
        gradient: unifiedBackground,
        titleAccent: 'text-gray-700 dark:text-gray-300',
        icon: null,
        accentClasses: {
          iconBg: 'bg-gray-500/10 border-gray-200/50 dark:border-gray-700/50',
          iconShadow: 'shadow-gray-500/20',
          underline: 'from-gray-500 to-gray-600',
          overlay: 'from-gray-500/3 via-transparent to-gray-600/3',
          orb1: 'bg-gray-400/8',
          orb2: 'bg-gray-300/5'
        }
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
      <div className="mb-6">
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6 animate-pulse">
          <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-3">
                <div className="w-4 h-4 bg-gray-200 dark:bg-gray-700 rounded"></div>
                <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-32"></div>
              </div>
              <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded w-64 mb-3"></div>
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
    <div className="mb-6">
      <div className={`rounded-xl ${styles.gradient} p-8 relative`}>
        {/* Animated Background Elements */}
        <div className="absolute inset-0 rounded-xl">
          {/* Subtle animated gradient overlay */}
          <div className={`absolute inset-0 rounded-xl bg-gradient-to-r ${styles.accentClasses.overlay} animate-pulse`}></div>
          
          {/* Floating orb effects */}
          <div className={`absolute top-4 right-4 w-32 h-32 ${styles.accentClasses.orb1} rounded-full blur-3xl animate-pulse`}></div>
          <div className={`absolute bottom-4 left-4 w-24 h-24 ${styles.accentClasses.orb2} rounded-full blur-2xl animate-pulse delay-1000`}></div>
          
          {/* Subtle pattern overlay */}
          <div className="absolute inset-0 rounded-xl opacity-30 dark:opacity-10"
               style={{
                 backgroundImage: `radial-gradient(circle at 25% 25%, rgba(255,255,255,0.1) 1px, transparent 1px)`,
                 backgroundSize: '24px 24px'
               }}>
          </div>
        </div>

        {/* Content Container */}
        <div className="relative z-10">
          {/* Breadcrumbs */}
          <Breadcrumbs items={breadcrumbs} />

          <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
            <div className="flex-1 min-w-0">
              {/* Title Row with Status */}
              <div className="flex items-center gap-3 mb-2 flex-wrap">
                <div className="flex items-center gap-3">
                  {styles.icon && (
                    <div className={`p-3 rounded-xl bg-white/90 dark:bg-gray-800/90 ${styles.titleAccent} ${styles.accentClasses.iconBg} shadow-lg ${styles.accentClasses.iconShadow} backdrop-blur-sm border border-white/50 dark:border-gray-700/50`}>
                      {styles.icon}
                    </div>
                  )}
                  <div>
                    <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
                      {emoji && <span className="mr-2">{emoji}</span>}
                      {title}
                    </h1>
                    {/* Subtle accent line under title */}
                    <div className={`h-0.5 w-16 bg-gradient-to-r ${styles.accentClasses.underline} rounded-full mt-1`}></div>
                  </div>
                </div>
                {getStatusIndicator(status, statusText)}
              </div>

              {/* Description */}
              {description && (
                <p className="text-gray-600 dark:text-gray-300 max-w-3xl leading-relaxed text-base">
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
                <div className="flex flex-wrap gap-3">
                  {actions}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default PageHeader;