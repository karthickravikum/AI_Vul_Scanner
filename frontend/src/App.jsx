/**
 * App.jsx
 * -------
 * Root component. Sets up React Router with three routes:
 *   /          → Home (landing page)
 *   /dashboard → Dashboard (scan interface)
 *   /report/:id → Report (full vulnerability report)
 *
 * The Navbar is rendered on every page via the layout wrapper.
 */

import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Navbar from './components/Navbar'
import Home from './pages/Home'
import Dashboard from './pages/Dashboard'
import Report from './pages/Report'

export default function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-bg text-white font-body">
        <Navbar />
        <Routes>
          <Route path="/"            element={<Home />} />
          <Route path="/dashboard"   element={<Dashboard />} />
          <Route path="/report/:id"  element={<Report />} />
        </Routes>
      </div>
    </BrowserRouter>
  )
}
