import { Routes, Route, Link, useLocation } from 'react-router-dom';
import { Shield } from 'lucide-react';
import ConsumerAlert from './pages/ConsumerAlert';
import AnalystDashboard from './pages/AnalystDashboard';

function App() {
  const location = useLocation();

  return (
    <div className="min-h-screen flex flex-col">
      <nav className="sticky top-0 z-50 glass-nav border-b border-white/10 px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <Link to="/" className="flex items-center space-x-2 text-electric-blue">
            <Shield className="w-8 h-8" />
            <span className="text-xl font-bold tracking-wider text-white">VoxShield</span>
          </Link>
          <div className="flex space-x-6">
            <Link 
              to="/" 
              className={`text-sm font-medium transition-colors ${
                location.pathname === '/' ? 'text-electric-blue' : 'text-gray-400 hover:text-white'
              }`}
            >
              Consumer Alert
            </Link>
            <Link 
              to="/dashboard" 
              className={`text-sm font-medium transition-colors ${
                location.pathname === '/dashboard' ? 'text-electric-blue' : 'text-gray-400 hover:text-white'
              }`}
            >
              Analyst Dashboard
            </Link>
          </div>
        </div>
      </nav>

      <main className="flex-1 max-w-7xl w-full mx-auto p-6">
        <Routes>
          <Route path="/" element={<ConsumerAlert />} />
          <Route path="/dashboard" element={<AnalystDashboard />} />
        </Routes>
      </main>
    </div>
  );
}

export default App;
