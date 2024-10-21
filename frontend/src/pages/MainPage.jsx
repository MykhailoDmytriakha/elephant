// frontend/src/pages/MainPage.jsx
import React, { useState, useEffect } from 'react';
import axios from 'axios';
import QueryCard from '../components/QueryCard';
import CreateQueryModal from '../components/CreateQueryModal';
import './MainPage.css';

const MainPage = () => {
    const [queries, setQueries] = useState([]);
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    const fetchQueries = async () => {
        try {
            const response = await axios.get('http://localhost:8000/user-queries/');
            setQueries(response.data);
        } catch (err) {
            setError('Не удалось загрузить запросы.');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchQueries();
    }, []);

    const handleQueryCreated = (newQuery) => {
        setQueries([newQuery, ...queries]);
    };

    return (
        <div className="main-page">
            <header className="header">
                <h1>Все Запросы</h1>
                <button className="create-button" onClick={() => setIsModalOpen(true)}>
                    Создать новый запрос
                </button>
            </header>

            {loading ? (
                <p>Загрузка...</p>
            ) : error ? (
                <p className="error">{error}</p>
            ) : (
                <div className="queries-list">
                    {queries.map(query => (
                        <QueryCard key={query.id} query={query} />
                    ))}
                </div>
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