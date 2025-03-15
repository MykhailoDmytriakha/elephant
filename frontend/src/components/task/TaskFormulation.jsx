import React from 'react';
import { CollapsibleSection } from './TaskComponents';
import { RefreshCcw, FileText } from 'lucide-react';

export default function TaskFormulation({
    task,
    isContextGathered,
    onFormulate,
    isFormulating
}) {
    if (!isContextGathered) {
        return null;
    }

    return (
        <CollapsibleSection title="Define scope of the task">
            <div className="space-y-4">
                {task.scope && (typeof task.scope !== 'object' || Object.keys(task.scope).length > 0) ? (
                    <div className="bg-white p-4 rounded-lg border">
                        <div className="flex justify-between items-start">
                            <h4 className="text-sm font-medium text-gray-500 mb-2">
                                Define scope of the task
                            </h4>
                            <button
                                onClick={() => onFormulate(true)}
                                disabled={isFormulating}
                                className="text-sm text-blue-600 hover:text-blue-700"
                            >
                                <RefreshCcw className={`w-4 h-4 ${isFormulating ? 'animate-spin' : ''}`} />
                            </button>
                        </div>
                        <p className="text-gray-900 whitespace-pre-wrap">{task.scope}</p>
                    </div>
                ) : (
                    <div className="text-center py-8">
                        <button
                            onClick={() => onFormulate(false)}
                            disabled={isFormulating}
                            className="inline-flex items-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:bg-blue-300"
                        >
                            {isFormulating ? (
                                <>
                                    <RefreshCcw className="w-5 h-5 animate-spin" />
                                    Formulating...
                                </>
                            ) : (
                                <>
                                    <FileText className="w-5 h-5" />
                                    Define Scope
                                </>
                            )}
                        </button>
                    </div>
                )}
            </div>
        </CollapsibleSection>
    );
}