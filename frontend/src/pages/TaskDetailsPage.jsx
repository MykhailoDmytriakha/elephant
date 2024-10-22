import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import axios from 'axios';

const TaskDetailsPage = () => {
    const { taskId } = useParams();
    const [task, setTask] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    useEffect(() => {
        const fetchTaskDetails = async () => {
            try {
                const response = await axios.get(`http://localhost:8000/tasks/${taskId}/`);
                setTask(response.data);
            } catch (err) {
                setError('Не удалось загрузить детали задачи.');
            } finally {
                setLoading(false);
            }
        };

        fetchTaskDetails();
    }, [taskId]);

    if (loading) {
        return <div className="flex justify-center items-center h-screen">Загрузка...</div>;
    }

    if (error) {
        return <div className="text-red-500 text-center mt-8">{error}</div>;
    }

    return (
        <div className="container mx-auto px-4 py-8">
            <h1 className="text-2xl font-bold mb-4">Task Details</h1>
            {task ? (
                <div className="bg-white shadow-md rounded-lg p-6">
                    <h2 className="text-xl font-semibold mb-2">{task.short_description || 'New Request'}</h2>
                    <p className="text-gray-600 mb-2">ID: {task.id}</p>
                    <p className="text-gray-600 mb-2">Status: {task.state || 'Unknown'}</p>
                    <p className="text-gray-600 mb-2">Created: {new Date(task.created_at).toLocaleString()}</p>
                    <p className="text-gray-600 mb-4">Updated: {new Date(task.updated_at).toLocaleString()}</p>
                    <div className="mb-4">
                        <h3 className="font-semibold mb-1">Context:</h3>
                        <p className="text-gray-700">{task.context || 'Context not available'}</p>
                    </div>
                    {task.is_context_sufficient === false && (
                        <div className="mb-4">
                            <button 
                                className="bg-blue-500 text-white px-4 py-2 rounded" 
                                onClick={() => alert('Please provide more context.')}
                            >
                                Provide More Context
                            </button>
                        </div>
                    )}
                    <div className="mb-4">
                        <h3 className="font-semibold mb-1">Task:</h3>
                        <p className="text-gray-700">{task.task || task.short_description || 'Task not defined'}</p>
                    </div>
                    <div className="mb-4">
                        <h3 className="font-semibold mb-1">Analysis:</h3>
                        <pre className="text-gray-700 whitespace-pre-wrap">{JSON.stringify(task.analysis, null, 2) || 'Analysis not available'}</pre>
                    </div>
                    <div className="mb-4">
                        <h3 className="font-semibold mb-1">Concepts:</h3>
                        <pre className="text-gray-700 whitespace-pre-wrap">{JSON.stringify(task.concepts, null, 2) || 'Concepts not available'}</pre>
                    </div>
                </div>
            ) : (
                <p>Task not found</p>
            )}
        </div>
    );
};

export default TaskDetailsPage;
