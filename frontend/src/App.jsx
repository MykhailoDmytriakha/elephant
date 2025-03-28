// src/App.jsx
import React from 'react';
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import MainPage from './pages/MainPage';
import TaskDetailsPage from './pages/TaskDetailsPage';
import StageDetailPage from './pages/StageDetailPage';
import AllStagesPage from './pages/AllStagesPage';
import ToastProvider from './components/common/ToastProvider';

const App = () => {
    return (
        <ToastProvider>
            <Router>
                <Routes>
                    <Route path="/" element={<MainPage />} />
                    <Route path="/tasks/:taskId" element={<TaskDetailsPage />} />
                    <Route path="/tasks/:taskId/stages/:stageId" element={<StageDetailPage />} />
                    <Route path="/tasks/:taskId/all-stages" element={<AllStagesPage />} />
                </Routes>
            </Router>
        </ToastProvider>
    );
};

export default App;