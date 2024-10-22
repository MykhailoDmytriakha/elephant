// src/App.jsx
import React from 'react';
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import MainPage from './pages/MainPage';
import TaskDetailsPage from './pages/TaskDetailsPage';

const App = () => {
    return (
        <Router>
            <Routes>
                <Route path="/" element={<MainPage />} />
                <Route path="/tasks/:taskId" element={<TaskDetailsPage />} />
                {/* Add more routes here as needed */}
            </Routes>
        </Router>
    );
};

export default App;
