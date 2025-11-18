import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ConfigProvider } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import ErrorBoundary from './components/ErrorBoundary';
import TopicsPage from './pages/Topics';
import TopicWorkspace from './pages/TopicWorkspace';
import { antdTheme } from './theme/antd';
import './App.css';

function App() {
  return (
    <ErrorBoundary>
      <ConfigProvider 
        locale={zhCN}
        theme={antdTheme}
      >
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<TopicsPage />} />
            <Route path="/topics/:id" element={<TopicWorkspace />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </BrowserRouter>
      </ConfigProvider>
    </ErrorBoundary>
  );
}

export default App;

