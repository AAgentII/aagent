import pytest
import asyncio
from backend.core.agents import (
    AgentConfig, AgentOutput,
    CoordinatorAgent, SupervisorAgent, 
    WorkerAgent, ValidatorAgent
)


@pytest.mark.asyncio
async def test_coordinator_agent_task_decomposition():
    """测试协调者Agent的任务分解能力"""
    config = AgentConfig(
        name="test_coordinator",
        role="coordinator"
    )
    
    coordinator = CoordinatorAgent(config)
    
    # 测试任务分解
    task = {
        "type": "decompose",
        "description": "Build a web scraper that collects product information from an e-commerce site",
        "requirements": {
            "output_format": "JSON",
            "data_fields": ["name", "price", "description", "image_url"],
            "error_handling": "retry with exponential backoff"
        }
    }
    
    result = await coordinator.process(task)
    
    assert result.success
    assert "subtasks" in result.data
    assert len(result.data["subtasks"]) > 0
    assert "execution_order" in result.data
    
    # 验证子任务包含必要字段
    for subtask in result.data["subtasks"]:
        assert "id" in subtask
        assert "name" in subtask
        assert "description" in subtask
        assert "required_role" in subtask


@pytest.mark.asyncio
async def test_worker_agent_execution():
    """测试工作者Agent的任务执行能力"""
    config = AgentConfig(
        name="test_worker",
        role="worker"
    )
    
    worker = WorkerAgent(config)
    
    # 测试代码编写任务
    task = {
        "type": "code",
        "language": "python",
        "specifications": "Create a function that calculates factorial",
        "requirements": {
            "function_name": "factorial",
            "input_validation": True,
            "handle_negative": True
        }
    }
    
    result = await worker.process(task)
    
    assert result.success
    assert "code" in result.data
    assert "factorial" in result.data["code"]
    assert "def" in result.data["code"]


@pytest.mark.asyncio
async def test_supervisor_monitoring():
    """测试监督者Agent的监控能力"""
    config = AgentConfig(
        name="test_supervisor",
        role="supervisor"
    )
    
    supervisor = SupervisorAgent(config)
    
    # 测试执行监控
    task = {
        "type": "monitor",
        "worker_id": "worker_123",
        "task_id": "task_456",
        "execution_data": {
            "progress": 0.6,
            "current_step": "processing data",
            "elapsed_time": 120
        }
    }
    
    result = await supervisor.process(task)
    
    assert result.success
    assert "progress_percentage" in result.data
    assert "quality_assessment" in result.data
    assert "intervention_needed" in result.data


@pytest.mark.asyncio
async def test_validator_validation():
    """测试验证者Agent的验证能力"""
    config = AgentConfig(
        name="test_validator",
        role="validator"
    )
    
    validator = ValidatorAgent(config)
    
    # 测试输出验证
    task = {
        "type": "validate_output",
        "output": {
            "result": "Factorial of 5 is 120",
            "execution_time": 0.001
        },
        "requirements": {
            "must_return_number": True,
            "max_execution_time": 1.0
        },
        "worker_id": "worker_123"
    }
    
    result = await validator.process(task)
    
    assert result.success
    assert "validation_passed" in result.data
    assert "scores" in result.data
    assert "requirements_status" in result.data


@pytest.mark.asyncio
async def test_agent_communication():
    """测试Agent之间的通信"""
    coordinator = CoordinatorAgent(AgentConfig(name="coord", role="coordinator"))
    worker = WorkerAgent(AgentConfig(name="work", role="worker"))
    
    # 发送消息
    message = await coordinator.send_message(
        to_agent=worker.id,
        content={"task": "test_task"},
        message_type="task"
    )
    
    assert message.from_agent == coordinator.id
    assert message.to_agent == worker.id
    assert message.content["task"] == "test_task"
    
    # 接收消息
    await worker.receive_message(message)
    
    # 等待消息
    received = await worker.wait_for_message(timeout=1.0)
    assert received is not None
    assert received.content["task"] == "test_task"


@pytest.mark.asyncio
async def test_multi_agent_collaboration():
    """测试多Agent协作完成复杂任务"""
    # 创建Agent团队
    coordinator = CoordinatorAgent(AgentConfig(name="coordinator", role="coordinator"))
    supervisor = SupervisorAgent(AgentConfig(name="supervisor", role="supervisor"))
    worker1 = WorkerAgent(AgentConfig(name="worker1", role="worker"))
    worker2 = WorkerAgent(AgentConfig(name="worker2", role="worker"))
    validator = ValidatorAgent(AgentConfig(name="validator", role="validator"))
    
    # 协调者分解任务
    main_task = {
        "type": "decompose",
        "description": "Analyze customer reviews and generate insights report",
        "requirements": {
            "data_source": "reviews.csv",
            "analysis_types": ["sentiment", "topics", "trends"],
            "output_format": "report"
        }
    }
    
    decomposition = await coordinator.process(main_task)
    assert decomposition.success
    
    subtasks = decomposition.data.get("subtasks", [])
    
    # 为每个子任务分配Worker
    results = []
    for i, subtask in enumerate(subtasks[:2]):  # 处理前两个子任务
        worker = worker1 if i == 0 else worker2
        
        # Worker执行任务
        worker_task = {
            "type": "execute",
            "description": subtask["description"],
            "requirements": subtask.get("requirements", {})
        }
        
        # 监督者监控执行
        monitor_task = {
            "type": "monitor",
            "worker_id": worker.id,
            "task_id": subtask["id"],
            "execution_data": {"progress": 0.5}
        }
        
        monitor_result = await supervisor.process(monitor_task)
        assert monitor_result.success
        
        # Worker完成任务
        work_result = await worker.process(worker_task)
        results.append(work_result)
        
        # 验证者验证结果
        validation_task = {
            "type": "validate_output",
            "output": work_result.data,
            "requirements": subtask.get("requirements", {}),
            "worker_id": worker.id
        }
        
        validation = await validator.process(validation_task)
        assert validation.success
    
    # 验证所有结果
    assert all(r.success for r in results)
    print("Multi-agent collaboration test passed!")


if __name__ == "__main__":
    # 运行所有测试
    asyncio.run(test_coordinator_agent_task_decomposition())
    asyncio.run(test_worker_agent_execution())
    asyncio.run(test_supervisor_monitoring())
    asyncio.run(test_validator_validation())
    asyncio.run(test_agent_communication())
    asyncio.run(test_multi_agent_collaboration())