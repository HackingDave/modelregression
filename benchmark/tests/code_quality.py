import re
from .base import BaseTest, EvalResult


class ShoppingCart(BaseTest):
    """cq-1: Implement a shopping cart class judged on code quality."""

    def _get_judge_rubric(self) -> str:
        return """Score the response on CODE QUALITY, not just correctness (total 100 points):

Naming quality (15 points):
- Class, method, and variable names are descriptive and follow Python conventions (5 points)
- No single-letter variables except in list comprehensions or lambdas (5 points)
- Boolean methods/properties use "is_", "has_", or "can_" prefixes (5 points)

Single Responsibility Principle (15 points):
- Each method does ONE thing (5 points)
- No method is longer than ~15 lines (5 points)
- Cart logic is separate from formatting/display logic (5 points)

DRY (Don't Repeat Yourself) (15 points):
- No duplicated logic across methods (5 points)
- Common operations (finding an item, calculating price) are extracted into helpers (5 points)
- Uses properties or computed values instead of duplicating calculations (5 points)

Type hints (15 points):
- ALL method parameters have type hints (5 points)
- ALL methods have return type annotations (5 points)
- Uses Optional, Union, or other typing constructs where appropriate (5 points)

API design (15 points):
- Methods have intuitive names that describe their action (5 points)
- Consistent return types (e.g., methods that modify the cart return self for chaining,
  or consistently return None) (5 points)
- Sensible error handling: raises specific exceptions with helpful messages (5 points)

Code style (15 points):
- Follows PEP 8 conventions (5 points)
- Has docstrings on the class and all public methods (5 points)
- Uses dataclasses, NamedTuples, or Pydantic for data structures (5 points)

Functionality completeness (10 points):
- add_item, remove_item, update_quantity, get_total, apply_discount, clear (5 points)
- Handles edge cases: negative quantity, removing non-existent item, empty cart total (5 points)

Deduct 10 points for any print() statements instead of return values.
Deduct 10 points for mutable default arguments (e.g., items=[]).
Maximum score is 100."""


class CronExpressionParser(BaseTest):
    """cq-2: Write a cron expression parser judged on readability and decomposition."""

    def _get_judge_rubric(self) -> str:
        return """Score the response on readability and code decomposition (total 100 points):

Readability (30 points):
- Code can be understood by reading it top-down without jumping around (10 points)
- Variable names clearly indicate what they hold (cron_field, not cf or x) (5 points)
- Complex logic has explanatory comments (5 points)
- No "clever" one-liners that sacrifice readability for brevity (5 points)
- Consistent code style throughout (5 points)

Decomposition (30 points):
- Parsing is broken into clear stages: tokenize, validate, expand, describe (10 points)
- Each cron field (minute, hour, day, month, weekday) is parsed by a shared function,
  not duplicated 5 times (10 points)
- Helper functions have single responsibilities (5 points)
- The main parse function is a clear orchestrator, not a monolith (5 points)

Correctness (20 points):
- Handles standard cron expressions: "* * * * *", "0 12 * * 1-5", "*/15 * * * *" (5 points)
- Handles ranges (1-5), lists (1,3,5), steps (*/10), and wildcards (*) (5 points)
- Validates field ranges (minutes 0-59, hours 0-23, etc.) (5 points)
- Raises clear errors for invalid expressions (5 points)

API design (10 points):
- Clean public interface (parse function returns a structured result, not raw data) (5 points)
- Result includes both parsed values and a human-readable description (5 points)

Type hints and documentation (10 points):
- Type hints on all functions (5 points)
- Docstrings explain what each function does and what it returns (5 points)

Deduct 15 points if all parsing is in one giant function with no helpers.
Deduct 10 points if field parsing logic is copy-pasted for each field.
Maximum score is 100."""


class PriorityTaskQueue(BaseTest):
    """cq-3: Design a priority task queue class judged on API design."""

    def _get_judge_rubric(self) -> str:
        return """Score the response on API DESIGN quality (total 100 points):

API intuitiveness (25 points):
- Method names clearly describe what they do (enqueue/add vs push, dequeue/next vs pop) (5 points)
- The API reads like English: queue.add(task, priority=1), queue.next(), queue.peek() (5 points)
- Methods return useful values (add returns the task/id, next returns the task) (5 points)
- Queue size is available as len(queue) via __len__ (5 points)
- Supports iteration via __iter__ (5 points)

Consistency (20 points):
- Consistent parameter ordering across methods (5 points)
- Consistent return types (e.g., all query methods return Task objects) (5 points)
- Consistent error behavior (same exception type for similar errors across methods) (5 points)
- Naming convention is consistent (all snake_case, no mixing) (5 points)

Completeness (20 points):
- Has add/enqueue, next/dequeue, peek (without removal), cancel/remove by id (5 points)
- Has size/is_empty, clear (3 points)
- Supports priority update (reprioritize an existing task) (4 points)
- Has a way to filter or query tasks by status/priority (4 points)
- Supports context manager (with queue as q:) or iteration (4 points)

Error handling (15 points):
- Empty queue operations (dequeue, peek) raise specific exceptions, not generic ones (5 points)
- Invalid priority values are rejected with clear messages (5 points)
- Duplicate task handling is defined (reject, update, or allow) (5 points)

Data modeling (10 points):
- Task is a proper class/dataclass, not a raw dict or tuple (5 points)
- Task has id, payload, priority, created_at, status fields (5 points)

Type safety (10 points):
- Generic type support or clear types (PriorityQueue[Task]) (3 points)
- All methods have type hints (4 points)
- Docstrings on all public methods (3 points)

Deduct 15 points if tasks are stored as raw tuples with magic index numbers.
Deduct 10 points if the API requires the caller to manage internal state.
Maximum score is 100."""


