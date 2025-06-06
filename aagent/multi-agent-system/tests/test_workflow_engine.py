import pytest
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from backend.core.workflow.workflow_engine import WorkflowEngine
from backend.models import Base


# 创建测试数据库
@pytest.fixture
async def db_session():
    """创建测试数据库会话"""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async_session = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session
    
    await engine.dispose()


@pytest.mark.asyncio
async def test_simple_workflow_execution(db_session):
    """测试简单工作流执行"""
    engine = WorkflowEngine(db_session)
    
    # 定义简单工作流
    workflow_def = {
        "nodes": [
            {
                "id": "start",
                "type": "start",
                "config": {}
            },
            {
                "id": "worker1",
                "type": "agent",
                "config": {},
                "agent_config": {
                    "name": "worker1",
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
            {
                "from_node": "start",
                "to_node": "worker1"
            },
            {
                "from_node": "worker1",
                "to_node": "end"
            }
        ]
    }
    
    # 加载工作流
    engine.load_workflow(workflow_def)
    
    # 验证图结构
    assert len(engine.graph.nodes()) == 3
    assert len(engine.graph.edges()) == 2
    
    # 执行工作流
    result = await engine.execute({"workflow_id": "test_workflow"})
    
    # 验证执行结果
    assert "worker1" in result
    assert result["worker1"]["success"] is True


@pytest.mark.asyncio
async def test_conditional_workflow(db_session):
    """测试条件分支工作流"""
    engine = WorkflowEngine(db_session)
    
    # 定义条件工作流
    workflow_def = {
        "nodes": [
            {
                "id": "start",
                "type": "start",
                "config": {}
            },
            {
                "id": "condition",
                "type": "condition",
                "config": {
                    "condition": "context['input'].get('value', 0) > 50"
                }
            },
            {
                "id": "worker_high",
                "type": "agent",
                "config": {},
                "agent_config": {
                    "name": "worker_high",
                    "role": "worker",
                    "tools": []
                }
            },
            {
                "id": "worker_low",
                "type": "agent",
                "config": {},
                "agent_config": {
                    "name": "worker_low",
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
            {
                "from_node": "start",
                "to_node": "condition"
            },
            {
                "from_node": "condition",
                "to_node": "worker_high",
                "condition": "context['results']['condition']['result'] == True"
            },
            {
                "from_node": "condition",
                "to_node": "worker_low",
                "condition": "context['results']['condition']['result'] == False"
            },
            {
                "from_node": "worker_high",
                "to_node": "end"
            },
            {
                "from_node": "worker_low",
                "to_node": "end"
            }
        ]
    }
    
    engine.load_workflow(workflow_def)
    
    # 测试高值条件
    result_high = await engine.execute({
        "workflow_id": "test_workflow",
        "value": 75
    })
    
    assert "worker_high" in result_high
    assert "worker_low" not in result_high
    
    # 重新创建引擎实例测试低值条件
    engine2 = WorkflowEngine(db_session)
    engine2.load_workflow(workflow_def)
    
    result_low = await engine2.execute({
        "workflow_id": "test_workflow",
        "value": 25
    })
    
    assert "worker_low" in result_low
    assert "worker_high" not in result_low


@pytest.mark.asyncio
async def test_parallel_workflow(db_session):
    """测试并行执行工作流"""
    engine = WorkflowEngine(db_session)
    
    # 定义并行工作流
    workflow_def = {
        "nodes": [
            {
                "id": "start",
                "type": "start",
                "config": {}
            },
            {
                "id": "parallel",
                "type": "parallel",
                "config": {}
            },
            {
                "id": "worker1",
                "type": "agent",
                "config": {},
                "agent_config": {
                    "name": "worker1",
                    "role": "worker",
                    "tools": []
                }
            },
            {
                "id": "worker2",
                "type": "agent",
                "config": {},
                "agent_config": {
                    "name": "worker2",
                    "role": "worker",
                    "tools": []
                }
            },
            {
                "id": "worker3",
                "type": "agent",
                "config": {},
                "agent_config": {
                    "name": "worker3",
                    "role": "worker",
                    "tools": []
                }
            },
            {
                "id": "join",
                "type": "join",
                "config": {}
            },
            {
                "id": "end",
                "type": "end",
                "config": {}
            }
        ],
        "edges": [
            {
                "from_node": "start",
                "to_node": "parallel"
            },
            {
                "from_node": "parallel",
                "to_node": "worker1"
            },
            {
                "from_node": "parallel",
                "to_node": "worker2"
            },
            {
                "from_node": "parallel",
                "to_node": "worker3"
            },
            {
                "from_node": "worker1",
                "to_node": "join"
            },
            {
                "from_node": "worker2",
                "to_node": "join"
            },
            {
                "from_node": "worker3",
                "to_node": "join"
            },
            {
                "from_node": "join",
                "to_node": "end"
            }
        ]
    }
    
    engine.load_workflow(workflow_def)
    
    # 执行并行工作流
    start_time = asyncio.get_event_loop().time()
    result = await engine.execute({"workflow_id": "test_workflow"})
    end_time = asyncio.get_event_loop().time()
    
    # 验证所有worker都执行了
    assert "worker1" in result
    assert "worker2" in result
    assert "worker3" in result
    
    # 验证join节点执行了
    assert "join" in result
    
    print(f"Parallel execution time: {end_time - start_time:.2f}s")


@pytest.mark.asyncio
async def test_complex_multi_agent_workflow(db_session):
    """测试复杂多Agent协作工作流"""
    engine = WorkflowEngine(db_session)
    
    # 定义复杂工作流：协调者分解任务 -> 多个Worker并行执行 -> 验证者验证 -> 汇总
    workflow_def = {
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
                    "name": "coordinator",
                    "role": "coordinator",
                    "tools": []
                }
            },
            {
                "id": "supervisor",
                "type": "agent",
                "config": {},
                "agent_config": {
                    "name": "supervisor",
                    "role": "supervisor",
                    "tools": []
                }
            },
            {
                "id": "parallel_work",
                "type": "parallel",
                "config": {}
            },
            {
                "id": "worker1",
                "type": "agent",
                "config": {},
                "agent_config": {
                    "name": "worker1",
                    "role": "worker",
                    "tools": ["web_search"]
                }
            },
            {
                "id": "worker2",
                "type": "agent",
                "config": {},
                "agent_config": {
                    "name": "worker2",
                    "role": "worker",
                    "tools": ["data_analyzer"]
                }
            },
            {
                "id": "join_work",
                "type": "join",
                "config": {}
            },
            {
                "id": "validator",
                "type": "agent",
                "config": {},
                "agent_config": {
                    "name": "validator",
                    "role": "validator",
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
            {
                "from_node": "start",
                "to_node": "coordinator"
            },
            {
                "from_node": "coordinator",
                "to_node": "supervisor"
            },
            {
                "from_node": "supervisor",
                "to_node": "parallel_work"
            },
            {
                "from_node": "parallel_work",
                "to_node": "worker1"
            },
            {
                "from_node": "parallel_work",
                "to_node": "worker2"
            },
            {
                "from_node": "worker1",
                "to_node": "join_work"
            },
            {
                "from_node": "worker2",
                "to_node": "join_work"
            },
            {
                "from_node": "join_work",
                "to_node": "validator"
            },
            {
                "from_node": "validator",
                "to_node": "end"
            }
        ]
    }
    
    engine.load_workflow(workflow_def)
    
    # 执行复杂工作流
    input_data = {
        "workflow_id": "complex_workflow",
        "task": "Analyze market trends for AI companies",
        "requirements": {
            "data_sources": ["news", "social_media", "financial_reports"],
            "analysis_depth": "comprehensive",
            "output_format": "executive_summary"
        }
    }
    
    result = await engine.execute(input_data)
    
    # 验证所有Agent都执行了
    assert "coordinator" in result
    assert "supervisor" in result
    assert "worker1" in result
    assert "worker2" in result
    assert "validator" in result
    
    # 验证执行成功
    assert result["coordinator"]["success"]
    assert result["validator"]["success"]
    
    print("Complex multi-agent workflow test passed!")


if __name__ == "__main__":
    # 运行测试
    import sys
    sys.path.append("..")
    
    async def run_tests():
        # 创建内存数据库
        engine = create_async_engine(
            "sqlite+aiosqlite:///:memory:",
            echo=False,
        )
        
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        async_session = async_sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )
        
        async with async_session() as session:
            print("Running simple workflow test...")
            await test_simple_workflow_execution(session)
            
            print("Running conditional workflow test...")
            await test_conditional_workflow(session)
            
            print("Running parallel workflow test...")
            await test_parallel_workflow(session)
            
            print("Running complex multi-agent workflow test...")
            await test_complex_multi_agent_workflow(session)
        
        await engine.dispose()
        print("\nAll tests passed!")
    
    asyncio.run(run_tests())