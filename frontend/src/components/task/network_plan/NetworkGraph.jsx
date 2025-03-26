import React, { useCallback, useMemo, useEffect, useState, useRef } from 'react';
import {
  ReactFlow,
  Background,
  Controls,
  Panel,
  MarkerType,
  useNodesState,
  useEdgesState,
  Handle,
  Position,
  BaseEdge,
  getSmoothStepPath,
  ConnectionMode
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';

// Add custom CSS for fullscreen mode and edge positioning
const customStyles = `
  .fullscreen-flow-container {
    background-color: #f9fafb; /* Match bg-gray-50 */
  }
  
  .fullscreen-flow-container .react-flow__renderer {
    background-color: #f9fafb; /* Match bg-gray-50 */
  }
  
  /* Make sure dots are visible in fullscreen */
  .fullscreen-flow-container .react-flow__background {
    z-index: 0;
    opacity: 1 !important;
  }
  
  /* Override browser's default fullscreen background */
  :fullscreen {
    background-color: #f9fafb !important;
  }
  
  :-webkit-full-screen {
    background-color: #f9fafb !important;
  }
  
  :-ms-fullscreen {
    background-color: #f9fafb !important;
  }
`;

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

// Custom edge component for better-looking connections
const CustomFlowEdge = ({ id, sourceX, sourceY, targetX, targetY, sourcePosition, targetPosition, style = {}, markerEnd, data }) => {
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
};

// Custom node component with improved design and correctly positioned handles
function StageNode({ data, selected , id}) {
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

// Define custom node types and edge types
const nodeTypes = {
  stageNode: StageNode,
};

const edgeTypes = {
  customEdge: CustomFlowEdge,
};

export default function NetworkGraph({
  stages,
  connections,
  selectedStageId,
  onStageSelect
}) {
  // Reference to the container div for fullscreen
  const flowContainerRef = useRef(null);
  
  // State to track if we're in fullscreen mode
  const [isFullscreen, setIsFullscreen] = useState(false);
  
  // Add the style to the document when component mounts
  useEffect(() => {
    // Add the fullscreen style to the document
    const styleElement = document.createElement('style');
    styleElement.innerHTML = customStyles;
    document.head.appendChild(styleElement);
    
    // Clean up function
    return () => {
      if (styleElement && document.head.contains(styleElement)) {
        document.head.removeChild(styleElement);
      }
    };
  }, []);
  
  // Debug connections data
  useEffect(() => {
    if (connections && connections.length > 0) {
      console.log('Raw connections data:', JSON.stringify(connections));
    } else {
      console.warn('No connections provided to NetworkGraph');
    }
  }, [connections]);

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

  // Create state for nodes and edges
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);
  
  // Get reactFlowInstance for viewport operations
  const [reactFlowInstance, setReactFlowInstance] = useState(null);

  // Update nodes and edges when data changes
  useEffect(() => {
    setNodes(initialNodes);
    setEdges(initialEdges);
    console.log('Updated nodes count:', initialNodes.length);
    console.log('Updated edges count:', initialEdges.length);
  }, [initialNodes, initialEdges, setNodes, setEdges]);

  // Additional debugging for edges
  useEffect(() => {
    if (edges.length > 0) {
      console.log('Current edges in state:', edges);
      
      // Check if nodes exist that match the edge connections
      edges.forEach(edge => {
        const sourceExists = nodes.some(n => n.id === edge.source);
        const targetExists = nodes.some(n => n.id === edge.target);
        
        if (!sourceExists) {
          console.warn(`Source node ${edge.source} for edge ${edge.id} doesn't exist!`);
        }
        if (!targetExists) {
          console.warn(`Target node ${edge.target} for edge ${edge.id} doesn't exist!`);
        }
      });
    } else if (connections && connections.length > 0) {
      console.warn('No edges created despite having connections data');
    }
  }, [edges, nodes, connections]);

  // Force a layout recalculation after component mounts
  useEffect(() => {
    if (reactFlowInstance && nodes.length > 0) {
      setTimeout(() => {
        reactFlowInstance.fitView({ padding: 0.2 });
      }, 200);
    }
  }, [reactFlowInstance, nodes]);

  // Handle node click - debounce to prevent multiple rapid selections
  const onNodeClick = useCallback((event, node) => {
    // Prevent event propagation to avoid double handling
    event.stopPropagation();
    
    // Toggle selection - if node is already selected, deselect it
    if (selectedStageId === node.id) {
      onStageSelect(null); // Deselect
    } else {
      onStageSelect(node.id); // Select
    }
  }, [onStageSelect, selectedStageId]);

  // Handle background click to deselect node
  const onPaneClick = useCallback(() => {
    onStageSelect(null);
  }, [onStageSelect]);
  
  // Function to toggle fullscreen
  const toggleFullscreen = useCallback(() => {
    if (!document.fullscreenElement) {
      // Enter fullscreen mode
      if (flowContainerRef.current.requestFullscreen) {
        flowContainerRef.current.requestFullscreen()
          .then(() => {
            setIsFullscreen(true);
            // Re-fit the view after entering fullscreen
            setTimeout(() => {
              if (reactFlowInstance) {
                reactFlowInstance.fitView({ padding: 0.1 });
              }
            }, 300);
          })
          .catch(err => {
            console.error(`Error attempting to enable fullscreen: ${err.message}`);
          });
      }
    } else {
      // Exit fullscreen mode
      if (document.exitFullscreen) {
        document.exitFullscreen()
          .then(() => {
            setIsFullscreen(false);
            // Re-fit the view after exiting fullscreen
            setTimeout(() => {
              if (reactFlowInstance) {
                reactFlowInstance.fitView({ padding: 0.2 });
              }
            }, 300);
          })
          .catch(err => {
            console.error(`Error attempting to exit fullscreen: ${err.message}`);
          });
      }
    }
  }, [reactFlowInstance]);
  
  // Add a stronger fullscreen change effect
  useEffect(() => {
    const handleFullscreenChange = () => {
      const isCurrentlyFullscreen = 
        document.fullscreenElement || 
        document.webkitFullscreenElement || 
        document.mozFullscreenElement || 
        document.msFullscreenElement;
      
      setIsFullscreen(!!isCurrentlyFullscreen);
      
      // Re-fit view after fullscreen change to ensure everything is visible
      if (reactFlowInstance) {
        setTimeout(() => {
          reactFlowInstance.fitView({ padding: 0.2 });
        }, 100);
      }
      
      // Force background style updates
      if (isCurrentlyFullscreen) {
        document.documentElement.style.backgroundColor = '#f9fafb';
        if (flowContainerRef.current) {
          flowContainerRef.current.style.backgroundColor = '#f9fafb';
        }
      }
    };
    
    document.addEventListener('fullscreenchange', handleFullscreenChange);
    document.addEventListener('webkitfullscreenchange', handleFullscreenChange);
    document.addEventListener('mozfullscreenchange', handleFullscreenChange);
    document.addEventListener('MSFullscreenChange', handleFullscreenChange);
    
    return () => {
      document.removeEventListener('fullscreenchange', handleFullscreenChange);
      document.removeEventListener('webkitfullscreenchange', handleFullscreenChange);
      document.removeEventListener('mozfullscreenchange', handleFullscreenChange);
      document.removeEventListener('MSFullscreenChange', handleFullscreenChange);
    };
  }, [reactFlowInstance]);

  return (
    <div 
      ref={flowContainerRef} 
      style={{ 
        width: '100%', 
        height: '100%',
        backgroundColor: '#f9fafb',
      }}
      className={isFullscreen ? 'fullscreen-flow-container' : ''}
    >
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeClick={onNodeClick}
        onPaneClick={onPaneClick}
        onInit={setReactFlowInstance}
        fitView
        fitViewOptions={{ padding: 0.2 }}
        minZoom={0.75}
        maxZoom={1.5}
        nodeTypes={nodeTypes}
        edgeTypes={edgeTypes}
        proOptions={{ hideAttribution: true }}
        elementsSelectable={true}
        nodesDraggable={false}
        className="bg-gray-50 rounded-lg"
        connectionMode={ConnectionMode.Loose}
        connectionLineType="smoothstep"
        defaultEdgeOptions={{
          type: 'customEdge',
        }}
      >
        <Background 
          color="#64748b"      // Darker color for better visibility
          gap={24}             // Slightly larger gap
          size={1.2}           // Slightly larger dots
          variant="dots" 
          className="!opacity-100"  // Force opacity to ensure visibility
        />
        <Controls 
          position="bottom-right" 
          showInteractive={false}
          className="bg-white shadow-md rounded-md border border-gray-100"
        />
        {/* <Panel position="bottom-right" className="bg-white p-2 rounded-md shadow-sm text-xs text-gray-500 opacity-50">
          Click on a stage to view its details
        </Panel> */}
        
        {/* Fullscreen toggle button */}
        <Panel position="top-right" className="bg-white shadow-md rounded-md border border-gray-100">
          <button
            onClick={toggleFullscreen}
            className="p-2 hover:bg-gray-100 rounded transition-colors flex items-center justify-center"
            title={isFullscreen ? "Exit Fullscreen" : "Fullscreen Mode"}
          >
            {isFullscreen ? (
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M8 3v3a2 2 0 0 1-2 2H3"></path>
                <path d="M21 8h-3a2 2 0 0 1-2-2V3"></path>
                <path d="M3 16h3a2 2 0 0 1 2 2v3"></path>
                <path d="M16 21v-3a2 2 0 0 1 2-2h3"></path>
              </svg>
            ) : (
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M8 3H5a2 2 0 0 0-2 2v3"></path>
                <path d="M21 8V5a2 2 0 0 0-2-2h-3"></path>
                <path d="M3 16v3a2 2 0 0 0 2 2h3"></path>
                <path d="M16 21h3a2 2 0 0 0 2-2v-3"></path>
              </svg>
            )}
          </button>
        </Panel>
      </ReactFlow>
    </div>
  );
} 