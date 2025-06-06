from typing import Dict, Any, List
import json
from datetime import datetime
from .base_agent import BaseAgent, AgentConfig, AgentOutput


class ValidatorAgent(BaseAgent):
    """Validator agent responsible for verifying and validating results"""
    
    def __init__(self, config: AgentConfig):
        # Set validator-specific system prompt
        if not config.system_prompt:
            config.system_prompt = """You are a meticulous validator responsible for:
1. Verifying the accuracy and completeness of work
2. Checking compliance with requirements and standards
3. Validating data integrity and consistency
4. Identifying errors, gaps, or quality issues
5. Providing detailed validation reports

When validating:
- Be thorough and systematic in your checks
- Apply objective criteria consistently
- Document all findings clearly
- Provide constructive feedback
- Suggest improvements where needed

Format validation results in structured JSON when possible."""
        
        config.role = "validator"
        super().__init__(config)
        
        self.validation_criteria = {
            "accuracy": 0.95,
            "completeness": 0.90,
            "consistency": 0.95,
            "compliance": 1.0
        }
        self.validation_history = []
    
    async def process(self, task: Dict[str, Any]) -> AgentOutput:
        """Process a validation task"""
        try:
            task_type = task.get("type", "validate")
            
            if task_type == "validate_output":
                return await self._validate_output(task)
            elif task_type == "validate_data":
                return await self._validate_data(task)
            elif task_type == "validate_compliance":
                return await self._validate_compliance(task)
            elif task_type == "validate_workflow":
                return await self._validate_workflow(task)
            elif task_type == "final_review":
                return await self._final_review(task)
            else:
                return await self._validate_general(task)
                
        except Exception as e:
            self.logger.error(f"Error processing validation task: {str(e)}")
            return AgentOutput(
                success=False,
                data=None,
                error=str(e)
            )
    
    async def _validate_output(self, task: Dict[str, Any]) -> AgentOutput:
        """Validate work output against requirements"""
        output = task.get("output", {})
        requirements = task.get("requirements", {})
        worker_id = task.get("worker_id")
        
        prompt = f"""Validate the following output against requirements:

Output to Validate:
{json.dumps(output, indent=2)}

Requirements:
{json.dumps(requirements, indent=2)}

Worker: {worker_id}

Perform comprehensive validation:
1. Check if all requirements are met
2. Verify accuracy of information
3. Assess completeness and thoroughness
4. Check for consistency throughout
5. Identify any errors or issues

Provide validation results in JSON format:
{{
    "validation_passed": true/false,
    "scores": {{
        "accuracy": 0-1,
        "completeness": 0-1,
        "consistency": 0-1,
        "compliance": 0-1
    }},
    "requirements_status": {{
        "requirement_id": {{"met": true/false, "notes": ""}}
    }},
    "issues_found": [
        {{"type": "", "severity": "low/medium/high", "description": "", "location": ""}}
    ],
    "recommendations": []
}}"""
        
        response = await self.think(prompt)
        
        try:
            validation_result = json.loads(response)
            
            # Apply validation criteria
            passed = self._check_against_criteria(validation_result["scores"])
            validation_result["validation_passed"] = passed
            
            # Record validation
            self.validation_history.append({
                "timestamp": datetime.now().isoformat(),
                "task_id": task.get("id"),
                "result": validation_result
            })
            
            # Send feedback to worker if validation failed
            if not passed:
                await self.send_message(
                    to_agent=worker_id,
                    content={
                        "type": "validation_feedback",
                        "passed": False,
                        "issues": validation_result["issues_found"],
                        "recommendations": validation_result["recommendations"]
                    },
                    message_type="feedback"
                )
            
            return AgentOutput(
                success=True,
                data=validation_result,
                metadata={
                    "validated_at": datetime.now().isoformat(),
                    "worker_id": worker_id
                }
            )
            
        except json.JSONDecodeError:
            return AgentOutput(
                success=True,
                data={"validation_notes": response},
                metadata={"format": "text"}
            )
    
    async def _validate_data(self, task: Dict[str, Any]) -> AgentOutput:
        """Validate data integrity and consistency"""
        data = task.get("data", {})
        schema = task.get("schema", {})
        rules = task.get("validation_rules", {})
        
        prompt = f"""Validate the following data:

Data:
{json.dumps(data, indent=2)}

Schema (if provided):
{json.dumps(schema, indent=2)}

Validation Rules:
{json.dumps(rules, indent=2)}

Check for:
1. Data type correctness
2. Required fields presence
3. Value ranges and constraints
4. Referential integrity
5. Business logic rules
6. Data consistency

Provide detailed validation report in JSON format."""
        
        response = await self.think(prompt)
        
        try:
            validation_report = json.loads(response)
            
            return AgentOutput(
                success=True,
                data=validation_report,
                metadata={
                    "data_size": len(str(data)),
                    "rules_applied": len(rules)
                }
            )
            
        except json.JSONDecodeError:
            return AgentOutput(
                success=True,
                data={"validation_report": response},
                metadata={"format": "text"}
            )
    
    async def _validate_compliance(self, task: Dict[str, Any]) -> AgentOutput:
        """Validate compliance with standards and regulations"""
        content = task.get("content", {})
        standards = task.get("standards", [])
        regulations = task.get("regulations", [])
        
        prompt = f"""Validate compliance with standards and regulations:

Content to Validate:
{json.dumps(content, indent=2)}

Standards:
{json.dumps(standards, indent=2)}

Regulations:
{json.dumps(regulations, indent=2)}

Check for:
1. Full compliance with all standards
2. Regulatory requirement adherence
3. Policy violations
4. Best practice alignment
5. Documentation completeness

Provide compliance validation report in JSON format:
{{
    "compliant": true/false,
    "standards_compliance": {{
        "standard_name": {{"compliant": true/false, "gaps": []}}
    }},
    "regulatory_compliance": {{
        "regulation_name": {{"compliant": true/false, "violations": []}}
    }},
    "risk_assessment": {{
        "level": "low/medium/high",
        "factors": []
    }},
    "remediation_required": []
}}"""
        
        response = await self.think(prompt)
        
        try:
            compliance_report = json.loads(response)
            
            # High severity if not compliant
            if not compliance_report.get("compliant", True):
                self.logger.warning("Compliance validation failed")
            
            return AgentOutput(
                success=True,
                data=compliance_report,
                metadata={
                    "standards_count": len(standards),
                    "regulations_count": len(regulations)
                }
            )
            
        except json.JSONDecodeError:
            return AgentOutput(
                success=True,
                data={"compliance_notes": response},
                metadata={"format": "text"}
            )
    
    async def _validate_workflow(self, task: Dict[str, Any]) -> AgentOutput:
        """Validate an entire workflow execution"""
        workflow_id = task.get("workflow_id")
        execution_data = task.get("execution_data", {})
        expected_outcomes = task.get("expected_outcomes", {})
        
        prompt = f"""Validate the workflow execution:

Workflow ID: {workflow_id}
Execution Data:
{json.dumps(execution_data, indent=2)}

Expected Outcomes:
{json.dumps(expected_outcomes, indent=2)}

Validate:
1. All nodes executed successfully
2. Data flow between nodes is correct
3. Expected outcomes are achieved
4. No errors or exceptions
5. Performance within acceptable limits

Provide workflow validation report."""
        
        response = await self.think(prompt)
        
        return AgentOutput(
            success=True,
            data={
                "workflow_validation": response,
                "workflow_id": workflow_id,
                "validated_at": datetime.now().isoformat()
            }
        )
    
    async def _final_review(self, task: Dict[str, Any]) -> AgentOutput:
        """Perform final review before approval"""
        deliverables = task.get("deliverables", {})
        requirements = task.get("original_requirements", {})
        validation_history = task.get("validation_history", [])
        
        prompt = f"""Perform final review of deliverables:

Deliverables:
{json.dumps(deliverables, indent=2)}

Original Requirements:
{json.dumps(requirements, indent=2)}

Previous Validations:
{json.dumps(validation_history, indent=2)}

Conduct final review:
1. Verify all requirements are fully met
2. Check overall quality and consistency
3. Ensure all issues have been resolved
4. Validate documentation completeness
5. Confirm readiness for delivery

Provide final approval decision and summary."""
        
        response = await self.think(prompt)
        
        return AgentOutput(
            success=True,
            data={
                "final_review": response,
                "approval_timestamp": datetime.now().isoformat(),
                "reviewer": self.id
            }
        )
    
    async def _validate_general(self, task: Dict[str, Any]) -> AgentOutput:
        """Handle general validation tasks"""
        prompt = f"""As a validator, handle the following validation task:

{json.dumps(task, indent=2)}

Perform thorough validation and provide detailed results."""
        
        response = await self.think(prompt)
        
        return AgentOutput(
            success=True,
            data={"validation_result": response}
        )
    
    def _check_against_criteria(self, scores: Dict[str, float]) -> bool:
        """Check scores against validation criteria"""
        for metric, threshold in self.validation_criteria.items():
            if metric in scores and scores[metric] < threshold:
                return False
        return True
    
    def get_validation_statistics(self) -> Dict[str, Any]:
        """Get validation statistics"""
        total_validations = len(self.validation_history)
        passed_validations = sum(
            1 for v in self.validation_history
            if v["result"].get("validation_passed", False)
        )
        
        return {
            "total_validations": total_validations,
            "passed_validations": passed_validations,
            "pass_rate": passed_validations / total_validations if total_validations > 0 else 0,
            "validation_criteria": self.validation_criteria,
            "recent_validations": self.validation_history[-5:]
        }