# ── Build test instances ──────────────────────────────────────────────

_cq1 = ShoppingCart(
    id="cq-1",
    name="Shopping Cart Class",
    category_id="code-quality",
    description="Implement a shopping cart class, scored purely on code quality: naming, SRP, DRY, type hints, and style.",
    eval_type="llm_judge",
    prompt="""Implement a ShoppingCart class in Python. This will be scored primarily on CODE QUALITY — naming conventions, adherence to SOLID principles, DRY, type hints, and overall style — not just whether it works.

The cart should support:
1. Adding items (product name, unit price, quantity)
2. Removing items by product name
3. Updating the quantity of an existing item
4. Calculating the subtotal (before discounts)
5. Applying a percentage discount or a flat discount
6. Calculating the final total (after discounts)
7. Listing all items with their details
8. Clearing the cart

Design requirements:
- Represent cart items as a proper data structure (dataclass, NamedTuple, or Pydantic model), NOT raw dicts or tuples.
- Use type hints on ALL method parameters and return types.
- Follow the Single Responsibility Principle: each method should do one thing.
- Follow DRY: extract shared logic into helper methods.
- Use descriptive names for everything — no single-letter variables, no abbreviations.
- Include docstrings on the class and all public methods.
- Handle edge cases with specific, descriptive exceptions (not generic Exception or ValueError("error")).
- NO print statements — methods should return values, not print them.
- NO mutable default arguments.

Provide the complete implementation. Write production-quality code as if it will be reviewed by a senior engineer who cares deeply about code quality.""",
)

_cq2 = CronExpressionParser(
    id="cq-2",
    name="Cron Expression Parser",
    category_id="code-quality",
    description="Write a cron expression parser, scored on readability, decomposition, and code organization.",
    eval_type="llm_judge",
    prompt="""Write a cron expression parser in Python that parses standard 5-field cron expressions and returns both the parsed schedule and a human-readable description. This will be scored on code READABILITY and DECOMPOSITION, not just correctness.

Cron format: "minute hour day_of_month month day_of_week"

Examples:
- "* * * * *" -> "Every minute"
- "0 12 * * 1-5" -> "At 12:00 on Monday through Friday"
- "*/15 * * * *" -> "Every 15 minutes"
- "0 0 1 * *" -> "At midnight on the 1st of every month"
- "30 8 * * 1,3,5" -> "At 08:30 on Monday, Wednesday, and Friday"
- "0 */2 * * *" -> "Every 2 hours, on the hour"

The parser must handle:
- Wildcards: * (any value)
- Ranges: 1-5 (values 1 through 5)
- Lists: 1,3,5 (values 1, 3, and 5)
- Steps: */15 (every 15), 1-30/5 (1 through 30, every 5th)
- Single values: 42 (exactly 42)

Field ranges:
- minute: 0-59
- hour: 0-23
- day_of_month: 1-31
- month: 1-12
- day_of_week: 0-6 (0 = Sunday)

Design requirements:
- Break the parser into clear, well-named helper functions. Do NOT write one monolithic parse function.
- Parsing a single field (handling *, ranges, lists, steps) should be a shared function, not duplicated 5 times.
- Return a structured result (dataclass or similar), not a raw dict.
- Include a `describe()` method that generates a human-readable English description.
- Validate inputs and raise clear errors for invalid expressions.
- Include type hints on ALL functions and return types.
- Code should be readable top-down without needing to jump around.

Provide the complete implementation. Prioritize READABILITY over cleverness.""",
)

_cq3 = PriorityTaskQueue(
    id="cq-3",
    name="Priority Task Queue",
    category_id="code-quality",
    description="Design a priority task queue class, scored on API design quality, consistency, and type safety.",
    eval_type="llm_judge",
    prompt="""Design and implement a PriorityTaskQueue class in Python. This will be scored primarily on API DESIGN quality — how intuitive, consistent, complete, and well-typed the public interface is.

The queue manages tasks with different priority levels. Higher priority tasks are dequeued first. Tasks with equal priority are dequeued in FIFO order.

Required capabilities:
1. Add a task with a payload and priority level
2. Get the next highest-priority task (removes it from the queue)
3. Peek at the next task without removing it
4. Cancel/remove a specific task by ID
5. Update the priority of an existing task
6. Query the queue size and check if it's empty
7. Clear all tasks
8. Filter or list tasks by priority level
9. Iterate over tasks in priority order (without removing them)

Design requirements:
- Define a Task data structure (dataclass) with fields: id, payload, priority, created_at, status
- Task IDs should be auto-generated (UUID or auto-increment)
- Priority is an integer where HIGHER numbers = higher priority
- Support Python protocols: len(queue), iter(queue), bool(queue), repr(queue)
- Methods should have intuitive names that read like English
- Consistent error handling: define custom exceptions (EmptyQueueError, TaskNotFoundError)
- All methods must have type hints and docstrings
- The queue should be usable as a context manager
- Consider making it generic (PriorityTaskQueue[T] where T is the payload type)

Provide the complete implementation including the Task dataclass, custom exceptions, and the PriorityTaskQueue class. Design the API as if it were a library that other developers will use — prioritize discoverability and consistency.""",
)


CODE_QUALITY_TESTS = [_cq1, _cq2, _cq3]
