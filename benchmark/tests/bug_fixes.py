import re
from .base import BaseTest, EvalResult


class PaginationOffByOne(BaseTest):
    """bf-1: Off-by-one in pagination calculation."""

    def _eval_regex(self, output: str) -> EvalResult:
        score = 0.0
        details = {"checks": {}}

        # Check for math.ceil or ceiling division
        if re.search(r'math\.ceil|import\s+math|ceil\(', output):
            score += 25.0
            details["checks"]["uses_ceil"] = True
        else:
            details["checks"]["uses_ceil"] = False

        # Check for alternative ceiling division: -(-a // b) or (a + b - 1) // b
        if re.search(r'-\s*\(\s*-\s*\w+\s*//|(?:\w+\s*\+\s*\w+\s*-\s*1\s*)\s*//', output):
            score += 25.0
            details["checks"]["alt_ceiling_div"] = True
        else:
            details["checks"]["alt_ceiling_div"] = False

        # Check that they identify the bug location (total_pages line)
        if re.search(r'total_pages', output):
            score += 15.0
            details["checks"]["identifies_total_pages"] = True
        else:
            details["checks"]["identifies_total_pages"] = False

        # Check for edge case discussion (e.g., 0 items, page_size=1)
        if re.search(r'(?:edge\s*case|0\s*items|empty|page_size\s*(?:of|=)\s*1|zero)', output, re.IGNORECASE):
            score += 15.0
            details["checks"]["edge_case_discussion"] = True
        else:
            details["checks"]["edge_case_discussion"] = False

        # Check they mention the problem: last page items get lost
        if re.search(r'(?:last\s*page|remainder|truncat|floor|integer\s*division|round.*down)', output, re.IGNORECASE):
            score += 20.0
            details["checks"]["explains_problem"] = True
        else:
            details["checks"]["explains_problem"] = False

        return EvalResult(score=min(100.0, score), details=details)

    def _get_judge_rubric(self) -> str:
        return """Score the response on these criteria (total 100 points):
- Correctly identifies the bug: integer division truncates, losing remainder items (20 points)
- Correctly fixes total_pages to use math.ceil() or equivalent ceiling division (25 points)
- Provides the corrected code that is syntactically valid and runnable (20 points)
- Explains WHY the bug causes problems with a concrete example (e.g., 23 items / 10 per page
  = 2 pages but should be 3) (15 points)
- Handles edge cases: 0 total items, page_size larger than total_items,
  exact multiple (e.g., 20 items / 10 per page = 2 pages exactly) (10 points)
- Does not introduce new bugs in the fix (10 points)
Deduct 30 points if the fix is wrong or introduces another off-by-one."""


class AsyncRaceCondition(BaseTest):
    """bf-2: Race condition in async Python counter."""

    def _get_judge_rubric(self) -> str:
        return """Score the response on these criteria (total 100 points):
- Correctly identifies the race condition: read-modify-write of shared_counter
  without synchronization allows lost updates (20 points)
- Provides fix using asyncio.Lock to protect the critical section (25 points)
- Lock is acquired BEFORE reading the counter and released AFTER writing,
  covering the entire read-modify-write sequence (15 points)
- Uses `async with lock:` context manager syntax (not manual acquire/release) (5 points)
- Explains why this is a problem: even though Python has the GIL, asyncio tasks
  yield at await points, allowing interleaving between the read and write (20 points)
- Provides corrected code that preserves the original async structure (10 points)
- Does not suggest threading.Lock (which would be wrong for asyncio) (5 points)
Deduct 20 points if the explanation claims "GIL prevents race conditions in asyncio."
Deduct 15 points if the lock does not cover both the read and the write."""


class MemoryLeakEventHandler(BaseTest):
    """bf-3: Memory leak from missing event handler cleanup."""

    def _get_judge_rubric(self) -> str:
        return """Score the response on these criteria (total 100 points):
- Correctly identifies the memory leak: addEventListener in useEffect without a
  cleanup function means handlers accumulate on every re-render (20 points)
- Provides fix with a useEffect cleanup function that calls removeEventListener
  with the SAME function reference (25 points)
- Explains that the handler function must be a named reference (not an anonymous
  arrow in addEventListener) so removeEventListener can match it (15 points)
- Demonstrates proper useEffect cleanup pattern: return () => { removeEventListener(...) } (15 points)
- Mentions the dependency array and its role in controlling when the effect
  re-runs and when cleanup fires (10 points)
- Corrected code is syntactically valid React/JSX (10 points)
- Mentions that in React 18 Strict Mode, effects mount/unmount/remount in dev,
  making this bug more visible (5 points)
Deduct 20 points if removeEventListener uses a different function reference than addEventListener."""


# ── Build test instances ──────────────────────────────────────────────

