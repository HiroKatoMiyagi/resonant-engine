import { ReactNode } from 'react';
import Sidebar from './Sidebar';
import NotificationBell from '../Notifications/NotificationBell';
import { WebSocketStatus } from '../WebSocketStatus';

interface LayoutProps {
  children: ReactNode;
}

export default function Layout({ children }: LayoutProps) {
  return (
    <div className="flex min-h-screen bg-gray-100">
      <Sidebar />
      <div className="flex-1 flex flex-col">
        <header className="bg-white shadow-sm p-4 flex justify-between items-center">
          <WebSocketStatus />
          <NotificationBell />
        </header>
        <main className="flex-1 p-6">{children}</main>
      </div>
    </div>
  );
}
