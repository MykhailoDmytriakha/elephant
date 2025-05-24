import React from 'react';
import { Handle, Position } from '@xyflow/react';
import { getEdgeColor } from '../../../utils/colorUtils';

export default function StageNode({ data, selected, id }) {
  const { stage } = data;
  
  // Get the color based on stage id - same color as would be used for its outgoing edges
  const color = getEdgeColor(stage.id);
  
  // Check if this node has any outgoing connections
  const hasOutgoingConnections = data.hasOutgoingConnections;
  
  return (
    <div className="relative bg-white border-2 border-gray-200 rounded-lg p-4 shadow-sm hover:shadow-md transition-all duration-200">
      {/* Top Handle */}
      <Handle
        type="target"
        position={Position.Top}
        style={{
          background: color,
          width: 12,
          height: 12,
          border: '2px solid white',
          boxShadow: '0 2px 4px rgba(0,0,0,0.2)'
        }}
      />
      
      <div className="text-center">
        <h3 className="font-medium text-gray-900 text-sm mb-1">
          {stage.id}
        </h3>
        <p className="text-xs text-gray-600 line-clamp-3">
          {stage.name}
        </p>
      </div>
      
      {/* Bottom Handle - only show if there are outgoing connections */}
      {hasOutgoingConnections && (
        <Handle
          type="source"
          position={Position.Bottom}
          style={{
            background: color,
            width: 12,
            height: 12,
            border: '2px solid white',
            boxShadow: '0 2px 4px rgba(0,0,0,0.2)'
          }}
        />
      )}
    </div>
  );
} 