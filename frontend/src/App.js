import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';

// Import pages to link
import HomePage from './pages/Home';
import Setup from './pages/Setup';
import CollectionsPage from './pages/Collections';
import CollectionPage from './pages/Collection';
import UsagePage from './pages/Usage';

const App = () => {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/create" element={<Setup />} />
        <Route path="/collections" element={<CollectionsPage />} />
        <Route path="/collections/:id" element={<CollectionPage />} />
        <Route path="/usage" element={<UsagePage />} />
      </Routes>
    </Router>
  );
};

export default App;
