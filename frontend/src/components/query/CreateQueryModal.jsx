// frontend/src/components/CreateQueryModal.jsx
import React, { useState } from 'react';
import Modal from 'react-modal';
import axios from 'axios';

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
            setError('Failed to create query. Please try again.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <Modal
            isOpen={isOpen}
            onRequestClose={onRequestClose}
            contentLabel="Create New Query"
            className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 bg-white p-6 rounded-lg shadow-lg w-full max-w-md"
            overlayClassName="fixed inset-0 bg-black bg-opacity-50"
        >
            <h2 className="text-xl font-bold mb-4">Create New Query</h2>
            <form onSubmit={handleSubmit}>
                <textarea
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    placeholder="Enter your query..."
                    required
                    className="w-full h-32 p-2 border rounded mb-4 resize-y"
                ></textarea>
                {error && <p className="text-red-500 mb-4">{error}</p>}
                <div className="flex justify-end gap-2">
                    <button
                        type="submit"
                        disabled={loading}
                        className="bg-green-500 text-white px-4 py-2 rounded hover:bg-green-600 disabled:bg-green-300"
                    >
                        {loading ? 'Creating...' : 'Create'}
                    </button>
                    <button
                        type="button"
                        onClick={onRequestClose}
                        className="bg-gray-500 text-white px-4 py-2 rounded hover:bg-gray-600"
                    >
                        Cancel
                    </button>
                </div>
            </form>
        </Modal>
    );
};

export default CreateQueryModal;
