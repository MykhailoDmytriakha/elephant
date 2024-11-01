import React, { useState, useEffect } from "react";
import { RefreshCcw, Lightbulb, Check } from "lucide-react";
import { CollapsibleSection } from "./TaskComponents";
import { TaskStates } from "../../constants/taskStates";
import { getStateNumber } from "../../constants/taskStates";

export default function ApproachFormation({
  approaches,
  onRegenerateApproaches,
  isRegenerating,
  taskState,
  onSelectionChange,
  selectedItems: selectedItemsProp,
  isDecompositionStarted
}) {
  const [selectedItems, setSelectedItems] = useState(() => {
    if (approaches?.selected_approaches) {
      return {
        analytical_tools: approaches.selected_approaches.analytical_tools || [],
        practical_methods: approaches.selected_approaches.practical_methods || [],
        frameworks: approaches.selected_approaches.frameworks || []
      };
    }
    return selectedItemsProp || {
      analytical_tools: [],
      practical_methods: [],
      frameworks: []
    };
  });

  const categorizeToolId = (toolName) => {
    // Check in analytical tools
    const analyticalTool = approaches.tool_categories.analytical_tools.find(
      tool => tool.name === toolName || tool.tool_id === toolName
    );
    if (analyticalTool) return { category: 'analytical_tools', id: analyticalTool.tool_id };

    // Check in practical methods
    const practicalMethod = approaches.tool_categories.practical_methods.find(
      method => method.name === toolName || method.method_id === toolName
    );
    if (practicalMethod) return { category: 'practical_methods', id: practicalMethod.method_id };

    // Check in frameworks
    const framework = approaches.tool_categories.frameworks.find(
      framework => framework.name === toolName || framework.framework_id === toolName
    );
    if (framework) return { category: 'frameworks', id: framework.framework_id };

    return null;
  };

  const checkActiveCombination = (currentSelection) => {
    if (!approaches?.tool_combinations) return -1;

    return approaches.tool_combinations.findIndex(combo => {
      const currentTools = new Set([
        ...currentSelection.analytical_tools,
        ...currentSelection.practical_methods,
        ...currentSelection.frameworks
      ]);

      // Check if the current selection has exactly the same tools as the combo
      const comboToolIds = combo.tools.map(tool => {
        const toolInfo = categorizeToolId(tool);
        return toolInfo?.id;
      }).filter(Boolean);

      // Both conditions must be true:
      // 1. All combo tools must be in current selection
      // 2. Current selection must have the same number of tools as the combo
      return comboToolIds.every(toolId => currentTools.has(toolId)) 
        && currentTools.size === comboToolIds.length;
    });
  };

  const [activeCombo, setActiveCombo] = useState(() => {
    if (!approaches?.selected_approaches) return null;

    return checkActiveCombination({
      analytical_tools: approaches.selected_approaches.analytical_tools || [],
      practical_methods: approaches.selected_approaches.practical_methods || [],
      frameworks: approaches.selected_approaches.frameworks || []
    });
  });

  useEffect(() => {
    if (selectedItemsProp) {
      setSelectedItems(selectedItemsProp);
      setActiveCombo(checkActiveCombination(selectedItemsProp));
    }
  }, [selectedItemsProp]);

  useEffect(() => {
    if (approaches?.selected_approaches) {
      const newSelectedItems = {
        analytical_tools: approaches.selected_approaches.analytical_tools || [],
        practical_methods: approaches.selected_approaches.practical_methods || [],
        frameworks: approaches.selected_approaches.frameworks || []
      };
      setSelectedItems(newSelectedItems);
      setActiveCombo(checkActiveCombination(newSelectedItems));
    }
  }, [approaches?.selected_approaches]);

  const isApproachFormationStageOrLater =
    getStateNumber(taskState) >= getStateNumber(TaskStates.CLARIFICATION_COMPLETE);

  if (!isApproachFormationStageOrLater && !approaches?.tool_categories) {
    return null;
  }

  if (!approaches || Object.keys(approaches).length === 0) {
    return (
      <CollapsibleSection title="Approach Formation">
        <div className="text-center py-8">
          <button
            onClick={onRegenerateApproaches}
            disabled={isRegenerating}
            className="inline-flex items-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:bg-blue-300"
          >
            {isRegenerating ? (
              <>
                <RefreshCcw className="w-5 h-5 animate-spin" />
                Generating Approaches...
              </>
            ) : (
              <>
                <Lightbulb className="w-5 h-5" />
                Generate Approaches
              </>
            )}
          </button>
        </div>
      </CollapsibleSection>
    );
  }

  const handleSelection = (category, itemId) => {
    if (isDecompositionStarted || approaches?.selected_approaches) return;

    setSelectedItems(prev => {
      const newSelection = {
        ...prev,
        [category]: prev[category].includes(itemId)
          ? prev[category].filter(id => id !== itemId)
          : [...prev[category], itemId]
      };
      
      const matchingCombo = checkActiveCombination(newSelection);
      setActiveCombo(matchingCombo >= 0 ? matchingCombo : null);
      
      if (onSelectionChange) {
        onSelectionChange(newSelection);
      }
      
      return newSelection;
    });
  };

  const handleCombinationClick = (tools, comboIndex) => {
    if (approaches?.selected_approaches || isDecompositionStarted) return;

    setActiveCombo(comboIndex);
    const newSelection = {
      analytical_tools: [],
      practical_methods: [],
      frameworks: []
    };

    // Process each tool in the combination
    tools.forEach(toolName => {
      const categorization = categorizeToolId(toolName);
      if (categorization) {
        newSelection[categorization.category].push(categorization.id);
      }
    });

    setSelectedItems(newSelection);
    if (onSelectionChange) {
      onSelectionChange(newSelection);
    }
  };

  const getItemStyles = (isSelected, category) => {
    const categoryColors = {
      analytical_tools: {
        selected: 'border-blue-500 ring-2 ring-blue-200 bg-blue-50',
        badge: 'bg-blue-100 text-blue-800'
      },
      practical_methods: {
        selected: 'border-green-500 ring-2 ring-green-200 bg-green-50',
        badge: 'bg-green-100 text-green-800'
      },
      frameworks: {
        selected: 'border-purple-500 ring-2 ring-purple-200 bg-purple-50',
        badge: 'bg-purple-100 text-purple-800'
      }
    };

    return `
      border rounded-lg p-4 relative 
      ${isDecompositionStarted || approaches?.selected_approaches ? 'cursor-not-allowed opacity-75' : 'cursor-pointer hover:border-blue-400'} 
      ${isSelected ? categoryColors[category].selected : 'bg-white'}
      transition-colors
    `;
  };

  const renderToolsAndResources = () => (
    <div className="space-y-8">
      {/* Analytical Tools */}
      <div className="space-y-4">
        <h3 className="text-lg font-semibold text-gray-900">Tools</h3>
        <div className="grid grid-cols-1 gap-4">
          {approaches.tool_categories.analytical_tools.map((tool) => (
            <div 
              key={tool.tool_id} 
              className={getItemStyles(
                selectedItems.analytical_tools.includes(tool.tool_id),
                'analytical_tools'
              )}
              onClick={() => handleSelection('analytical_tools', tool.tool_id)}
              aria-disabled={isDecompositionStarted || approaches?.selected_approaches}
            >
              <div className="flex justify-between items-start mb-2">
                <h4 className="font-medium">{tool.name}</h4>
                <div className="flex items-center gap-2">
                  {selectedItems.analytical_tools.includes(tool.tool_id) && (
                    <Check className="w-4 h-4 text-blue-500" />
                  )}
                  <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">
                    {tool.tool_id}
                  </span>
                </div>
              </div>
              <p className="text-sm text-gray-600 mb-2">{tool.purpose}</p>
              <div className="text-sm mb-3">
                <strong>When to use:</strong> {tool.when_to_use}
              </div>
              <div className="text-sm mb-8">
                <strong>Contribution:</strong> {tool.contribution_to_task}
              </div>
              <div className="mt-2 mb-6">
                <strong className="text-sm block mb-2">Examples:</strong>
                <ul className="space-y-1">
                  {tool.examples.map((example, idx) => (
                    <li key={idx} className="text-xs bg-gray-100 text-gray-700 px-2 py-1 rounded w-fit">
                      {example}
                    </li>
                  ))}
                </ul>
              </div>
              <span className="absolute bottom-4 right-4 text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">
                {tool.ease_of_use}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Practical Methods */}
      <div className="space-y-4">
        <h3 className="text-lg font-semibold text-gray-900">Methods</h3>
        <div className="grid grid-cols-1 gap-4">
          {approaches.tool_categories.practical_methods.map((method) => (
            <div
              key={method.method_id}
              className={getItemStyles(
                selectedItems.practical_methods.includes(method.method_id),
                'practical_methods'
              )}
              onClick={() => handleSelection('practical_methods', method.method_id)}
              aria-disabled={isDecompositionStarted || approaches?.selected_approaches}
            >
              <div className="flex justify-between items-start mb-2">
                <h4 className="font-medium">{method.name}</h4>
                <div className="flex items-center gap-2">
                  {selectedItems.practical_methods.includes(method.method_id) && (
                    <Check className="w-4 h-4 text-green-500" />
                  )}
                  <span className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded">
                    {method.method_id}
                  </span>
                </div>
              </div>
              <p className="text-sm text-gray-600 mb-2">{method.description}</p>
              <div className="text-sm mb-8">
                <strong>Best for:</strong>
                <ul className="list-disc list-inside mt-1">
                  {method.best_for.map((use, idx) => (
                    <li key={idx} className="text-gray-600">{use}</li>
                  ))}
                </ul>
              </div>
              <span className="absolute bottom-4 right-4 text-xs bg-green-100 text-green-800 px-2 py-1 rounded">
                {method.difficulty_level}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Frameworks */}
      <div className="space-y-4">
        <h3 className="text-lg font-semibold text-gray-900">Frameworks</h3>
        <div className="grid grid-cols-1 gap-4">
          {approaches.tool_categories.frameworks.map((framework) => (
            <div
              key={framework.framework_id}
              className={getItemStyles(
                selectedItems.frameworks.includes(framework.framework_id),
                'frameworks'
              )}
              onClick={() => handleSelection('frameworks', framework.framework_id)}
              aria-disabled={isDecompositionStarted || approaches?.selected_approaches}
            >
              <div className="flex justify-between items-start mb-2">
                <h4 className="font-medium">{framework.name}</h4>
                <div className="flex items-center gap-2">
                  {selectedItems.frameworks.includes(framework.framework_id) && (
                    <Check className="w-4 h-4 text-purple-500" />
                  )}
                  <span className="text-xs bg-purple-100 text-purple-800 px-2 py-1 rounded">
                    {framework.framework_id}
                  </span>
                </div>
              </div>
              <div className="text-sm text-gray-600 mb-3">
                <strong>Structure:</strong> {framework.structure}
              </div>
              <div className="text-sm text-gray-600 mb-4">
                <strong>How to use:</strong> {framework.how_to_use}
              </div>
              
              <div className="space-y-3">
                <div>
                  <strong className="text-sm">Benefits:</strong>
                  <ul className="list-disc list-inside text-sm text-gray-600">
                    {framework.benefits.map((benefit, idx) => (
                      <li key={idx}>{benefit}</li>
                    ))}
                  </ul>
                </div>
                
                <div>
                  <strong className="text-sm">Adaptation Tips:</strong>
                  <ul className="list-disc list-inside text-sm text-gray-600">
                    {framework.adaptation_tips.map((tip, idx) => (
                      <li key={idx}>{tip}</li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Tool Combinations */}
      <div className="space-y-4">
        <h3 className="text-lg font-semibold text-gray-900">Recommended Combinations</h3>
        {approaches.tool_combinations.map((combo, idx) => (
          <div 
            key={idx} 
            className={`
              border rounded-lg p-4 transition-colors 
              ${approaches?.selected_approaches || isDecompositionStarted
                ? 'cursor-not-allowed opacity-75' 
                : 'cursor-pointer hover:bg-gray-50'
              }
              ${activeCombo === idx 
                ? 'border-amber-500 ring-2 ring-amber-200 bg-amber-50'
                : 'bg-white'
              }
            `}
            onClick={() => handleCombinationClick(combo.tools, idx)}
            aria-disabled={approaches?.selected_approaches || isDecompositionStarted}
          >
            <div className="flex justify-between items-start mb-2">
              <h4 className="font-medium">{combo.combination_name}</h4>
              <div className="flex items-center gap-2">
                {activeCombo === idx && (
                  <Check className="w-4 h-4 text-amber-500" />
                )}
              </div>
            </div>
            <p className="text-sm text-gray-600 mb-2">{combo.synergy_description}</p>
            <div className="text-sm mb-4">
              <strong>Use case:</strong> {combo.use_case}
            </div>
            <div className="flex flex-wrap gap-2">
              {combo.tools.map((tool, toolIdx) => {
                const toolInfo = categorizeToolId(tool);
                const isSelected = toolInfo && (
                  (toolInfo.category === 'analytical_tools' && selectedItems.analytical_tools.includes(toolInfo.id)) ||
                  (toolInfo.category === 'practical_methods' && selectedItems.practical_methods.includes(toolInfo.id)) ||
                  (toolInfo.category === 'frameworks' && selectedItems.frameworks.includes(toolInfo.id))
                );
                
                return (
                  <span 
                    key={toolIdx} 
                    className={`
                      text-xs px-2 py-1 rounded
                      ${isSelected 
                        ? 'bg-amber-100 text-amber-800' 
                        : 'bg-gray-100 text-gray-600'
                      }
                    `}
                  >
                    {tool}
                  </span>
                );
              })}
            </div>
          </div>
        ))}
      </div>
    </div>
  );

  return (
    <CollapsibleSection title="Approach Formation">
      <div 
        className={`relative ${isRegenerating ? 'pointer-events-none opacity-50' : ''}`}
      >
        <button
          onClick={onRegenerateApproaches}
          disabled={isRegenerating}
          className="absolute right-0 -top-1 inline-flex items-center justify-center gap-1.5 px-6 py-1.5 text-sm bg-gray-50 text-blue-600 rounded-md hover:bg-blue-50 hover:text-blue-700 transition-all shadow-sm disabled:bg-gray-50 disabled:text-gray-400 w-[160px]"
        >
          <RefreshCcw
            className={`w-3.5 h-3.5 ${isRegenerating ? "animate-spin" : ""}`}
            style={{ minWidth: "0.875rem" }}
          />
          {isRegenerating ? "Reapproaching..." : "Reapproach"}
        </button>

        <div className="mt-8">
          {renderToolsAndResources()}
        </div>
      </div>
    </CollapsibleSection>
  );
}
