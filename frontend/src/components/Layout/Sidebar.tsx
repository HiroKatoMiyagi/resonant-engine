import { MessageSquare, FileText, Target, AlertTriangle } from 'lucide-react';
import { NavLink } from 'react-router-dom';

export default function Sidebar() {
  const navItems = [
    { to: '/messages', icon: MessageSquare, label: 'メッセージ' },
    { to: '/specifications', icon: FileText, label: '仕様書' },
    { to: '/intents', icon: Target, label: '意図' },
    { to: '/contradictions', icon: AlertTriangle, label: '矛盾検出' },
    // 🆕 Sprint 13 Additions
    { to: '/dashboard', icon: AlertTriangle, label: 'Dashboard' }, // icon placeholder
    { to: '/choice-points', icon: Target, label: 'Choice Points' }, // icon placeholder
    { to: '/memory', icon: FileText, label: 'Memory' }, // icon placeholder
    { to: '/term-drift', icon: AlertTriangle, label: 'Term Drift' }, // icon placeholder
    { to: '/temporal-constraint', icon: FileText, label: 'Constraints' }, // icon placeholder
    { to: '/files', icon: FileText, label: 'Files' }, // icon placeholder
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
              `flex items-center p-3 rounded transition-colors ${isActive ? 'bg-gray-700' : 'hover:bg-gray-700'
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
