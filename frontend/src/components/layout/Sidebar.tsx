import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  BarChart3,
  Briefcase,
  Building2,
  LineChart,
  PieChart,
  Settings,
  ShoppingBasket,
  User,
  Turtle,
  X,
} from 'lucide-react';
import ThemeToggle from '../common/ThemeToggle';
import { cn } from '../../utils/cn';
import { useAuth } from '../../context/AuthContext';

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
}

interface NavItem {
  name: string;
  path: string;
  icon: React.ReactNode;
  disabled?: boolean;
}

const Sidebar: React.FC<SidebarProps> = ({ isOpen, onClose }) => {
  const { user } = useAuth();

  // Main navigation items
  const navItems: NavItem[] = [
    { name: 'Dashboard', path: '/', icon: <BarChart3 className="w-5 h-5" /> },
    { name: 'Brokers', path: '/brokers', icon: <Building2 className="w-5 h-5" /> },
    { name: 'Baskets', path: '/baskets', icon: <ShoppingBasket className="w-5 h-5" /> },
    { name: 'Strategies', path: '/strategies', icon: <LineChart className="w-5 h-5" />, disabled: true },
    { name: 'Portfolio', path: '/portfolio', icon: <Briefcase className="w-5 h-5" />, disabled: true },
    { name: 'Analytics', path: '/analytics', icon: <PieChart className="w-5 h-5" />, disabled: true },
  ];

  // Settings navigation items
  const secondaryNavItems: NavItem[] = [
    { name: 'Settings', path: '/settings', icon: <Settings className="w-5 h-5" /> },
    { name: 'Account', path: '/account', icon: <User className="w-5 h-5" /> },
  ];

  return (
    <>
      {/* Overlay for mobile */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 z-20 lg:hidden"
          onClick={onClose}
        />
      )}

      {/* Sidebar */}
      <aside
        className={cn(
          "fixed top-0 left-0 z-30 h-full w-64 bg-white dark:bg-gray-900 shadow-lg transform transition-transform duration-300 ease-in-out lg:translate-x-0",
          isOpen ? "translate-x-0" : "-translate-x-full"
        )}
      >
        <div className="flex flex-col h-full">
          {/* Logo */}
          <div className="flex items-center justify-between h-16 px-6 border-b border-gray-200 dark:border-gray-700">
            <div className="flex items-center">
              <Turtle className="h-8 w-8 text-blue-600" />
              <span className="ml-2 text-xl font-bold text-gray-900 dark:text-white">
                Quantleap
              </span>
            </div>
            <button
              onClick={onClose}
              className="lg:hidden text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
            >
              <X className="h-6 w-6" />
            </button>
          </div>

          {/* User info */}
          <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
            <div className="flex items-center">
              <div className="h-10 w-10 rounded-full bg-blue-600 flex items-center justify-center text-white">
                <User className="h-5 w-5" />
              </div>
              <div className="ml-3">
                <p className="text-sm font-medium text-gray-900 dark:text-white">
                  {user?.fullName || 'User'}
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  {user?.email || 'user@example.com'}
                </p>
              </div>
            </div>
          </div>

          {/* Navigation */}
          <nav className="flex-1 px-4 py-6 overflow-y-auto">
            {/* Main Navigation */}
            <ul className="space-y-1">
              {navItems.map((item) => (
                <li key={item.path}>
                  <NavLink
                    to={item.path}
                    className={({ isActive }) => cn(
                      "flex items-center px-4 py-2.5 text-sm font-medium rounded-md transition-colors",
                      item.disabled
                        ? "text-gray-400 cursor-not-allowed opacity-60"
                        : isActive
                        ? "bg-blue-50 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300"
                        : "text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-800"
                    )}
                    end={item.path === '/'}
                    onClick={item.disabled ? (e) => e.preventDefault() : undefined}
                  >
                    {item.icon}
                    <span className="ml-3">{item.name}</span>
                    {item.disabled && (
                      <span className="ml-auto text-xs bg-gray-100 dark:bg-gray-700 px-2 py-1 rounded-full">
                        Soon
                      </span>
                    )}
                  </NavLink>
                </li>
              ))}
            </ul>

            {/* Settings Section */}
            <div className="mt-6">
              <div className="px-4 mb-2">
                <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider">
                  Settings
                </p>
              </div>
              <ul className="space-y-1">
                {secondaryNavItems.map((item) => (
                  <li key={item.path}>
                    <NavLink
                      to={item.path}
                      className={({ isActive }) => cn(
                        "flex items-center px-4 py-2.5 text-sm font-medium rounded-md transition-colors",
                        isActive
                          ? "bg-blue-50 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300"
                          : "text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-800"
                      )}
                    >
                      {item.icon}
                      <span className="ml-3">{item.name}</span>
                    </NavLink>
                  </li>
                ))}
              </ul>
            </div>
          </nav>

          {/* Footer */}
          <div className="p-4 border-t border-gray-200 dark:border-gray-700">
            <div className="flex items-center justify-center">
              <ThemeToggle />
            </div>
          </div>
        </div>
      </aside>
    </>
  );
};

export default Sidebar;