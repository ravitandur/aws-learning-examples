import React from 'react';
import BasketManagement from '../components/basket/BasketManagement';

const BasketsPage: React.FC = () => {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Baskets</h1>
      <BasketManagement />
    </div>
  );
};

export default BasketsPage;