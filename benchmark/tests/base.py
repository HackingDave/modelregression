from dataclasses import dataclass, field
from typing import Optional
import re
import json

@dataclass
class EvalResult:
    score: float  # 0-100
    details: dict = field(default_factory=dict)

@dataclass
class BaseTest:
    id: str
    name: str
    category_id: str
    description: str
    prompt: str
    eval_type: str  # 'regex', 'llm_judge', 'code_exec', 'composite'
    system_prompt: str = "You are a helpful assistant. Respond directly to the task."
    max_score: float = 100.0

    def evaluate(self, model_output: str, judge_fn=None) -> EvalResult:
        """Evaluate model output. judge_fn is a callback for llm_judge evals."""
        if self.eval_type == 'regex':
            return self._eval_regex(model_output)
        elif self.eval_type == 'llm_judge':
            return self._eval_llm_judge(model_output, judge_fn)
        elif self.eval_type == 'composite':
            return self._eval_composite(model_output, judge_fn)
        else:
            # Default: llm_judge
            return self._eval_llm_judge(model_output, judge_fn)

    def _eval_regex(self, output: str) -> EvalResult:
        """Override in subclass or use eval_config"""
        return EvalResult(score=50.0, details={"method": "regex_default"})

    def _eval_llm_judge(self, output: str, judge_fn) -> EvalResult:
        """Use an LLM to judge the output against a rubric"""
        if judge_fn is None:
            return EvalResult(score=50.0, details={"error": "no_judge_fn"})

        rubric = self._get_judge_rubric()
        judge_prompt = f"""You are an expert evaluator. Score the following AI model output on a scale of 0-100.

TASK GIVEN TO THE MODEL:
{self.prompt}

MODEL'S OUTPUT:
{output}

SCORING RUBRIC:
{rubric}

Respond with ONLY a JSON object in this exact format:
{{"score": <number 0-100>, "reasoning": "<brief explanation>", "breakdown": {{"criteria1": <score>, "criteria2": <score>}}}}"""

        judge_response = judge_fn(judge_prompt)
        try:
            result = json.loads(judge_response)
            return EvalResult(
                score=min(100, max(0, float(result.get("score", 50)))),
                details=result
            )
        except (json.JSONDecodeError, ValueError, TypeError):
            # Try to extract score from text
            match = re.search(r'"score"\s*:\s*(\d+(?:\.\d+)?)', judge_response)
            if match:
                return EvalResult(score=float(match.group(1)), details={"raw": judge_response[:500]})
            return EvalResult(score=50.0, details={"error": "parse_failed", "raw": judge_response[:500]})

    def _eval_composite(self, output: str, judge_fn) -> EvalResult:
        """Combine regex checks with LLM judge"""
        regex_result = self._eval_regex(output)
        judge_result = self._eval_llm_judge(output, judge_fn)

        combined_score = (regex_result.score * 0.4) + (judge_result.score * 0.6)
        return EvalResult(
            score=combined_score,
            details={
                "regex_score": regex_result.score,
                "judge_score": judge_result.score,
                "regex_details": regex_result.details,
                "judge_details": judge_result.details,
            }
        )

    def _get_judge_rubric(self) -> str:
        """Override in subclass to provide specific rubric"""
        return "Score based on correctness, completeness, and quality of the response."
