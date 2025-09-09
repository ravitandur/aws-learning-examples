import React from 'react';
import StandardLayout from '../components/common/StandardLayout';
import PageHeader from '../components/common/PageHeader';
import { Home, Settings } from 'lucide-react';
import BrokerAccountsList from '../components/broker/BrokerAccountsList';

const BrokersPage: React.FC = () => {
  return (
    <StandardLayout>
      <PageHeader 
        title="Broker Accounts" 
        emoji="🏦"
        description="Manage your trading accounts and API connections. Your credentials are stored securely and encrypted using AWS Secrets Manager."
        pageType="management"
        breadcrumbs={[
          { label: 'Home', href: '/', icon: <Home className="w-4 h-4" /> },
          { label: 'Broker Management', icon: <Settings className="w-4 h-4" /> }
        ]}
      />
      <BrokerAccountsList />
    </StandardLayout>
  );
};

export default BrokersPage;