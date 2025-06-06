import React from 'react';

export const Toaster: React.FC = () => {
  return (
    <div className="fixed bottom-4 right-4 z-50" id="toaster">
      {/* Toast notifications will be rendered here */}
    </div>
  );
};