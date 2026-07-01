import { useState } from 'react';
import Sidebar from './components/Sidebar';
import MarketOverview from './pages/MarketOverview';
import Charts from './pages/Charts';
import Sentiment from './pages/Sentiment';
import Strategy from './pages/Strategy';
import PaperTrading from './pages/PaperTrading';
import About from './pages/About';

const PAGES = {
  overview: MarketOverview,
  charts: Charts,
  sentiment: Sentiment,
  strategy: Strategy,
  trading: PaperTrading,
  about: About,
};

export default function App() {
  const [page, setPage] = useState('overview');
  const PageComponent = PAGES[page] || MarketOverview;

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar activePage={page} onNavigate={setPage} />
      <main className="flex-1 overflow-y-auto bg-bg">
        <PageComponent />
      </main>
    </div>
  );
}