_bf1 = PaginationOffByOne(
    id="bf-1",
    name="Off-by-one in Pagination",
    category_id="bug-fixes",
    description="Fix an off-by-one error in a pagination utility where the last page of items is lost.",
    eval_type="composite",
    prompt="""The following Python pagination utility has a bug. Users report that when they have 23 items with 10 per page, the items on page 3 (items 21-23) never appear. Find the bug, explain it clearly, and provide the corrected code.

```python
class Paginator:
    def __init__(self, items: list, page_size: int = 10):
        self.items = items
        self.page_size = page_size
        self.total_items = len(items)
        self.total_pages = self.total_items / self.page_size  # BUG IS HERE

    def get_page(self, page_number: int) -> dict:
        \"\"\"Return items for the given page number (1-indexed).\"\"\"
        if page_number < 1 or page_number > self.total_pages:
            return {"items": [], "page": page_number, "total_pages": self.total_pages}

        start = (page_number - 1) * self.page_size
        end = start + self.page_size
        return {
            "items": self.items[start:end],
            "page": page_number,
            "total_pages": self.total_pages,
        }

    def has_next(self, page_number: int) -> bool:
        return page_number < self.total_pages

    def has_previous(self, page_number: int) -> bool:
        return page_number > 1
```

Test case that fails:
```python
items = list(range(1, 24))  # 23 items
p = Paginator(items, page_size=10)
print(p.total_pages)       # Prints 2.3 — should be 3
print(p.get_page(3))       # Returns empty — should return items 21-23
print(p.has_next(2))       # Returns False — should return True
```

Your response should:
1. Identify the exact line with the bug and explain why it is wrong.
2. Explain the root cause (integer vs float division and why truncation/float loses the remainder).
3. Provide the COMPLETE corrected class with the fix applied.
4. Show that the fix works with the test case above.
5. Discuss additional edge cases the fix should handle (0 items, exact multiples, page_size > total_items).""",
)

_bf2 = AsyncRaceCondition(
    id="bf-2",
    name="Async Race Condition",
    category_id="bug-fixes",
    description="Fix a race condition in an asynchronous Python counter that produces incorrect counts.",
    eval_type="llm_judge",
    prompt="""The following async Python code has a race condition. When 100 tasks each increment the counter 100 times, the final count should be 10,000 but it often comes out lower (e.g., 9,823 or 9,947). Find the race condition, explain why it happens even with Python's GIL, and fix it.

```python
import asyncio

shared_counter = 0

async def increment(n: int):
    global shared_counter
    for _ in range(n):
        current = shared_counter
        await asyncio.sleep(0)  # Simulate async work / yield control
        shared_counter = current + 1

async def main():
    tasks = [asyncio.create_task(increment(100)) for _ in range(100)]
    await asyncio.gather(*tasks)
    print(f"Final counter: {shared_counter}")  # Expected: 10000

asyncio.run(main())
```

Your response should:
1. Identify the exact race condition — which lines form the critical section and where the interleaving occurs.
2. Explain why Python's GIL does NOT prevent this race condition in asyncio (the key insight is about await points as yield points in cooperative multitasking).
3. Provide the corrected code using the appropriate asyncio synchronization primitive.
4. Ensure the lock/synchronization covers the ENTIRE read-modify-write sequence, not just part of it.
5. Show the corrected `increment` function and explain why the fix works.
6. Do NOT suggest using threading.Lock — this is asyncio, not threading.""",
)

_bf3 = MemoryLeakEventHandler(
    id="bf-3",
    name="Memory Leak in Event Handler",
    category_id="bug-fixes",
    description="Fix a React component that leaks memory by not cleaning up event listeners on unmount.",
    eval_type="llm_judge",
    prompt="""The following React component has a memory leak. Users report that after navigating away from and back to this page several times, the browser becomes increasingly slow and laggy. Identify the memory leak, explain why it happens, and provide the corrected code.

```jsx
import React, { useState, useEffect } from 'react';

function ScrollTracker() {
    const [scrollY, setScrollY] = useState(0);
    const [scrollDirection, setScrollDirection] = useState('none');
    const [lastScrollY, setLastScrollY] = useState(0);

    useEffect(() => {
        window.addEventListener('scroll', () => {
            const currentScrollY = window.scrollY;
            setScrollDirection(currentScrollY > lastScrollY ? 'down' : 'up');
            setLastScrollY(currentScrollY);
            setScrollY(currentScrollY);
        });

        window.addEventListener('resize', () => {
            console.log('Window resized, recalculating...');
            setScrollY(window.scrollY);
        });
    });

    return (
        <div style={{ position: 'fixed', top: 10, right: 10, padding: '10px', background: '#333', color: '#fff' }}>
            <p>Scroll Y: {scrollY}</p>
            <p>Direction: {scrollDirection}</p>
        </div>
    );
}

export default ScrollTracker;
```

Your response should:
1. Identify ALL the issues causing the memory leak (there are at least two major problems).
2. Explain the lifecycle: why missing cleanup and missing dependency array cause handlers to accumulate.
3. Explain why using anonymous arrow functions inside addEventListener is a problem for cleanup.
4. Provide the COMPLETE corrected component with proper useEffect cleanup, dependency array, and named handler references.
5. Mention how React 18 Strict Mode in development double-invokes effects, making this bug more visible during development.
6. Ensure the corrected code has the same functionality as the original.""",
)


BUG_FIXES_TESTS = [_bf1, _bf2, _bf3]
