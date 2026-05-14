/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ErrorBoundary } from '@/src/components/ErrorBoundary';
import { Navigation } from '@/src/components/Navigation';
import LandingPage from '@/src/pages/LandingPage';
import Dashboard from '@/src/pages/Dashboard';
import Analytics from '@/src/pages/Analytics';
import Compare from '@/src/pages/Compare';
import NationalMap from '@/src/pages/NationPage';
import HealthAlerts from '@/src/pages/HealthAlert';

export default function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen flex flex-col">
        <Navigation />
        <main className="flex-1">
          <ErrorBoundary>
            <Routes>
              <Route path="/" element={<LandingPage />} />
              <Route path="/dashboard" element={<Dashboard />} />
              <Route path="/analytics" element={<Analytics />} />
              <Route path="/compare" element={<Compare />} />
              <Route path="/map" element={<NationalMap />} />
              <Route path="/alerts" element={<HealthAlerts />} />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </ErrorBoundary>
        </main>
      </div>
    </BrowserRouter>
  );
}
