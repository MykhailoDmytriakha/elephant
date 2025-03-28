// frontend/src/components/query/CreateQueryModal.jsx
import React, { useState, useEffect, useRef } from 'react';
import Modal from 'react-modal';
import { X, Loader2, Send, Maximize2, Minimize2 } from 'lucide-react';
import { useToast } from '../common/ToastProvider';
import { createQuery } from '../../utils/api';

Modal.setAppElement('#root');

const CreateQueryModal = ({ isOpen, onRequestClose, onQueryCreated }) => {
    const [query, setQuery] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [charCount, setCharCount] = useState(0);
    const [isExpanded, setIsExpanded] = useState(false);
    const textareaRef = useRef(null);
    const toast = useToast();
    
    // Reset form when modal is opened
    useEffect(() => {
        if (isOpen) {
            setQuery('');
            setError('');
            setIsExpanded(false);
        }
    }, [isOpen]);
    
    // Update character count when query changes
    useEffect(() => {
        setCharCount(query.length);
    }, [query]);

    const toggleExpand = () => {
        setIsExpanded(!isExpanded);
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        
        if (!query.trim()) {
            setError('Please enter a query');
            toast.showError('Please enter a query');
            return;
        }
        
        setLoading(true);
        setError('');
        try {
            const response = await createQuery(query);
            onQueryCreated(response);
            toast.showSuccess('Task created successfully');
            setQuery('');
            onRequestClose();
        } catch (err) {
            const errorMessage = err.message || 'Failed to create task';
            setError(errorMessage);
            toast.showError(errorMessage);
        } finally {
            setLoading(false);
        }
    };

    return (
        <Modal
            isOpen={isOpen}
            onRequestClose={loading ? null : onRequestClose}
            contentLabel="Create New Query"
            className={`
                absolute bg-white rounded-xl shadow-xl outline-none
                ${isExpanded 
                    ? 'inset-4 md:inset-8 lg:inset-12' 
                    : 'top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-[95%] max-h-[90vh] md:w-[85%] md:max-w-2xl'
                }
                overflow-hidden flex flex-col
            `}
            overlayClassName="fixed inset-0 bg-black bg-opacity-50 z-50 overflow-y-auto p-2 md:p-4 flex items-center justify-center"
        >
            <div className="flex flex-col h-full max-h-[90vh]">
                <div className="flex items-center justify-between px-4 md:px-6 py-3 md:py-4 border-b border-gray-200">
                    <h2 className="text-lg md:text-xl font-bold text-gray-900 truncate">Create New Query</h2>
                    <div className="flex items-center gap-2">
                        <button
                            type="button"
                            onClick={toggleExpand}
                            className="text-gray-400 hover:text-gray-600 focus:outline-none p-1 rounded-md hover:bg-gray-100"
                            aria-label={isExpanded ? "Minimize" : "Maximize"}
                            title={isExpanded ? "Minimize editor" : "Maximize editor"}
                        >
                            {isExpanded ? (
                                <Minimize2 className="w-5 h-5" />
                            ) : (
                                <Maximize2 className="w-5 h-5" />
                            )}
                        </button>
                        <button
                            type="button"
                            onClick={loading ? null : onRequestClose}
                            disabled={loading}
                            className="text-gray-400 hover:text-gray-600 focus:outline-none disabled:opacity-50 p-1 rounded-md hover:bg-gray-100"
                            aria-label="Close"
                        >
                            <X className="w-5 h-5" />
                        </button>
                    </div>
                </div>
                
                <form onSubmit={handleSubmit} className="flex flex-col flex-grow overflow-hidden p-4 md:p-6">
                    <div className="mb-2 flex flex-wrap justify-between items-center gap-2">
                        <label htmlFor="query-input" className="block text-sm font-medium text-gray-700">
                            Query Text
                        </label>
                        <div className="text-xs text-gray-500">
                            <span>{charCount > 0 ? `${charCount} characters` : 'Enter your query'}</span>
                            {charCount > 500 && <span className="ml-2 text-yellow-600">Query is quite long</span>}
                        </div>
                    </div>
                    
                    <div className="relative flex-grow min-h-[150px] mb-4 overflow-hidden">
                        <textarea
                            id="query-input"
                            ref={textareaRef}
                            value={query}
                            onChange={(e) => setQuery(e.target.value)}
                            placeholder="Enter your query here..."
                            required
                            disabled={loading}
                            className="w-full h-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-50 disabled:text-gray-500 resize-none"
                            style={{ minHeight: isExpanded ? '30vh' : '150px' }}
                        ></textarea>
                        {!isExpanded && (
                            <button
                                type="button"
                                onClick={toggleExpand}
                                className="absolute bottom-2 right-2 p-1 bg-gray-100 rounded-md hover:bg-gray-200 text-gray-600"
                                title="Expand editor"
                            >
                                <Maximize2 className="w-4 h-4" />
                            </button>
                        )}
                    </div>
                    
                    {error && (
                        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
                            {error}
                        </div>
                    )}
                    
                    <div className="flex flex-wrap justify-end gap-3 mt-auto">
                        <button
                            type="button"
                            onClick={onRequestClose}
                            disabled={loading}
                            className="px-4 py-2 text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors disabled:opacity-50"
                        >
                            Cancel
                        </button>
                        <button
                            type="submit"
                            disabled={loading || !query.trim()}
                            className="flex items-center gap-2 px-5 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:bg-blue-300"
                        >
                            {loading ? (
                                <>
                                    <Loader2 className="w-4 h-4 animate-spin" />
                                    Creating...
                                </>
                            ) : (
                                <>
                                    <Send className="w-4 h-4" />
                                    Create Query
                                </>
                            )}
                        </button>
                    </div>
                </form>
            </div>
        </Modal>
    );
};

export default CreateQueryModal;
