import React from 'react';
import BrokerAccountsList from '../components/broker/BrokerAccountsList';

const BrokersPage: React.FC = () => {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
          Broker Accounts
        </h1>
        <p className="text-gray-600 dark:text-gray-300">
          Manage your trading accounts and API connections. Your credentials are stored securely
          and encrypted using AWS Secrets Manager.
        </p>
      </div>

      <BrokerAccountsList />
    </div>
  );
};

export default BrokersPage;