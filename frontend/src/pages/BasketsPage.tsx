import React, { useState } from 'react';
import StandardLayout from '../components/common/StandardLayout';
import PageHeader from '../components/common/PageHeader';
import TabbedBasketManager from '../components/basket/TabbedBasketManager';
import Button from '../components/ui/Button';
import { Plus, RefreshCw, Home, Package } from 'lucide-react';

const BasketsPage: React.FC = () => {
  const [refreshKey, setRefreshKey] = useState(0);
  
  const handleRefresh = () => {
    setRefreshKey(prev => prev + 1);
  };

  const actions = (
    <>
      <Button
        variant="outline"
        onClick={handleRefresh}
        leftIcon={<RefreshCw className="h-4 w-4" />}
        className="w-full sm:w-auto"
      >
        Refresh
      </Button>
      <Button
        leftIcon={<Plus className="h-4 w-4" />}
        onClick={() => {
          // This will be handled by the TabbedBasketManager
          const event = new CustomEvent('openCreateBasketDialog');
          window.dispatchEvent(event);
        }}
        className="w-full sm:w-auto"
      >
        Create Basket
      </Button>
    </>
  );

  return (
    <StandardLayout>
      <PageHeader 
        title="Basket Management" 
        description="Create and manage your strategy baskets with revolutionary multi-broker allocation and performance tracking."
        pageType="management"
        breadcrumbs={[
          { label: 'Home', href: '/', icon: <Home className="w-4 h-4" /> },
          { label: 'Basket Management', icon: <Package className="w-4 h-4" /> }
        ]}
        actions={actions}
      />
      <TabbedBasketManager key={refreshKey} />
    </StandardLayout>
  );
};

export default BasketsPage;