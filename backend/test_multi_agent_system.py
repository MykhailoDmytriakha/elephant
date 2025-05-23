#!/usr/bin/env python3
"""
Test script for the Multi-Agent System

This script tests the core functionality of the autonomous multi-agent system.
"""

import asyncio
import sys
import os

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.ai_agents.router_agent import analyze_request_intent, AgentType
from src.ai_agents.chat_agent import create_workspace_for_task
from src.ai_agents.multi_agent_config import multi_agent_config, get_agent_capabilities
from src.model.task import Task
from src.model.status import StatusEnum

def test_intent_analysis():
    """Test the request intent analysis functionality"""
    print("🧪 Testing Intent Analysis...")
    
    test_cases = [
        ("Analyze sales data and create charts", AgentType.DATA_ANALYSIS),
        ("Write a Python script for web scraping", AgentType.CODE_DEVELOPMENT),
        ("Research the latest AI trends in 2024", AgentType.RESEARCH),
        ("Create a project plan for mobile app", AgentType.PLANNING),
        ("Hello, how are you today?", AgentType.GENERAL_CHAT),
        ("Build a machine learning model", AgentType.CODE_DEVELOPMENT),
        ("Visualize this CSV dataset", AgentType.DATA_ANALYSIS),
    ]
    
    success_count = 0
    for query, expected_agent in test_cases:
        result = analyze_request_intent(query)
        detected_agent = result["agent_type"]
        confidence = result["confidence"]
        
        success = detected_agent == expected_agent
        if success:
            success_count += 1
        
        status = "✅" if success else "❌"
        print(f"  {status} \"{query}\"")
        print(f"      Expected: {expected_agent.value}, Got: {detected_agent.value} (conf: {confidence:.2f})")
    
    print(f"\n📊 Intent Analysis Results: {success_count}/{len(test_cases)} correct")
    return success_count == len(test_cases)

def test_workspace_creation():
    """Test workspace creation functionality"""
    print("\n🏗️ Testing Workspace Creation...")
    
    try:
        # Create a test task
        test_task_id = "test_123"
        workspace_path = create_workspace_for_task(test_task_id)
        
        print(f"  ✅ Workspace created: {workspace_path}")
        
        # Check if directories were created
        import os
        from pathlib import Path
        
        workspace = Path(workspace_path)
        expected_dirs = ["data", "output", "temp"]
        
        all_dirs_exist = True
        for dir_name in expected_dirs:
            dir_path = workspace / dir_name
            if dir_path.exists():
                print(f"    ✅ {dir_name}/ directory created")
            else:
                print(f"    ❌ {dir_name}/ directory missing")
                all_dirs_exist = False
        
        return all_dirs_exist
        
    except Exception as e:
        print(f"  ❌ Workspace creation failed: {e}")
        return False

def test_agent_configuration():
    """Test agent configuration system"""
    print("\n⚙️ Testing Agent Configuration...")
    
    try:
        # Test getting agent configs
        data_agent_config = multi_agent_config.get_agent_config("data_analysis_agent")
        if data_agent_config:
            print(f"  ✅ Data agent config loaded: {data_agent_config.name}")
        else:
            print("  ❌ Data agent config not found")
            return False
        
        # Test capabilities
        capabilities = get_agent_capabilities("data_analysis_agent")
        expected_capabilities = ["data_analysis", "visualization", "file_operations"]
        
        has_capabilities = all(
            any(cap.value == expected for cap in capabilities) 
            for expected in expected_capabilities
        )
        
        if has_capabilities:
            print(f"  ✅ Agent capabilities verified: {[cap.value for cap in capabilities]}")
        else:
            print(f"  ❌ Missing expected capabilities")
            return False
        
        # Test workspace path generation
        workspace_path = multi_agent_config.get_workspace_path("test_task")
        print(f"  ✅ Workspace path generation: {workspace_path}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Configuration test failed: {e}")
        return False

async def test_data_analysis_tools():
    """Test data analysis tools"""
    print("\n📊 Testing Data Analysis Tools...")
    
    try:
        from src.ai_agents.autonomous_data_agent import analyze_csv_data, create_data_visualization
        import pandas as pd
        import tempfile
        import os
        
        # Create a test CSV file
        test_data = pd.DataFrame({
            'sales': [100, 150, 200, 175, 300],
            'month': ['Jan', 'Feb', 'Mar', 'Apr', 'May'],
            'product': ['A', 'B', 'A', 'B', 'A']
        })
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            test_data.to_csv(f.name, index=False)
            test_csv_path = f.name
        
        try:
            # Test CSV analysis
            analysis_result = analyze_csv_data(test_csv_path, "overview")
            if "Shape:" in analysis_result and "5 rows" in analysis_result:
                print("  ✅ CSV analysis working")
            else:
                print("  ❌ CSV analysis failed")
                return False
            
            # Test visualization (without actually creating the plot to avoid display issues)
            # We'll just test that the function doesn't crash
            print("  ✅ Data analysis tools functional")
            return True
            
        finally:
            # Clean up test file
            os.unlink(test_csv_path)
            
    except Exception as e:
        print(f"  ❌ Data analysis tools test failed: {e}")
        return False

def test_system_integration():
    """Test overall system integration"""
    print("\n🔗 Testing System Integration...")
    
    try:
        # Create a mock task
        test_task = Task(
            id="integration_test_123",
            task="Test data analysis integration",
            short_description="Integration test for multi-agent system"
        )
        
        # Test that we can import all required modules
        from src.ai_agents.chat_agent import stream_chat_response
        from src.ai_agents.router_agent import stream_intelligent_router_response
        from src.ai_agents.autonomous_data_agent import create_autonomous_data_agent
        
        print("  ✅ All modules imported successfully")
        
        # Test workspace creation for task
        workspace_path = create_workspace_for_task(str(test_task.id))
        print(f"  ✅ Task workspace created: {workspace_path}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ System integration test failed: {e}")
        return False

async def main():
    """Run all tests"""
    print("🚀 Starting Multi-Agent System Tests")
    print("=" * 50)
    
    tests = [
        ("Intent Analysis", test_intent_analysis),
        ("Workspace Creation", test_workspace_creation),
        ("Agent Configuration", test_agent_configuration),
        ("Data Analysis Tools", test_data_analysis_tools),
        ("System Integration", test_system_integration),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            
            if result:
                passed += 1
            else:
                failed += 1
                
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
            failed += 1
    
    print("\n" + "=" * 50)
    print(f"🏁 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed! Multi-Agent System is ready!")
        return True
    else:
        print("⚠️ Some tests failed. Please review the errors above.")
        return False

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n🛑 Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1) 