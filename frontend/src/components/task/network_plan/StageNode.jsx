import React from 'react';
import { Handle, Position } from '@xyflow/react';
import { getEdgeColor } from './NetworkGraphLayout'; // Import the shared function

// Helper function to get edge color based on stage ID (for visual variety)
// Remove the duplicate function definition
// const getEdgeColor = (id) => {
//   const colors = [
//     '#3b82f6', // blue-500
//     '#8b5cf6', // purple-500
//     '#22c55e', // green-500
//     '#f59e0b', // amber-500
//     '#f43f5e'  // rose-500
//   ];
//   const numericId = parseInt(id, 10);
//   return colors[(numericId - 1) % colors.length];
// };

export default function StageNode({ data, selected, id }) {
  const { stage } = data;
  
  // Get the color based on stage id - same color as would be used for its outgoing edges
  const color = getEdgeColor(stage.id);
  
  // Check if this node has any outgoing connections
  const hasOutgoingConnections = data.hasOutgoingConnections;
  
  return (
    <div className={`p-4 transition-all duration-300 h-full w-full rounded-lg shadow-md relative overflow-visible
                    ${selected ? 'ring-2 ring-blue-500 bg-blue-50' : 'bg-white'}`}>
      {/* Source handle on right side*/}
      <Handle
        id="right"
        type="source"
        position={Position.Right}
        isConnectable={false}
        style={{ 
          backgroundColor: color, // Use the color from getEdgeColor
          border: 'none',
          width: '10px',
          height: '10px',
          visibility: hasOutgoingConnections ? 'visible' : 'hidden'
        }}
      />
      
      {/* Target handle on left side */}
      <Handle
        id="left"
        type="target"
        position={Position.Left}
        isConnectable={false}
        style={{ 
          visibility: 'hidden'
        }}
      />
      
      {/* Stage ID badge - remove transition effects that might cause blinking */}
      <div className={`absolute -top-2 -left-2 w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold shadow-sm bg-blue-100 text-blue-800`}
           style={{ transition: 'none' }}>
        {stage.id}
      </div>
      
      {/* Stage name with adaptive sizing support */}
      <div className="flex items-center justify-center h-full w-full pt-2 pb-4">
        <div className="text-sm font-medium text-center px-3 break-words">
          {stage.name}
        </div>
      </div>
      
      {/* Add a colored band to visually indicate the node's color */}
      <div 
        className="absolute h-2 bottom-0 left-0 right-0 rounded-b-lg" 
        style={{ backgroundColor: color }}
      />
    </div>
  );
} 