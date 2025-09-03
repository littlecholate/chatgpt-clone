import ProtectedRoute from '@/context/ProtectedRoute';
import React from 'react';

const ProtectedLayout = ({ children }) => {
    return <ProtectedRoute>{children}</ProtectedRoute>;
};

export default ProtectedLayout;
