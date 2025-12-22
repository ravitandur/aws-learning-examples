import React from 'react';

interface StandardLayoutProps {
  children: React.ReactNode;
  className?: string;
}

/**
 * Standard page layout wrapper that ensures consistent spacing
 * and follows the design system patterns used across the application.
 * 
 * Usage:
 * <StandardLayout>
 *   <PageHeader title="Page Title" />
 *   <Card>Content...</Card>
 *   <Card>More content...</Card>
 * </StandardLayout>
 */
const StandardLayout: React.FC<StandardLayoutProps> = ({ 
  children, 
  className = "" 
}) => {
  return (
    <div className={`space-y-4 ${className}`}>
      {children}
    </div>
  );
};

export default StandardLayout;