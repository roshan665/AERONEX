import React, { useState } from 'react';
import Sidebar from './Sidebar';
import TopHeader from './TopHeader';

export default function AppLayout({ 
  children, 
  activeNav, 
  setActiveNav,
  searchQuery, 
  setSearchQuery, 
  onSelectEvent, 
  filteredEvents = [],
  anomalyCount = 5,
  dataMode = 'DEMO_DATA',
  dataProvenance,
  onDataModeChange,
  onIngestionSuccess,
  onResetDemo,
  backendOnline = true,
  onRetryBackend,
}) {
  const [isMobileSidebarOpen, setIsMobileSidebarOpen] = useState(false);

  return (
    <div className="min-h-screen bg-[#050B1A] text-[#F4F7FF] flex flex-col lg:flex-row antialiased">
      {/* Persistent Left Sidebar */}
      <Sidebar 
        activeNav={activeNav}
        setActiveNav={setActiveNav}
        isMobileOpen={isMobileSidebarOpen}
        setIsMobileOpen={setIsMobileSidebarOpen}
        anomalyCount={anomalyCount}
      />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Top Header */}
        <TopHeader 
          searchQuery={searchQuery}
          setSearchQuery={setSearchQuery}
          onSelectEvent={onSelectEvent}
          filteredEvents={filteredEvents}
          onToggleMobileSidebar={() => setIsMobileSidebarOpen(prev => !prev)}
          dataMode={dataMode}
          dataProvenance={dataProvenance}
          onDataModeChange={onDataModeChange}
          onIngestionSuccess={onIngestionSuccess}
          onResetDemo={onResetDemo}
          backendOnline={backendOnline}
          onRetryBackend={onRetryBackend}
        />

        {/* Dynamic Page Body */}
        <main className="flex-1 p-3.5 sm:p-4 lg:p-5 overflow-y-auto max-w-[1720px] mx-auto w-full">
          {children}
        </main>
      </div>
    </div>
  );
}
