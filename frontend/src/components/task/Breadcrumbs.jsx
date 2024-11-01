// src/components/task/Breadcrumbs.jsx
import React, { useState, useEffect } from 'react';
import { ChevronRight } from 'lucide-react';
import { fetchTaskDetails } from '../../utils/api';
import { Link } from 'react-router-dom';

export default function Breadcrumbs({ task }) {
  const [parentTask, setParentTask] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const loadParentTask = async () => {
      if (!task.parent_task) return;
      
      try {
        setLoading(true);
        const parent = await fetchTaskDetails(task.parent_task);
        setParentTask(parent);
      } catch (error) {
        console.error('Failed to load parent task:', error);
      } finally {
        setLoading(false);
      }
    };

    loadParentTask();
  }, [task.parent_task]);

  if (!task.parent_task) return null;

  return (
    <nav className="flex items-center space-x-2 text-sm">
      {loading ? (
        <div className="h-5 w-24 bg-gray-200 animate-pulse rounded"></div>
      ) : parentTask && (
        <Link 
          to={`/tasks/${parentTask.id}`}
          className="text-gray-600 hover:text-gray-900"
        >
          {parentTask.short_description}
        </Link>
      )}
      <ChevronRight className="w-4 h-4 text-gray-400" />
      <span className="text-gray-900 font-medium">
        {task.short_description}
      </span>
    </nav>
  );
}