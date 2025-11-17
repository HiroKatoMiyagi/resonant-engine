import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/Layout';
import MessagesPage from './pages/MessagesPage';
import SpecificationsPage from './pages/SpecificationsPage';
import IntentsPage from './pages/IntentsPage';

function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<Navigate to="/messages" replace />} />
          <Route path="/messages" element={<MessagesPage />} />
          <Route path="/specifications" element={<SpecificationsPage />} />
          <Route path="/intents" element={<IntentsPage />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  );
}

export default App;
