import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Home from './pages/Home';
import Map from './pages/Map';
import Upload from './pages/Upload';
import ParcelDetail from './pages/ParcelDetail';
import Navbar from './components/Navbar';
import Footer from './components/Footer';
import './App.css';

function App() {
  return (
    <Router>
      <div className="flex flex-col min-h-screen">
        <Navbar />
        <main className="flex-grow">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/map" element={<Map />} />
            <Route path="/upload" element={<Upload />} />
            <Route path="/parcel/:id" element={<ParcelDetail />} />
            {/* La route /faq peut renvoyer vers la carte ou une page d'information */} 
          </Routes>
        </main>
        <Footer />
      </div>
    </Router>
  );
}

export default App;