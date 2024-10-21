// frontend/src/components/CreateQueryModal.jsx
import React, { useState } from 'react';
import Modal from 'react-modal';
import axios from 'axios';
import './CreateQueryModal.css';

Modal.setAppElement('#root');

const CreateQueryModal = ({ isOpen, onRequestClose, onQueryCreated }) => {
    const [query, setQuery] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError('');
        try {
            const response = await axios.post('http://localhost:8000/user-queries/', {
                query
            });
            onQueryCreated(response.data);
            setQuery('');
            onRequestClose();
        } catch (err) {
            setError('Не удалось создать запрос. Попробуйте снова.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <Modal
            isOpen={isOpen}
            onRequestClose={onRequestClose}
            contentLabel="Создать Новый Запрос"
            className="modal"
            overlayClassName="overlay"
        >
            <h2>Создать Новый Запрос</h2>
            <form onSubmit={handleSubmit}>
                <textarea
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    placeholder="Введите ваш запрос..."
                    required
                ></textarea>
                {error && <p className="error">{error}</p>}
                <div className="modal-buttons">
                    <button type="submit" disabled={loading}>
                        {loading ? 'Создание...' : 'Создать'}
                    </button>
                    <button type="button" onClick={onRequestClose}>Отмена</button>
                </div>
            </form>
        </Modal>
    );
};

export default CreateQueryModal;