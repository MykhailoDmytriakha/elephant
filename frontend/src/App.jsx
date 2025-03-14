// src/App.jsx
import React from 'react';
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import MainPage from './pages/MainPage';
import TaskDetailsPage from './pages/TaskDetailsPage';
import ToastProvider from './components/common/ToastProvider';

const App = () => {
    return (
        <ToastProvider>
            <Router>
                <Routes>
                    <Route path="/" element={<MainPage />} />
                    <Route path="/tasks/:taskId" element={<TaskDetailsPage />} />
                    {/* Add more routes here as needed */}
                </Routes>
            </Router>
        </ToastProvider>
    );
};

export default App;
