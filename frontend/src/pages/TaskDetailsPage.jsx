import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';

const TaskDetailsPage = () => {
    const { taskId } = useParams();
    const [task, setTask] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const navigate = useNavigate();

    useEffect(() => {
        const fetchTaskDetails = async () => {
            try {
                const response = await axios.get(`http://localhost:8000/tasks/${taskId}/`);
                setTask(response.data);
            } catch (err) {
                setError('Failed to load task details.');
            } finally {
                setLoading(false);
            }
        };

        fetchTaskDetails();
    }, [taskId]);

    const handleDelete = async () => {
        const confirmDelete = window.confirm('Are you sure you want to delete this task?');
        if (confirmDelete) {
            try {
                await axios.delete(`http://localhost:8000/tasks/${taskId}/`);
                alert('Task successfully deleted.');
                navigate('/');
            } catch (err) {
                alert('Error while deleting the task.');
            }
        }
    };

    if (loading) {
        return <div className="flex justify-center items-center h-screen">Loading...</div>;
    }

    if (error) {
        return <div className="text-red-500 text-center mt-8">{error}</div>;
    }

    return (
        <div className="container mx-auto px-4 py-8">
            <h1 className="text-3xl font-bold mb-6 text-center">Query Details</h1>
            <div className="container mx-auto px-4 py-8 flex">
                <div className="flex-1 mr-4">
                    {task ? (
                        <div className="bg-white shadow-lg rounded-lg p-6 border border-gray-200 flex-1">
                            <h2 className="text-2xl font-semibold mb-4">{task.short_description || 'New Request'}</h2>
                            <div className="mb-4">
                                <h3 className="font-semibold mb-1">Task:</h3>
                                <p className="text-gray-700">{task.task || task.short_description || 'Task not defined'}</p>
                            </div>
                            <div className="mb-4">
                                <h3 className="font-semibold mb-1">Context:</h3>
                                <p className="text-gray-700">{task.context || 'Context not available'}</p>
                            </div>
                            {task.is_context_sufficient === false && (
                                <div className="mb-4">
                                    <button 
                                        className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 transition"
                                        onClick={() => alert('Please provide more context.')}
                                    >
                                        Provide More Context
                                    </button>
                                </div>
                            )}
                            <div className="mb-4">
                                <h3 className="font-semibold mb-1">Analysis:</h3>
                                <pre className="text-gray-700 whitespace-pre-wrap bg-gray-100 p-2 rounded">{JSON.stringify(task.analysis, null, 2) || 'Analysis not available'}</pre>
                            </div>
                            <div className="mb-4">
                                <h3 className="font-semibold mb-1">Concepts:</h3>
                                <pre className="text-gray-700 whitespace-pre-wrap bg-gray-100 p-2 rounded">{JSON.stringify(task.concepts, null, 2) || 'Concepts not available'}</pre>
                            </div>
                            <div className="mb-4">
                                <button 
                                    className="bg-red-600 text-white px-4 py-2 rounded hover:bg-red-700 transition" 
                                    onClick={handleDelete}
                                >
                                    Delete Task
                                </button>
                            </div>
                        </div>
                    ) : (
                        <p className="text-center text-red-500">Task not found</p>
                    )}
                </div>
                <div className="w-1/3">
                    <div className="bg-white shadow-lg rounded-lg p-4 border border-gray-200 h-full flex-1">
                        <h3 className="text-xl font-semibold mb-4">Meta-data</h3>
                        <p className="text-gray-600 mb-1">ID: <span className="font-medium">{task?.id}</span></p>
                        <p className="text-gray-600 mb-1">Status: <span className="font-medium">{task?.state || 'Unknown'}</span></p>
                        <p className="text-gray-600 mb-1">Created: <span className="font-medium">{new Date(task?.created_at).toLocaleString()}</span></p>
                        <p className="text-gray-600 mb-4">Updated: <span className="font-medium">{new Date(task?.updated_at).toLocaleString()}</span></p>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default TaskDetailsPage;
