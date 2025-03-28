import { useMemo } from 'react';
import { MarkerType } from '@xyflow/react';

// Helper function to get edge color based on stage ID (for visual variety)
const getEdgeColor = (id) => {
  const colors = [
    '#3b82f6', // blue-500
    '#8b5cf6', // purple-500
    '#22c55e', // green-500
    '#f59e0b', // amber-500
    '#f43f5e'  // rose-500
  ];
  const numericId = parseInt(id, 10);
  return colors[(numericId - 1) % colors.length];
};

export function useNetworkGraphLayout(stages, connections, selectedStageId) {
  // Create nodes from stages
  const initialNodes = useMemo(() => {
    if (!stages || stages.length === 0) {
      console.warn('No stages provided to NetworkGraph');
      return [];
    }
    
    console.log('Stages received:', stages);
    
    // Set up grid layout
    const columns = Math.min(3, stages.length);
    const baseNodeWidth = 220;
    const baseNodeHeight = 120;
    const horizontalGap = 150;
    const verticalGap = 150;
    
    // Function to calculate adaptive size based on text length
    const calculateNodeSize = (text) => {
      const textLength = text.length;
      // Base size for short text
      if (textLength < 100) {
        return { width: baseNodeWidth, height: baseNodeHeight };
      }
      // Medium text (30-60 characters)
      else if (textLength < 130) {
        return { width: baseNodeWidth + 40, height: baseNodeHeight + 20 };
      }
      // Long text (60+ characters)
      else {
        return { width: baseNodeWidth + 80, height: baseNodeHeight + 40 };
      }
    };
    
    // Find which nodes have outgoing connections
    const nodesWithOutgoingConnections = new Set();
    if (connections && connections.length > 0) {
      connections.forEach(conn => {
        nodesWithOutgoingConnections.add(String(conn.stage1));
      });
    }
    
    return stages.map((stage, index) => {
      // Ensure ID is a string and log for debugging
      const nodeId = String(stage.id);
      console.log(`Creating node with ID: ${nodeId}`);
      
      // Calculate adaptive node size based on text length
      const { width: nodeWidth, height: nodeHeight } = calculateNodeSize(stage.name);
      
      // Calculate positions in a grid layout
      const column = index % columns;
      const row = Math.floor(index / columns);
      
      return {
        id: nodeId,
        type: 'stageNode',
        data: { 
          stage,
          selected: selectedStageId === stage.id || selectedStageId === nodeId,
          hasOutgoingConnections: nodesWithOutgoingConnections.has(nodeId)
        },
        position: { 
          x: column * (baseNodeWidth + horizontalGap) + 50, 
          y: row * (baseNodeHeight + verticalGap) + 50 
        },
        style: {
          width: nodeWidth,
          height: nodeHeight,
          borderRadius: 10,
          border: `2px solid ${(selectedStageId === stage.id || selectedStageId === nodeId) ? '#3b82f6' : '#e5e7eb'}`,
          boxShadow: (selectedStageId === stage.id || selectedStageId === nodeId)
            ? '0 0 0 3px rgba(59, 130, 246, 0.3), 0 4px 6px -1px rgba(0, 0, 0, 0.1)' 
            : '0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)',
          transition: 'all 0.3s ease',
          zIndex: 1 // Lower zIndex for nodes so edges can appear above them
        },
        connectable: true,
      };
    });
  }, [stages, selectedStageId, connections]);

  // Create edges from connections
  const initialEdges = useMemo(() => {
    if (!connections || connections.length === 0 || !stages || stages.length === 0) {
      console.log('No connections or stages available');
      return [];
    }
    
    console.log('Creating edges from connections:', connections);
    
    // Check if connections have valid source and target
    const validConnections = connections.filter(conn => {
      const source = String(conn.stage1);
      const target = String(conn.stage2);
      
      const hasValidSource = stages.some(s => String(s.id) === source);
      const hasValidTarget = stages.some(s => String(s.id) === target);
      
      if (!hasValidSource) {
        console.warn(`Invalid connection source: ${source} not found in stages`);
      }
      if (!hasValidTarget) {
        console.warn(`Invalid connection target: ${target} not found in stages`);
      }
      
      return hasValidSource && hasValidTarget;
    });
    
    console.log('Valid connections:', validConnections);
    
    return validConnections.map((connection, index) => {
      // Get the source stage to determine color
      const sourceId = parseInt(connection.stage1);
      const stageColor = getEdgeColor(sourceId); // Get color based on source stage ID

      console.log('Connection:', connection);
      const edge = {
        id: `edge-${connection.stage1}-${connection.stage2}`,
        source: String(connection.stage1),
        target: String(connection.stage2),
        animated: false,
        data: {
          color: stageColor // Pass color in data for custom edge
        },
        markerEnd: {
          type: MarkerType.ArrowClosed,
          color: stageColor,
          width: 18, 
          height: 18
        },
        zIndex: 1000, // Additional zIndex property for the edge
      };
      
      console.log(`Created edge: ${edge.source} -> ${edge.target}, from ${edge.sourceHandle} to ${edge.targetHandle}`);
      return edge;
    });
  }, [connections, stages]);

  return { initialNodes, initialEdges };
} 