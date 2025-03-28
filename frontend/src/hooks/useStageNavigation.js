import { useState, useEffect } from 'react';
import { useToast } from '../components/common/ToastProvider';
import { fetchTaskDetails } from '../utils/api';

export function useStageNavigation(taskId, location) {
    const [allStages, setAllStages] = useState([]);
    const [isLoadingStages, setIsLoadingStages] = useState(true);
    const toast = useToast();

    useEffect(() => {
        async function fetchStages() {
            try {
                // Check if we already have stages from location.state
                if (location.state?.task?.network_plan?.stages) {
                    setAllStages(location.state.task.network_plan.stages);
                    setIsLoadingStages(false);
                    return;
                }

                // Otherwise fetch the task data to get all stages
                const taskData = await fetchTaskDetails(taskId);
                if (taskData && taskData.network_plan && taskData.network_plan.stages) {
                    setAllStages(taskData.network_plan.stages);
                }
            } catch (error) {
                console.error("Error fetching stages:", error);
                toast.showError("Could not load all stages for navigation.");
            } finally {
                setIsLoadingStages(false);
            }
        }

        if (taskId) {
            fetchStages();
        }
    }, [taskId, location.state, toast]);

    const getStageNavigation = (currentStageId) => {
        const currentStageIndex = allStages.findIndex(s => s.id === currentStageId);
        const hasPrevStage = currentStageIndex > 0;
        const hasNextStage = currentStageIndex < allStages.length - 1 && currentStageIndex !== -1;
        const prevStageId = hasPrevStage ? allStages[currentStageIndex - 1].id : null;
        const nextStageId = hasNextStage ? allStages[currentStageIndex + 1].id : null;

        return {
            currentStageIndex,
            hasPrevStage,
            hasNextStage,
            prevStageId,
            nextStageId
        };
    };

    return {
        allStages,
        isLoadingStages,
        getStageNavigation
    };
} 