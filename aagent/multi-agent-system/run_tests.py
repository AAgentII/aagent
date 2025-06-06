#!/usr/bin/env python3
"""
运行系统测试的脚本
"""
import os
import sys
import asyncio
import subprocess

# 添加backend目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

def run_command(cmd):
    """执行命令并打印输出"""
    print(f"\n{'='*60}")
    print(f"Running: {cmd}")
    print(f"{'='*60}\n")
    
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    
    return result.returncode == 0

def main():
    """主函数"""
    print("Multi-Agent Orchestration System - Test Runner")
    print("=" * 60)
    
    # 检查环境
    print("\n1. Checking environment...")
    
    # 检查Python版本
    python_version = sys.version_info
    if python_version.major < 3 or python_version.minor < 11:
        print(f"Error: Python 3.11+ required, found {python_version.major}.{python_version.minor}")
        return 1
    print(f"✓ Python {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    # 设置环境变量
    os.environ['CLAUDE_API_KEY'] = 'sk-jQf4913d0436e88518954e0671c33c454484d916f13NqK25'
    os.environ['CLAUDE_API_BASE_URL'] = 'https://api.gptsapi.net/v1'
    os.environ['DATABASE_URL'] = 'sqlite+aiosqlite:///:memory:'
    os.environ['REDIS_URL'] = 'redis://localhost:6379'
    os.environ['SECRET_KEY'] = 'test-secret-key'
    
    # 运行Agent测试
    print("\n2. Running Agent tests...")
    if run_command("cd tests && python test_agents.py"):
        print("✓ Agent tests passed")
    else:
        print("✗ Agent tests failed")
        return 1
    
    # 运行工作流引擎测试
    print("\n3. Running Workflow Engine tests...")
    if run_command("cd tests && python test_workflow_engine.py"):
        print("✓ Workflow Engine tests passed")
    else:
        print("✗ Workflow Engine tests failed")
        return 1
    
    print("\n" + "="*60)
    print("✓ All tests passed successfully!")
    print("="*60)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())