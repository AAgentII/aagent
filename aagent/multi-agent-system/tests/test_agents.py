#!/usr/bin/env python3
"""
Agent系统测试脚本
"""
import asyncio
import sys
import os

# 添加backend目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'backend'))

from core.agents import AgentConfig, WorkerAgent, CoordinatorAgent, SupervisorAgent, ValidatorAgent
from core.agents.base_agent import AgentOutput


async def test_worker_agent():
    """测试Worker Agent"""
    print("\n[Test] Worker Agent")
    
    config = AgentConfig(
        name="test_worker",
        role="worker",
        model="claude-3-sonnet-20240229",
        system_prompt="You are a helpful assistant that processes tasks."
    )
    
    worker = WorkerAgent(config)
    
    # 测试任务
    task = {
        "task": "Calculate the sum of 15 + 27",
        "context": {"operation": "addition"}
    }
    
    try:
        result = await worker.process(task)
        print(f"✓ Worker processed task: {result.success}")
        print(f"  Result: {result.data}")
        return result.success
    except Exception as e:
        print(f"✗ Worker test failed: {e}")
        return False


async def test_coordinator_agent():
    """测试Coordinator Agent"""
    print("\n[Test] Coordinator Agent")
    
    config = AgentConfig(
        name="test_coordinator",
        role="coordinator",
        system_prompt="You are a coordinator that manages task distribution."
    )
    
    coordinator = CoordinatorAgent(config)
    
    # 测试任务分配
    task = {
        "task": "Process customer orders",
        "context": {
            "orders": ["order1", "order2", "order3"]
        }
    }
    
    try:
        result = await coordinator.process(task)
        print(f"✓ Coordinator processed task: {result.success}")
        print(f"  Plan: {result.data}")
        return result.success
    except Exception as e:
        print(f"✗ Coordinator test failed: {e}")
        return False


async def test_supervisor_agent():
    """测试Supervisor Agent"""
    print("\n[Test] Supervisor Agent")
    
    config = AgentConfig(
        name="test_supervisor",
        role="supervisor",
        system_prompt="You are a supervisor that monitors task execution."
    )
    
    supervisor = SupervisorAgent(config)
    
    # 测试监督任务
    task = {
        "task": "Monitor system performance",
        "context": {
            "metrics": {
                "cpu": 75,
                "memory": 60,
                "disk": 40
            }
        }
    }
    
    try:
        result = await supervisor.process(task)
        print(f"✓ Supervisor processed task: {result.success}")
        print(f"  Analysis: {result.data}")
        return result.success
    except Exception as e:
        print(f"✗ Supervisor test failed: {e}")
        return False


async def test_validator_agent():
    """测试Validator Agent"""
    print("\n[Test] Validator Agent")
    
    config = AgentConfig(
        name="test_validator",
        role="validator",
        system_prompt="You are a validator that checks task outputs."
    )
    
    validator = ValidatorAgent(config)
    
    # 测试验证任务
    task = {
        "task": "Validate calculation result",
        "context": {
            "input": "15 + 27",
            "output": "42",
            "expected_type": "number"
        }
    }
    
    try:
        result = await validator.process(task)
        print(f"✓ Validator processed task: {result.success}")
        print(f"  Validation: {result.data}")
        return result.success
    except Exception as e:
        print(f"✗ Validator test failed: {e}")
        return False


async def test_agent_communication():
    """测试Agent间通信"""
    print("\n[Test] Agent Communication")
    
    # 创建两个Agent
    coordinator = CoordinatorAgent(AgentConfig(
        name="coordinator",
        role="coordinator"
    ))
    
    worker = WorkerAgent(AgentConfig(
        name="worker",
        role="worker"
    ))
    
    try:
        # 发送消息
        message = await coordinator.send_message(
            to_agent=worker.id,
            content={"task": "Test message"},
            message_type="task"
        )
        print(f"✓ Message sent: {message.id}")
        
        # 接收消息
        await worker.receive_message(message)
        received = await worker.wait_for_message(timeout=1.0)
        
        if received:
            print(f"✓ Message received by worker")
            return True
        else:
            print(f"✗ Message not received")
            return False
            
    except Exception as e:
        print(f"✗ Communication test failed: {e}")
        return False


async def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("Agent System Test Suite".center(60))
    print("=" * 60)
    
    # 设置环境变量
    os.environ['CLAUDE_API_KEY'] = 'sk-jQf4913d0436e88518954e0671c33c454484d916f13NqK25'
    os.environ['CLAUDE_API_BASE_URL'] = 'https://api.gptsapi.net/v1'
    
    tests = [
        ("Worker Agent", test_worker_agent),
        ("Coordinator Agent", test_coordinator_agent),
        ("Supervisor Agent", test_supervisor_agent),
        ("Validator Agent", test_validator_agent),
        ("Agent Communication", test_agent_communication)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n✗ Test {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # 打印总结
    print("\n" + "=" * 60)
    print("Test Summary".center(60))
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "PASSED" if result else "FAILED"
        symbol = "✓" if result else "✗"
        color = "\033[92m" if result else "\033[91m"
        reset = "\033[0m"
        print(f"{color}{symbol}{reset} {test_name}: {status}")
    
    print(f"\nTotal: {total}, Passed: {passed}, Failed: {total - passed}")
    
    return passed == total


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)