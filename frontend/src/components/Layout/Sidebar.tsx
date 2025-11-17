import { MessageSquare, FileText, Target } from 'lucide-react';
import { NavLink } from 'react-router-dom';

export default function Sidebar() {
  const navItems = [
    { to: '/messages', icon: MessageSquare, label: 'Messages' },
    { to: '/specifications', icon: FileText, label: 'Specifications' },
    { to: '/intents', icon: Target, label: 'Intents' },
  ];

  return (
    <aside className="w-64 bg-gray-800 text-white p-4 min-h-screen">
      <h1 className="text-xl font-bold mb-6">Resonant Dashboard</h1>
      <nav className="space-y-2">
        {navItems.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              `flex items-center p-3 rounded transition-colors ${
                isActive ? 'bg-gray-700' : 'hover:bg-gray-700'
              }`
            }
          >
            <Icon className="mr-3 h-5 w-5" />
            {label}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}
