#!/usr/bin/env python3
"""
简化的系统测试脚本
"""
import os
import sys
import subprocess
import time
import asyncio

# 设置环境变量
os.environ['CLAUDE_API_KEY'] = 'sk-jQf4913d0436e88518954e0671c33c454484d916f13NqK25'
os.environ['CLAUDE_API_BASE_URL'] = 'https://api.gptsapi.net/v1'
os.environ['DATABASE_URL'] = 'sqlite+aiosqlite:///test.db'
os.environ['REDIS_URL'] = 'redis://localhost:6379'
os.environ['SECRET_KEY'] = 'test-secret-key-for-development'

# 添加backend目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))


def print_header(text):
    print(f"\n{'=' * 50}")
    print(f"{text:^50}")
    print(f"{'=' * 50}\n")


def print_status(task, success):
    symbol = "✓" if success else "✗"
    color = "\033[92m" if success else "\033[91m"
    reset = "\033[0m"
    print(f"{color}{symbol}{reset} {task}")


async def test_imports():
    """测试所有导入"""
    print_header("Testing Imports")
    
    imports = [
        ("FastAPI", "from fastapi import FastAPI"),
        ("SQLAlchemy", "from sqlalchemy import create_engine"),
        ("Anthropic", "from anthropic import AsyncAnthropic"),
        ("Pydantic", "from pydantic import BaseModel"),
        ("Agents", "from core.agents import WorkerAgent, CoordinatorAgent"),
        ("Database", "from core.database import get_db"),
        ("Settings", "from config.settings import settings")
    ]
    
    all_ok = True
    for name, import_stmt in imports:
        try:
            exec(import_stmt)
            print_status(f"Import {name}", True)
        except Exception as e:
            print_status(f"Import {name}: {str(e)}", False)
            all_ok = False
    
    return all_ok


async def test_basic_agent():
    """测试基本Agent功能"""
    print_header("Testing Basic Agent")
    
    try:
        from core.agents import AgentConfig, WorkerAgent
        
        config = AgentConfig(
            name="test_worker",
            role="worker",
            model="claude-3-sonnet-20240229"
        )
        
        worker = WorkerAgent(config)
        print_status("Created Worker Agent", True)
        
        # 测试基本处理
        result = await worker.process({
            "task": "Say hello",
            "context": {}
        })
        
        print_status(f"Agent processed task: {result.success}", result.success)
        return result.success
        
    except Exception as e:
        print_status(f"Agent test failed: {e}", False)
        return False


async def test_database():
    """测试数据库连接"""
    print_header("Testing Database")
    
    try:
        from core.database import init_db, engine
        from sqlalchemy import text
        
        # 初始化数据库
        await init_db()
        print_status("Database initialized", True)
        
        # 测试连接
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            print_status("Database connection successful", True)
            return True
            
    except Exception as e:
        print_status(f"Database test failed: {e}", False)
        return False


async def test_api_server():
    """测试API服务器"""
    print_header("Testing API Server")
    
    try:
        # 启动服务器
        server_process = subprocess.Popen(
            [sys.executable, '-m', 'uvicorn', 'main:app', '--host', '0.0.0.0', '--port', '8001'],
            cwd='backend',
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        print("Starting API server...")
        time.sleep(5)  # 等待服务器启动
        
        # 测试健康检查
        import requests
        try:
            response = requests.get("http://localhost:8001/api/health")
            if response.status_code == 200:
                print_status("API server is running", True)
                result = True
            else:
                print_status("API server health check failed", False)
                result = False
        except:
            print_status("API server not responding", False)
            result = False
        
        # 停止服务器
        server_process.terminate()
        server_process.wait()
        
        return result
        
    except Exception as e:
        print_status(f"API server test failed: {e}", False)
        return False


async def test_workflow_engine():
    """测试工作流引擎"""
    print_header("Testing Workflow Engine")
    
    try:
        from core.workflow.workflow_engine import WorkflowEngine
        from core.database import AsyncSessionLocal
        
        async with AsyncSessionLocal() as session:
            engine = WorkflowEngine(session)
            
            # 加载简单工作流
            workflow_def = {
                "nodes": [
                    {"id": "start", "type": "start", "config": {}},
                    {"id": "end", "type": "end", "config": {}}
                ],
                "edges": [
                    {"from_node": "start", "to_node": "end"}
                ]
            }
            
            engine.load_workflow(workflow_def)
            print_status("Workflow loaded", True)
            
            # 执行工作流
            result = await engine.execute({"test": "data"})
            print_status("Workflow executed", True)
            return True
            
    except Exception as e:
        print_status(f"Workflow test failed: {e}", False)
        return False


async def run_all_tests():
    """运行所有测试"""
    print("=" * 50)
    print("Multi-Agent System Simple Test Suite".center(50))
    print("=" * 50)
    
    tests = [
        ("Imports", test_imports),
        ("Basic Agent", test_basic_agent),
        ("Database", test_database),
        ("API Server", test_api_server),
        ("Workflow Engine", test_workflow_engine)
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
    print_header("Test Summary")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "PASSED" if result else "FAILED"
        print_status(f"{test_name}: {status}", result)
    
    print(f"\nTotal: {total}, Passed: {passed}, Failed: {total - passed}")
    
    if passed == total:
        print("\n✅ All tests passed! System is functional.")
        print("\nTo start the system manually:")
        print("1. cd backend")
        print("2. python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload")
        print("\nAPI Documentation will be available at:")
        print("- http://localhost:8000/docs")
    else:
        print("\n❌ Some tests failed. Please check the errors above.")
    
    return passed == total


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)