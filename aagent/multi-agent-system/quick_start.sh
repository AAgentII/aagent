#!/bin/bash
# 多Agent系统快速启动脚本

echo "=========================================="
echo "   Multi-Agent System Quick Start"
echo "=========================================="

# 设置颜色
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 检查Python版本
echo -e "\n${GREEN}[1/5]${NC} Checking Python version..."
python_version=$(python3 --version 2>&1 | grep -oE '[0-9]+\.[0-9]+')
if [[ $(echo "$python_version >= 3.11" | bc) -eq 1 ]]; then
    echo -e "${GREEN}✓${NC} Python $python_version"
else
    echo -e "${RED}✗${NC} Python 3.11+ required, found $python_version"
    exit 1
fi

# 设置环境变量
echo -e "\n${GREEN}[2/5]${NC} Setting environment variables..."
export CLAUDE_API_KEY='sk-jQf4913d0436e88518954e0671c33c454484d916f13NqK25'
export CLAUDE_API_BASE_URL='https://api.gptsapi.net/v1'
export DATABASE_URL='sqlite+aiosqlite:///test.db'
export REDIS_URL='redis://localhost:6379'
export SECRET_KEY='test-secret-key-for-development'
echo -e "${GREEN}✓${NC} Environment configured"

# 修复导入问题
echo -e "\n${GREEN}[3/5]${NC} Fixing import paths..."
python3 fix_imports.py

# 安装依赖
echo -e "\n${GREEN}[4/5]${NC} Installing dependencies..."
cd backend
pip install -r requirements.txt --quiet
cd ..

# 启动后端服务
echo -e "\n${GREEN}[5/5]${NC} Starting backend service..."
cd backend
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
cd ..

# 等待服务启动
echo -e "\nWaiting for services to start..."
sleep 5

# 检查服务状态
if curl -s http://localhost:8000/api/health > /dev/null; then
    echo -e "\n${GREEN}✅ System is ready!${NC}"
    echo -e "\n🌐 Access points:"
    echo -e "   - API: http://localhost:8000"
    echo -e "   - API Docs: http://localhost:8000/docs"
    echo -e "   - Health Check: http://localhost:8000/api/health"
    echo -e "\n📝 Quick test commands:"
    echo -e "   - List workflows: curl http://localhost:8000/api/workflows"
    echo -e "   - List agents: curl http://localhost:8000/api/agents"
    echo -e "\n⚡ To stop the system: kill $BACKEND_PID"
else
    echo -e "\n${RED}✗ Failed to start system${NC}"
    kill $BACKEND_PID
    exit 1
fi

# 保持脚本运行
echo -e "\nPress Ctrl+C to stop the system..."
wait $BACKEND_PID