#!/usr/bin/env python3
"""
多Agent系统启动和功能验证脚本
"""
import os
import sys
import asyncio
import subprocess
import time
import requests
import json
from typing import Dict, Any

# 添加backend目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

class SystemTester:
    def __init__(self):
        self.api_base_url = "http://localhost:8000"
        self.test_results = []
        self.backend_process = None
        
    def print_header(self, text: str):
        """打印格式化标题"""
        print(f"\n{'='*60}")
        print(f"{text:^60}")
        print(f"{'='*60}\n")
        
    def print_status(self, task: str, status: bool):
        """打印任务状态"""
        symbol = "✓" if status else "✗"
        color = "\033[92m" if status else "\033[91m"
        reset = "\033[0m"
        print(f"{color}{symbol}{reset} {task}")
        
    def check_python_version(self) -> bool:
        """检查Python版本"""
        version = sys.version_info
        if version.major >= 3 and version.minor >= 11:
            self.print_status(f"Python {version.major}.{version.minor}.{version.micro}", True)
            return True
        else:
            self.print_status(f"Python 3.11+ required, found {version.major}.{version.minor}", False)
            return False
            
    def check_dependencies(self) -> bool:
        """检查必要的依赖"""
        self.print_header("Checking Dependencies")
        
        dependencies = {
            "docker": "docker --version",
            "docker-compose": "docker-compose --version",
            "npm": "npm --version",
            "python": "python --version"
        }
        
        all_ok = True
        for dep, cmd in dependencies.items():
            try:
                result = subprocess.run(cmd.split(), capture_output=True, text=True)
                if result.returncode == 0:
                    self.print_status(f"{dep}: {result.stdout.strip()}", True)
                else:
                    self.print_status(f"{dep}: Not found", False)
                    all_ok = False
            except:
                self.print_status(f"{dep}: Not found", False)
                all_ok = False
                
        return all_ok
        
    def setup_environment(self):
        """设置环境变量"""
        self.print_header("Setting up Environment")
        
        env_vars = {
            'CLAUDE_API_KEY': 'sk-jQf4913d0436e88518954e0671c33c454484d916f13NqK25',
            'CLAUDE_API_BASE_URL': 'https://api.gptsapi.net/v1',
            'DATABASE_URL': 'sqlite+aiosqlite:///test.db',
            'REDIS_URL': 'redis://localhost:6379',
            'SECRET_KEY': 'test-secret-key-for-development'
        }
        
        for key, value in env_vars.items():
            os.environ[key] = value
            self.print_status(f"Set {key}", True)
            
    def install_backend_deps(self) -> bool:
        """安装后端依赖"""
        self.print_header("Installing Backend Dependencies")
        
        try:
            # 创建虚拟环境
            if not os.path.exists('backend/venv'):
                subprocess.run([sys.executable, '-m', 'venv', 'backend/venv'], check=True)
                self.print_status("Created virtual environment", True)
            
            # 激活虚拟环境并安装依赖
            pip_path = 'backend/venv/bin/pip' if os.name != 'nt' else 'backend\\venv\\Scripts\\pip'
            
            if os.path.exists(pip_path):
                subprocess.run([pip_path, 'install', '-r', 'backend/requirements.txt'], check=True)
                self.print_status("Installed backend dependencies", True)
                return True
            else:
                # 直接使用系统pip
                subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'backend/requirements.txt'], check=True)
                self.print_status("Installed backend dependencies (system pip)", True)
                return True
                
        except Exception as e:
            self.print_status(f"Failed to install backend dependencies: {e}", False)
            return False
            
    def start_backend(self) -> bool:
        """启动后端服务"""
        self.print_header("Starting Backend Service")
        
        try:
            # 启动后端
            python_path = 'backend/venv/bin/python' if os.name != 'nt' else 'backend\\venv\\Scripts\\python'
            if not os.path.exists(python_path):
                python_path = sys.executable
                
            self.backend_process = subprocess.Popen(
                [python_path, '-m', 'uvicorn', 'main:app', '--host', '0.0.0.0', '--port', '8000', '--reload'],
                cwd='backend',
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # 等待服务启动
            self.print_status("Starting FastAPI server...", True)
            time.sleep(5)
            
            # 检查服务是否运行
            try:
                response = requests.get(f"{self.api_base_url}/")
                if response.status_code == 200:
                    self.print_status("Backend service is running", True)
                    return True
            except:
                pass
                
            self.print_status("Backend service failed to start", False)
            return False
            
        except Exception as e:
            self.print_status(f"Failed to start backend: {e}", False)
            return False
            
    def test_api_endpoints(self) -> bool:
        """测试API端点"""
        self.print_header("Testing API Endpoints")
        
        all_passed = True
        
        # 测试健康检查
        try:
            response = requests.get(f"{self.api_base_url}/api/health")
            if response.status_code == 200:
                self.print_status("Health check endpoint", True)
            else:
                self.print_status("Health check endpoint", False)
                all_passed = False
        except Exception as e:
            self.print_status(f"Health check failed: {e}", False)
            all_passed = False
            
        # 测试工作流API
        endpoints = [
            ("GET", "/api/workflows", None),
            ("GET", "/api/agents", None),
            ("GET", "/api/agents/roles/available", None),
            ("GET", "/api/agents/models/available", None),
            ("GET", "/api/executions", None)
        ]
        
        for method, endpoint, data in endpoints:
            try:
                if method == "GET":
                    response = requests.get(f"{self.api_base_url}{endpoint}")
                else:
                    response = requests.post(f"{self.api_base_url}{endpoint}", json=data)
                    
                if response.status_code in [200, 201]:
                    self.print_status(f"{method} {endpoint}", True)
                else:
                    self.print_status(f"{method} {endpoint} - {response.status_code}", False)
                    all_passed = False
            except Exception as e:
                self.print_status(f"{method} {endpoint} - Error: {e}", False)
                all_passed = False
                
        return all_passed
        
    def test_workflow_creation(self) -> bool:
        """测试工作流创建和执行"""
        self.print_header("Testing Workflow Creation & Execution")
        
        try:
            # 创建测试工作流
            workflow_data = {
                "name": "Test Workflow",
                "description": "Automated test workflow",
                "definition": {
                    "nodes": [
                        {
                            "id": "start",
                            "type": "start",
                            "config": {}
                        },
                        {
                            "id": "coordinator",
                            "type": "agent",
                            "config": {},
                            "agent_config": {
                                "name": "test_coordinator",
                                "role": "coordinator",
                                "tools": []
                            }
                        },
                        {
                            "id": "worker",
                            "type": "agent",
                            "config": {},
                            "agent_config": {
                                "name": "test_worker",
                                "role": "worker",
                                "tools": []
                            }
                        },
                        {
                            "id": "end",
                            "type": "end",
                            "config": {}
                        }
                    ],
                    "edges": [
                        {"from_node": "start", "to_node": "coordinator"},
                        {"from_node": "coordinator", "to_node": "worker"},
                        {"from_node": "worker", "to_node": "end"}
                    ]
                }
            }
            
            # 创建工作流
            response = requests.post(
                f"{self.api_base_url}/api/workflows",
                json=workflow_data
            )
            
            if response.status_code == 200:
                self.print_status("Created test workflow", True)
                workflow = response.json()
                
                # 激活工作流
                update_response = requests.put(
                    f"{self.api_base_url}/api/workflows/{workflow['id']}",
                    json={"status": "active"}
                )
                
                if update_response.status_code == 200:
                    self.print_status("Activated workflow", True)
                    
                    # 执行工作流
                    exec_response = requests.post(
                        f"{self.api_base_url}/api/executions",
                        json={
                            "workflow_id": workflow['id'],
                            "input_data": {"test": "data"}
                        }
                    )
                    
                    if exec_response.status_code == 200:
                        self.print_status("Started workflow execution", True)
                        execution = exec_response.json()
                        
                        # 等待执行完成
                        time.sleep(3)
                        
                        # 检查执行状态
                        status_response = requests.get(
                            f"{self.api_base_url}/api/executions/{execution['id']}"
                        )
                        
                        if status_response.status_code == 200:
                            self.print_status("Workflow execution completed", True)
                            return True
                        else:
                            self.print_status("Failed to get execution status", False)
                    else:
                        self.print_status("Failed to execute workflow", False)
                else:
                    self.print_status("Failed to activate workflow", False)
            else:
                self.print_status(f"Failed to create workflow: {response.text}", False)
                
        except Exception as e:
            self.print_status(f"Workflow test failed: {e}", False)
            
        return False
        
    def test_agent_system(self) -> bool:
        """测试Agent系统"""
        self.print_header("Testing Agent System")
        
        try:
            # 运行Agent测试
            result = subprocess.run(
                [sys.executable, 'tests/test_agents.py'],
                capture_output=True,
                text=True,
                cwd=os.path.dirname(__file__)
            )
            
            if result.returncode == 0:
                self.print_status("Agent system tests passed", True)
                return True
            else:
                self.print_status(f"Agent tests failed: {result.stderr}", False)
                return False
                
        except Exception as e:
            self.print_status(f"Failed to run agent tests: {e}", False)
            return False
            
    def cleanup(self):
        """清理资源"""
        if self.backend_process:
            self.backend_process.terminate()
            self.backend_process.wait()
            self.print_status("Stopped backend service", True)
            
    def run_all_tests(self):
        """运行所有测试"""
        self.print_header("Multi-Agent System Test Suite")
        
        try:
            # 1. 检查环境
            if not self.check_python_version():
                return False
                
            if not self.check_dependencies():
                print("\nPlease install missing dependencies first.")
                return False
                
            # 2. 设置环境
            self.setup_environment()
            
            # 3. 安装依赖
            if not self.install_backend_deps():
                return False
                
            # 4. 启动后端
            if not self.start_backend():
                return False
                
            # 5. 测试API
            api_ok = self.test_api_endpoints()
            
            # 6. 测试工作流
            workflow_ok = self.test_workflow_creation()
            
            # 7. 测试Agent系统
            agent_ok = self.test_agent_system()
            
            # 总结
            self.print_header("Test Summary")
            
            total_tests = 3
            passed_tests = sum([api_ok, workflow_ok, agent_ok])
            
            print(f"Total tests: {total_tests}")
            print(f"Passed: {passed_tests}")
            print(f"Failed: {total_tests - passed_tests}")
            
            if passed_tests == total_tests:
                print("\n✅ All tests passed! System is ready for use.")
                print("\nAccess the system at:")
                print("- Frontend: http://localhost:3000")
                print("- API Docs: http://localhost:8000/docs")
                return True
            else:
                print("\n❌ Some tests failed. Please check the errors above.")
                return False
                
        except KeyboardInterrupt:
            print("\n\nTest interrupted by user.")
            return False
        finally:
            self.cleanup()


if __name__ == "__main__":
    tester = SystemTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)