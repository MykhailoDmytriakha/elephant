// src/pages/MainPage.jsx
import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import QueryList from '../components/QueryList';
import CreateQueryModal from '../components/CreateQueryModal';

const MainPage = () => {
    const [queries, setQueries] = useState([]);
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const navigate = useNavigate();

    const fetchQueries = async () => {
        try {
            const response = await axios.get('http://localhost:8000/user-queries/');
            setQueries(response.data);
        } catch (err) {
            setError('Failed to load queries.');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchQueries();
    }, []);

    const handleQueryCreated = async (newQuery) => {
        setQueries([newQuery, ...queries]);
        await fetchQueries(); // Reload queries after creating a new one
    };

    const handleDetailsClick = (taskId) => {
        navigate(`/tasks/${taskId}`);
    };

    return (
        <div className="min-h-screen bg-gray-50 py-8">
            {loading ? (
                <div className="flex justify-center items-center h-64">
                    <p className="text-gray-500">Loading...</p>
                </div>
            ) : error ? (
                <div className="max-w-3xl mx-auto px-4">
                    <p className="text-red-500">{error}</p>
                </div>
            ) : (
                <QueryList 
                    queries={queries}
                    onCreateClick={() => setIsModalOpen(true)}
                    onDetailsClick={handleDetailsClick}
                />
            )}

            <CreateQueryModal
                isOpen={isModalOpen}
                onRequestClose={() => setIsModalOpen(false)}
                onQueryCreated={handleQueryCreated}
            />
        </div>
    );
};

export default MainPage;
