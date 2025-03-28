import React from 'react';
import { BaseEdge, getSmoothStepPath } from '@xyflow/react';

export default function CustomFlowEdge({ 
  id, 
  sourceX, 
  sourceY, 
  targetX, 
  targetY, 
  sourcePosition, 
  targetPosition, 
  style = {}, 
  markerEnd, 
  data 
}) {
  // Get the color from the data prop or use a default
  const color = data.color;

  // Calculate the edge path with explicit position forcing
  const [edgePath] = getSmoothStepPath({
    sourceX,
    sourceY,
    sourcePosition,
    targetX,
    targetY,
    targetPosition,
    borderRadius: 16,
  });

  return (
    <BaseEdge
      id={id}
      path={edgePath}
      style={{
        ...style,
        stroke: color,
        strokeWidth: 2,
      }}
      markerEnd={markerEnd}
    />
  );
} 