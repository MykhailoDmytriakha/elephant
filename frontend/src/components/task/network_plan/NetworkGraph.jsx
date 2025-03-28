import React, { useCallback, useEffect, useState, useRef } from 'react';
import {
  ReactFlow,
  Background,
  Controls,
  useNodesState,
  useEdgesState,
  ConnectionMode
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import StageNode from './StageNode';
import CustomFlowEdge from './CustomFlowEdge';
import NetworkGraphControls from './NetworkGraphControls';
import { useNetworkGraphLayout } from './NetworkGraphLayout';

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
  
  // Get initial nodes and edges from the layout hook
  const { initialNodes, initialEdges } = useNetworkGraphLayout(stages, connections, selectedStageId);
  
  // Create state for nodes and edges
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);
  
  // Get reactFlowInstance for viewport operations
  const [reactFlowInstance, setReactFlowInstance] = useState(null);

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
        <NetworkGraphControls 
          isFullscreen={isFullscreen}
          onToggleFullscreen={toggleFullscreen}
        />
      </ReactFlow>
    </div>
  );
} 