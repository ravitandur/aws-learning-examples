import React from 'react';
import { 
  BarChart3, 
  Building2, 
  Settings, 
  User, 
  Turtle, 
  LogOut
} from 'lucide-react';

interface NavigationItem {
  name: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
  current: boolean;
}

interface NavigationProps {
  navigationItems: NavigationItem[];
  user?: any;
  onSignOut?: () => void;
}

const Navigation: React.FC<NavigationProps> = ({ 
  navigationItems, 
  user, 
  onSignOut 
}) => {
  return (
    <div className="fixed inset-y-0 left-0 z-50 w-72 bg-white shadow-lg">
      <div className="flex flex-col h-full">
        {/* Logo */}
        <div className="flex items-center h-16 px-6 border-b border-gray-200">
          <div className="flex items-center">
            <Turtle className="h-8 w-8 text-blue-600" />
            <span className="ml-2 text-xl font-bold text-gray-900">
              Quantleap
            </span>
          </div>
          <div className="ml-auto text-xs bg-green-100 text-green-800 px-2 py-1 rounded-full">
            Amplify Gen2
          </div>
        </div>

        {/* User info */}
        <div className="px-6 py-4 border-b border-gray-200">
          <div className="flex items-center">
            <div className="h-10 w-10 rounded-full bg-blue-600 flex items-center justify-center text-white">
              <User className="h-5 w-5" />
            </div>
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-900">
                {user?.attributes?.name || user?.attributes?.full_name || 'User'}
              </p>
              <p className="text-xs text-gray-500">
                {user?.attributes?.email || 'user@example.com'}
              </p>
            </div>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-4 py-6 overflow-y-auto">
          <ul className="space-y-1">
            {navigationItems.map((item) => {
              const IconComponent = item.icon;
              return (
                <li key={item.name}>
                  <a
                    href={item.href}
                    className={`
                      flex items-center px-4 py-2.5 text-sm font-medium rounded-md transition-colors
                      ${item.current
                        ? 'bg-blue-50 text-blue-700'
                        : 'text-gray-700 hover:bg-gray-100'
                      }
                    `}
                  >
                    <IconComponent className="w-5 h-5" />
                    <span className="ml-3">{item.name}</span>
                  </a>
                </li>
              );
            })}
          </ul>
        </nav>

        {/* Sign Out */}
        <div className="p-4 border-t border-gray-200">
          <button
            onClick={onSignOut}
            className="flex w-full items-center px-4 py-2.5 text-sm font-medium text-red-600 hover:bg-red-50 rounded-md transition-colors"
          >
            <LogOut className="w-5 h-5" />
            <span className="ml-3">Sign Out</span>
          </button>
        </div>
      </div>
    </div>
  );
};

export default Navigation;