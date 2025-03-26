import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { InfoCard } from './TaskComponents';
import { Copy, Check } from "lucide-react";

export default function Metadata({ task }) {
    const [copied, setCopied] = useState(false);
    // Removed subtask state as it wasn't used in the provided code for linking

    const handleCopy = () => {
        navigator.clipboard.writeText(task.id);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };

    return (
        <div className="sticky top-4">
            <InfoCard title="Metadata">
                <div className="space-y-3">
                    {/* Task ID */}
                    <div>
                        <h3 className="text-sm font-medium text-gray-500">Task ID</h3>
                        <div className="flex items-center gap-2 mt-1">
                            <p className="text-gray-900 font-mono text-xs bg-gray-50 p-1 rounded border break-all">
                                {task.id}
                            </p>
                            <button
                                onClick={handleCopy}
                                className="p-1 text-gray-500 hover:text-gray-700 rounded-md hover:bg-gray-100"
                                title="Copy Task ID"
                            >
                                {copied ? (
                                    <Check className="w-4 h-4 text-green-600" />
                                ) : (
                                    <Copy className="w-4 h-4" />
                                )}
                            </button>
                        </div>
                    </div>
                    {/* Created At */}
                    <div>
                        <h3 className="text-sm font-medium text-gray-500">Created</h3>
                        <p className="mt-1 text-gray-900 text-sm">
                            {new Date(task.created_at).toLocaleString()}
                        </p>
                    </div>
                    {/* Updated At */}
                    <div>
                        <h3 className="text-sm font-medium text-gray-500">Last Updated</h3>
                        <p className="mt-1 text-gray-900 text-sm">
                            {new Date(task.updated_at).toLocaleString()}
                        </p>
                    </div>

                    {/* Stages List */}
                    {task.network_plan?.stages && task.network_plan.stages.length > 0 && (
                        <>
                            <hr className="my-3 border-gray-200" />
                            <div>
                                <h3 className="text-sm font-medium text-gray-500 mb-2">Stages</h3>
                                <div className="space-y-1">
                                    {task.network_plan.stages.map((stage) => (
                                        // --- LINK ADDED HERE ---
                                        <Link
                                            key={stage.id}
                                            to={`/tasks/${task.id}/stages/${stage.id}`}
                                            // Pass stage and task info needed for the detail page
                                            state={{ stage: stage, taskShortDescription: task.short_description, taskId: task.id }}
                                            className="block p-2 rounded-md hover:bg-gray-100 cursor-pointer transition-colors border border-transparent hover:border-gray-200"
                                        >
                                            <span className="text-sm font-medium text-blue-700 hover:text-blue-900">
                                                {stage.id}. {stage.name}
                                            </span>
                                        </Link>
                                        // --- END LINK ---
                                    ))}
                                </div>
                            </div>
                        </>
                    )}
                </div>
            </InfoCard>
        </div>
    );
}