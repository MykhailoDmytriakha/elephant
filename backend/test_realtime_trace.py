#!/usr/bin/env python3
"""
Test script to demonstrate real-time execution trace streaming
"""
import asyncio
import sys
import os

# Add the backend src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.model.task import Task
from src.ai_agents.router_agent import route_and_execute_request
from src.ai_agents.agent_tracker import get_tracker, remove_tracker

async def test_realtime_trace():
    """Test the real-time execution trace functionality"""
    print("🧪 Testing Real-Time Execution Trace")
    print("=" * 50)
    
    # Create a simple test task
    task = Task(
        id="test-task-123",
        task="Test task for real-time trace demonstration",
        short_description="Real-time trace test"
    )
    
    # Test message that will trigger general chat
    test_message = "what is current status of project?"
    workspace_path = "/tmp/test_workspace"
    session_id = "test_session_123"
    
    print(f"📝 Test Message: {test_message}")
    print(f"🏗️ Workspace: {workspace_path}")
    print(f"🔗 Session: {session_id}")
    print()
    
    print("🚀 Starting Real-Time Execution Trace:")
    print("-" * 50)
    
    try:
        # Stream the response and show how execution trace appears in real-time
        async for chunk in route_and_execute_request(task, test_message, workspace_path, session_id):
            # Print each chunk as it comes (simulating real-time streaming)
            print(chunk, end='', flush=True)
            
            # Add a small delay to demonstrate real-time effect
            await asyncio.sleep(0.1)
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
    finally:
        # Clean up
        remove_tracker(str(task.id), session_id)
    
    print("\n" + "=" * 50)
    print("✅ Real-Time Execution Trace Test Completed")

def demonstrate_difference():
    """Show the difference between old and new approaches"""
    print("\n📊 **BEFORE vs AFTER Comparison**")
    print("=" * 60)
    
    print("🟥 **BEFORE (Old Approach):**")
    print("1. 🔍 Agent Routing Analysis (immediate)")
    print("2. 💬 Main Agent Response (streaming)")
    print("3. 🔍 Agent Execution Trace (at the end) ❌")
    print("   └── User has to wait for full response to see trace")
    
    print("\n🟢 **AFTER (New Approach):**")
    print("1. 🔍 Agent Routing Analysis (immediate)")
    print("2. 🔍 Agent Execution Trace Header (immediate)")
    print("3. 🔗 Agent Routing Events (real-time as they happen) ✅")
    print("4. 💬 Main Agent Response (streaming)")
    print("5. 🛠️ Tool Calls (real-time as they happen) ✅")
    print("6. ⏱️ Execution Summary (at the end)")
    print("   └── User sees execution details in real-time!")

if __name__ == "__main__":
    # Show the conceptual difference first
    demonstrate_difference()
    
    print("\n" + "🧪" * 20)
    print("Now running live demonstration...")
    print("🧪" * 20)
    
    # Run the actual test
    asyncio.run(test_realtime_trace()) 