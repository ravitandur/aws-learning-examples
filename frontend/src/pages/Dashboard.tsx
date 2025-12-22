import React, { useState, useEffect } from 'react';
import {
  Building2,
  TrendingUp,
  User,
  Plus,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { formatPhoneNumber } from '../utils/validation';
import brokerService from '../services/brokerService';
import StandardLayout from '../components/common/StandardLayout';
import PageHeader from '../components/common/PageHeader';
import { Home } from 'lucide-react';
import Button from '../components/ui/Button';

const Dashboard: React.FC = () => {
  const { user } = useAuth();
  const [brokerAccountCount, setBrokerAccountCount] = useState<number>(0);

  useEffect(() => {
    const fetchBrokerAccounts = async () => {
      try {
        const accounts = await brokerService.getBrokerAccounts();
        setBrokerAccountCount(accounts.length);
      } catch (error) {
        console.error('Failed to fetch broker accounts for dashboard:', error);
        setBrokerAccountCount(0);
      }
    };

    fetchBrokerAccounts();
  }, []);

  const quickStats = [
    {
      title: 'Broker Accounts',
      value: brokerAccountCount.toString(),
      subtitle: 'Connected accounts',
      icon: <Building2 className="w-10 h-10" />,
      color: 'text-blue-600',
      bgColor: 'bg-blue-50 dark:bg-blue-900/20',
    },
    {
      title: 'Active Strategies',
      value: '0', // TODO: Implement in future modules
      subtitle: 'Running algorithms',
      icon: <TrendingUp className="w-10 h-10" />,
      color: 'text-green-600',
      bgColor: 'bg-green-50 dark:bg-green-900/20',
    },
    {
      title: 'P&L Today',
      value: '₹0.00', // TODO: Implement in future modules
      subtitle: 'Trading profit/loss',
      icon: <TrendingUp className="w-10 h-10" />,
      color: 'text-orange-600',
      bgColor: 'bg-orange-50 dark:bg-orange-900/20',
    },
  ];

  const getWelcomeMessage = () => {
    const hour = new Date().getHours();
    if (hour < 12) return 'Good morning';
    if (hour < 17) return 'Good afternoon';
    return 'Good evening';
  };

  const actions = (
    <Button
      onClick={() => window.location.href = '/brokers'}
      leftIcon={<Plus className="h-4 w-4" />}
      className="w-full sm:w-auto"
    >
      Connect Broker Account
    </Button>
  );

  return (
    <StandardLayout>
      <PageHeader 
        title={`${getWelcomeMessage()}, ${user?.fullName?.split(' ')[0]}!`}
        description="Welcome to your algorithmic trading dashboard. Monitor your strategies, manage broker accounts, and track performance."
        pageType="dashboard"
        status="active"
        statusText={`${brokerAccountCount} broker accounts connected`}
        breadcrumbs={[
          { label: 'Home', icon: <Home className="w-4 h-4" /> }
        ]}
        actions={actions}
      />

      {/* User Profile Summary */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
        <div className="flex items-center mb-4">
          <User className="w-5 h-5 text-blue-600 mr-2" />
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Profile Summary</h2>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <p className="text-sm text-gray-500 dark:text-gray-400">Full Name</p>
            <p className="text-gray-900 dark:text-white">{user?.fullName}</p>
          </div>
          <div>
            <p className="text-sm text-gray-500 dark:text-gray-400">Email</p>
            <p className="text-gray-900 dark:text-white">{user?.email}</p>
          </div>
          <div>
            <p className="text-sm text-gray-500 dark:text-gray-400">Phone Number</p>
            <p className="text-gray-900 dark:text-white">
              {user?.phoneNumber && formatPhoneNumber(user.phoneNumber)}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-500 dark:text-gray-400">State</p>
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200">
              {user?.state}
            </span>
          </div>
        </div>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {quickStats.map((stat, index) => (
          <div key={index} className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-3xl font-bold text-gray-900 dark:text-white mb-1">
                  {stat.value}
                </p>
                <p className="text-lg font-medium text-gray-700 dark:text-gray-200">
                  {stat.title}
                </p>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  {stat.subtitle}
                </p>
              </div>
              <div className={`${stat.bgColor} ${stat.color} p-3 rounded-lg`}>
                {stat.icon}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Getting Started Section */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Getting Started
        </h2>
        
        <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4 mb-6">
          <p className="text-sm text-blue-800 dark:text-blue-200">
            <strong>Welcome to Quantleap Analytics!</strong> You've successfully set up your account. 
            Now let's connect your broker account to start algorithmic trading.
          </p>
        </div>

        <div>
          <p className="text-gray-900 dark:text-white font-medium mb-3">
            <strong>Next Steps:</strong>
          </p>
          <ol className="list-decimal list-inside space-y-2 mb-6 text-gray-700 dark:text-gray-300">
            <li>
              Connect your Zerodha account to enable trading
            </li>
            <li>
              Test your broker connection to ensure everything works
            </li>
            <li className="text-gray-500 dark:text-gray-400">
              Set up your first trading strategy (Module 3 - Coming soon)
            </li>
            <li className="text-gray-500 dark:text-gray-400">
              Monitor and optimize your portfolio (Module 4 - Coming soon)
            </li>
          </ol>

          <Button
            onClick={() => window.location.href = '/brokers'}
            leftIcon={<Plus className="h-4 w-4" />}
          >
            Connect Broker Account
          </Button>
        </div>
      </div>
    </StandardLayout>
  );
};

export default Dashboard; 