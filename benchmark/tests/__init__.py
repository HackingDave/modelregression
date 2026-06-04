from .base import BaseTest, EvalResult
from .long_reasoning import LONG_REASONING_TESTS
from .coding_tasks import CODING_TASKS_TESTS
from .bug_fixes import BUG_FIXES_TESTS
from .feature_implementation import FEATURE_IMPLEMENTATION_TESTS
from .code_thoroughness import CODE_THOROUGHNESS_TESTS
from .bug_introduction import BUG_INTRODUCTION_TESTS
from .security_awareness import SECURITY_AWARENESS_TESTS
from .instruction_following import INSTRUCTION_FOLLOWING_TESTS
from .code_quality import CODE_QUALITY_TESTS
from .performance_efficiency import PERFORMANCE_EFFICIENCY_TESTS

ALL_TESTS = (
    LONG_REASONING_TESTS +
    CODING_TASKS_TESTS +
    BUG_FIXES_TESTS +
    FEATURE_IMPLEMENTATION_TESTS +
    CODE_THOROUGHNESS_TESTS +
    BUG_INTRODUCTION_TESTS +
    SECURITY_AWARENESS_TESTS +
    INSTRUCTION_FOLLOWING_TESTS +
    CODE_QUALITY_TESTS +
    PERFORMANCE_EFFICIENCY_TESTS
)
