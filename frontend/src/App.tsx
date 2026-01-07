import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/Layout';
import MessagesPage from './pages/MessagesPage';
import SpecificationsPage from './pages/SpecificationsPage';
import IntentsPage from './pages/IntentsPage';
import ContradictionsPage from './pages/ContradictionsPage';
import DashboardPage from './pages/DashboardPage';
import ChoicePointsPage from './pages/ChoicePointsPage';
import MemoryPage from './pages/MemoryPage';
import TermDriftPage from './pages/TermDriftPage';
import TemporalConstraintPage from './pages/TemporalConstraintPage';
import FileModificationPage from './pages/FileModificationPage';

function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<Navigate to="/messages" replace />} />
          <Route path="/messages" element={<MessagesPage />} />
          <Route path="/specifications" element={<SpecificationsPage />} />
          <Route path="/intents" element={<IntentsPage />} />
          <Route path="/contradictions" element={<ContradictionsPage />} />
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/choice-points" element={<ChoicePointsPage />} />
          <Route path="/memory" element={<MemoryPage />} />
          <Route path="/term-drift" element={<TermDriftPage />} />
          <Route path="/temporal-constraint" element={<TemporalConstraintPage />} />
          <Route path="/files" element={<FileModificationPage />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  );
}

export default App;
