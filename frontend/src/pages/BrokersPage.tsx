import React from 'react';
import StandardLayout from '../components/common/StandardLayout';
import PageHeader from '../components/common/PageHeader';
import BrokerAccountsList from '../components/broker/BrokerAccountsList';

const BrokersPage: React.FC = () => {
  return (
    <StandardLayout>
      <PageHeader 
        title="Broker Accounts" 
        emoji="🏦"
        description="Manage your trading accounts and API connections. Your credentials are stored securely and encrypted using AWS Secrets Manager."
      />
      <BrokerAccountsList />
    </StandardLayout>
  );
};

export default BrokersPage;