import React from 'react';
import QuestionGroup from './QuestionGroup';

/**
 * Component for rendering the current question group within the scope definition workflow
 */
export default function ScopeQuestionsSection({
    currentGroup,
    currentQuestions,
    submitAnswers,
    isSubmitting,
    progress,
    GROUPS
}) {
    if (!currentQuestions || !currentQuestions.length) {
        return <div className="text-center py-4">Loading questions...</div>;
    }

    // Check if this is the last group
    const currentIndex = GROUPS.indexOf(currentGroup);
    const isLastGroup = currentIndex === GROUPS.length - 1;

    return (
        <QuestionGroup
            groupId={currentGroup}
            questions={currentQuestions}
            onSubmit={submitAnswers}
            isSubmitting={isSubmitting}
            progress={progress}
            isLastGroup={isLastGroup}
        />
    );
} 