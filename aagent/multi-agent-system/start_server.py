#!/usr/bin/env python3
"""
简单的服务器启动脚本
"""
import os
import sys
import uvicorn

# 设置环境变量
os.environ['CLAUDE_API_KEY'] = 'sk-jQf4913d0436e88518954e0671c33c454484d916f13NqK25'
os.environ['CLAUDE_API_BASE_URL'] = 'https://api.gptsapi.net/v1'
os.environ['DATABASE_URL'] = 'sqlite+aiosqlite:///test.db'
os.environ['REDIS_URL'] = 'redis://localhost:6379'
os.environ['SECRET_KEY'] = 'test-secret-key-for-development'

# 添加backend目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

print("=" * 60)
print("Starting Multi-Agent System API Server".center(60))
print("=" * 60)

print("\n✅ Environment configured")
print("✅ Starting server...")
print("\n🌐 Access the API at:")
print("   - http://localhost:8000")
print("   - API Docs: http://localhost:8000/docs")
print("   - Health Check: http://localhost:8000/api/health")
print("\n⚠️  Press Ctrl+C to stop the server\n")

# 运行服务器
if __name__ == "__main__":
    try:
        # 切换到backend目录
        os.chdir('backend')
        
        # 启动服务器
        uvicorn.run(
            "main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n\n✋ Server stopped by user")
    except Exception as e:
        print(f"\n❌ Error starting server: {e}")
        sys.exit(1)