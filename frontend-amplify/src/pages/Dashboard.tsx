import React, { useState, useEffect } from 'react';
import Navigation from '../components/layout/Navigation';
import { Home, TrendingUp, Settings, LogOut } from 'lucide-react';
import brokerService from '../services/brokerService';
import type { BrokerAccount } from '../types';

interface DashboardProps {
  signOut?: () => void;
  user?: any;
}

const Dashboard: React.FC<DashboardProps> = ({ signOut, user }) => {
  const [brokerAccounts, setBrokerAccounts] = useState<BrokerAccount[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>('');

  const navigationItems = [
    { name: 'Dashboard', href: '/', icon: Home, current: true },
    { name: 'Broker Accounts', href: '/brokers', icon: TrendingUp, current: false },
    { name: 'Settings', href: '/settings', icon: Settings, current: false },
  ];

  useEffect(() => {
    const fetchBrokerAccounts = async () => {
      try {
        const accounts = await brokerService.getBrokerAccounts();
        setBrokerAccounts(accounts);
      } catch (err) {
        console.error('Error fetching broker accounts:', err);
        setError('Unable to load broker accounts');
      } finally {
        setLoading(false);
      }
    };

    fetchBrokerAccounts();
  }, []);

  return (
    <div className="min-h-screen bg-gray-50">
      <Navigation 
        navigationItems={navigationItems}
        user={user}
        onSignOut={signOut}
      />
      
      <div className="lg:pl-72">
        <div className="xl:pl-96">
          <div className="px-4 py-10 sm:px-6 lg:px-8 lg:py-6">
            {/* Header */}
            <div className="border-b border-gray-200 pb-5 mb-8">
              <h1 className="text-3xl font-bold leading-tight text-gray-900">
                Welcome to Quantleap Analytics
              </h1>
              <p className="mt-2 text-gray-600">
                AWS Amplify Gen 2 Implementation - Algorithmic Trading Platform
              </p>
            </div>

            {/* User Info */}
            <div className="bg-white overflow-hidden shadow rounded-lg mb-8">
              <div className="px-4 py-5 sm:p-6">
                <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
                  User Information
                </h3>
                <dl className="grid grid-cols-1 gap-x-4 gap-y-6 sm:grid-cols-2">
                  <div>
                    <dt className="text-sm font-medium text-gray-500">
                      Username
                    </dt>
                    <dd className="mt-1 text-sm text-gray-900">
                      {user?.username || 'N/A'}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-sm font-medium text-gray-500">
                      Email
                    </dt>
                    <dd className="mt-1 text-sm text-gray-900">
                      {user?.attributes?.email || 'N/A'}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-sm font-medium text-gray-500">
                      Full Name
                    </dt>
                    <dd className="mt-1 text-sm text-gray-900">
                      {user?.attributes?.name || user?.attributes?.full_name || 'N/A'}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-sm font-medium text-gray-500">
                      Phone Number
                    </dt>
                    <dd className="mt-1 text-sm text-gray-900">
                      {user?.attributes?.phone_number || 'N/A'}
                    </dd>
                  </div>
                </dl>
              </div>
            </div>

            {/* Quick Stats */}
            <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
              <div className="bg-white overflow-hidden shadow rounded-lg">
                <div className="p-5">
                  <div className="flex items-center">
                    <div className="flex-shrink-0">
                      <TrendingUp className="h-6 w-6 text-primary-600" />
                    </div>
                    <div className="ml-5 w-0 flex-1">
                      <dl>
                        <dt className="text-sm font-medium text-gray-500 truncate">
                          Broker Accounts
                        </dt>
                        <dd className="text-lg font-medium text-gray-900">
                          {loading ? '...' : brokerAccounts.length}
                        </dd>
                      </dl>
                    </div>
                  </div>
                </div>
              </div>

              <div className="bg-white overflow-hidden shadow rounded-lg">
                <div className="p-5">
                  <div className="flex items-center">
                    <div className="flex-shrink-0">
                      <Home className="h-6 w-6 text-primary-600" />
                    </div>
                    <div className="ml-5 w-0 flex-1">
                      <dl>
                        <dt className="text-sm font-medium text-gray-500 truncate">
                          Active Strategies
                        </dt>
                        <dd className="text-lg font-medium text-gray-900">
                          0
                        </dd>
                      </dl>
                    </div>
                  </div>
                </div>
              </div>

              <div className="bg-white overflow-hidden shadow rounded-lg">
                <div className="p-5">
                  <div className="flex items-center">
                    <div className="flex-shrink-0">
                      <Settings className="h-6 w-6 text-primary-600" />
                    </div>
                    <div className="ml-5 w-0 flex-1">
                      <dl>
                        <dt className="text-sm font-medium text-gray-500 truncate">
                          Total P&L
                        </dt>
                        <dd className="text-lg font-medium text-gray-900">
                          ₹0.00
                        </dd>
                      </dl>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Welcome Message */}
            <div className="bg-primary-50 border border-primary-200 rounded-lg p-6 mt-8">
              <div className="flex">
                <div className="flex-shrink-0">
                  <TrendingUp className="h-6 w-6 text-primary-600" />
                </div>
                <div className="ml-3">
                  <h3 className="text-lg font-medium text-primary-800">
                    Welcome to AWS Amplify Gen 2!
                  </h3>
                  <div className="mt-2 text-sm text-primary-700">
                    <p>
                      This is a comparison implementation using AWS Amplify Gen 2 with built-in authentication components.
                      The design matches our custom frontend while using Amplify's pre-built authenticator.
                    </p>
                  </div>
                  <div className="mt-4">
                    <button
                      onClick={signOut}
                      className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
                    >
                      <LogOut className="w-4 h-4 mr-2" />
                      Sign Out
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;