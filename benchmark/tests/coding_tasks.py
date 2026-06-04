import re
from .base import BaseTest, EvalResult


class TrieImplementation(BaseTest):
    """ct-1: Implement a Trie with insert, search, autocomplete."""

    def _get_judge_rubric(self) -> str:
        return """Score the response on these criteria (total 100 points):
- Correct TrieNode class with a children mapping and an end-of-word flag (10 points)
- Correct insert method that creates nodes character by character and marks word end (15 points)
- Correct search method that traverses the trie and checks end-of-word (15 points)
- Correct autocomplete/starts_with method that collects all words with a given prefix using
  DFS or BFS traversal (20 points)
- Proper Python type hints on all methods (parameters and return types) (10 points)
- Edge case handling: empty string insert/search, prefix longer than any word,
  single-character words, overlapping prefixes (15 points)
- Clean code style: meaningful variable names, docstrings, no unnecessary complexity (10 points)
- Correct time/space complexity discussion or comments (5 points)
Deduct 20 points if the autocomplete returns wrong results. Deduct 15 points if search
returns True for a prefix that is not a complete inserted word."""


class FlaskRESTEndpoint(BaseTest):
    """ct-2: Write a Flask REST endpoint POST /api/transform."""

    def _get_judge_rubric(self) -> str:
        return """Score the response on these criteria (total 100 points):
- Uses Flask correctly: @app.route or Blueprint with POST method (10 points)
- Parses JSON request body with request.get_json() or equivalent (10 points)
- Implements all 3 transformations correctly:
  * uppercase: converts text field to uppercase (10 points)
  * reverse: reverses the text field (10 points)
  * count_words: returns word count of text field (10 points)
- Returns proper JSON response with Content-Type application/json (10 points)
- Error handling: missing 'text' field returns 400 with message (10 points)
- Error handling: missing/invalid 'operation' field returns 400 with message (10 points)
- Error handling: non-JSON body returns 400 (5 points)
- Uses appropriate HTTP status codes (200 success, 400 client error) (5 points)
- Type hints and docstrings present (5 points)
- Code is well-organized, not overly complex (5 points)
Deduct 15 points for any transformation that produces wrong output."""


class LargestRectangle(BaseTest):
    """ct-3: Largest rectangle of 1s in a 2D binary grid."""

    def _get_judge_rubric(self) -> str:
        return """Score the response on these criteria (total 100 points):
- Uses the histogram-based approach: builds height histogram per row, then applies
  largest-rectangle-in-histogram on each row's histogram (25 points)
- Largest-rectangle-in-histogram uses a stack-based O(n) approach (20 points)
- Overall time complexity is O(rows * cols) as required, not O(rows * cols^2) (15 points)
- Space complexity is O(cols) or O(rows * cols) with clear justification (5 points)
- Handles edge cases: empty grid, single row, single column, all 0s, all 1s (10 points)
- Correct implementation that would produce the right answer on standard test cases
  like [[1,0,1,0,0],[1,0,1,1,1],[1,1,1,1,1],[1,0,0,1,0]] => 6 (15 points)
- Clean code with meaningful names and comments explaining the algorithm (5 points)
- Includes complexity analysis in comments or explanation (5 points)
Deduct 30 points if the algorithm is O(rows * cols^2) or worse. Deduct 20 points
for an incorrect approach that gives wrong answers."""


# ── Build test instances ──────────────────────────────────────────────

_ct1 = TrieImplementation(
    id="ct-1",
    name="Trie Implementation",
    category_id="coding-tasks",
    description="Implement a fully functional Trie data structure in Python with insert, search, and autocomplete.",
    eval_type="llm_judge",
    prompt="""Implement a Trie (prefix tree) data structure in Python with the following requirements:

1. Create a `TrieNode` class that stores children and an end-of-word marker.
2. Create a `Trie` class with these methods:
   - `insert(word: str) -> None` — Insert a word into the trie.
   - `search(word: str) -> bool` — Return True only if the exact complete word exists in the trie (not just a prefix).
   - `starts_with(prefix: str) -> bool` — Return True if any inserted word starts with the given prefix.
   - `autocomplete(prefix: str, max_results: int = 5) -> List[str]` — Return up to `max_results` words that start with the given prefix, sorted alphabetically.

Requirements:
- Use proper Python type hints on ALL method signatures (parameters and return types).
- Handle edge cases: inserting an empty string, searching for an empty string, a prefix longer than any word in the trie, and single-character words.
- The autocomplete method must use DFS to collect completions efficiently, not brute-force iterate all words.
- Include brief docstrings for each method.
- Do NOT use any external libraries — only Python builtins.

Provide the complete, runnable code. After the class definitions, include a short demonstration that inserts the words ["apple", "app", "application", "apt", "bat", "batch", "bath"] and shows the output of:
- search("app") => True
- search("ap") => False
- starts_with("ap") => True
- autocomplete("app") => ["app", "apple", "application"]
- autocomplete("bat") => ["bat", "batch", "bath"]
- autocomplete("xyz") => []""",
)

_ct2 = FlaskRESTEndpoint(
    id="ct-2",
    name="Flask REST Endpoint",
    category_id="coding-tasks",
    description="Write a Flask REST API endpoint with input validation and multiple text transformations.",
    eval_type="llm_judge",
    prompt="""Write a Flask REST API endpoint `POST /api/transform` that accepts a JSON body and performs text transformations. The complete implementation should be a single runnable Python file.

Request body format:
```json
{
    "text": "Hello World",
    "operation": "uppercase"
}
```

Supported operations and their expected responses:
1. `"uppercase"` — Returns `{"result": "HELLO WORLD", "operation": "uppercase", "original_length": 11}`
2. `"reverse"` — Returns `{"result": "dlroW olleH", "operation": "reverse", "original_length": 11}`
3. `"count_words"` — Returns `{"result": 2, "operation": "count_words", "original_length": 11}`

Requirements:
- Return HTTP 400 with `{"error": "<descriptive message>"}` if:
  - The request body is not valid JSON
  - The `"text"` field is missing or not a string
  - The `"operation"` field is missing or not one of the three supported operations
- Return HTTP 200 with the result for valid requests.
- Set Content-Type to application/json on all responses.
- Include proper type hints and a docstring for the route handler.
- Use `request.get_json(silent=True)` to gracefully handle non-JSON bodies.
- Include a `if __name__ == '__main__':` block that runs the app in debug mode on port 5000.

Provide the complete, runnable code including all necessary imports.""",
)

_ct3 = LargestRectangle(
    id="ct-3",
    name="Largest Rectangle in Binary Grid",
    category_id="coding-tasks",
    description="Find the area of the largest rectangle containing only 1s in a 2D binary grid in O(rows*cols) time.",
    eval_type="llm_judge",
    prompt="""Write a Python function that finds the area of the largest rectangle containing only 1s in a 2D binary matrix. The solution MUST run in O(rows * cols) time complexity.

Function signature:
```python
def maximal_rectangle(matrix: List[List[int]]) -> int:
```

Algorithm requirements:
- You MUST use the histogram-based approach: for each row, build a histogram of heights (consecutive 1s going upward), then apply the "largest rectangle in histogram" algorithm.
- The "largest rectangle in histogram" sub-problem MUST be solved using a stack-based O(n) approach, NOT a brute-force O(n^2) approach.
- Overall time complexity must be O(rows * cols). State this in a comment.
- Space complexity should be O(cols). State this in a comment.

Handle these edge cases:
- Empty matrix (return 0)
- Matrix with a single row
- Matrix with a single column
- Matrix of all 0s (return 0)
- Matrix of all 1s (return rows * cols)

After the function, include test cases that verify:
```python
assert maximal_rectangle([[1,0,1,0,0],
                           [1,0,1,1,1],
                           [1,1,1,1,1],
                           [1,0,0,1,0]]) == 6

assert maximal_rectangle([[0]]) == 0
assert maximal_rectangle([[1]]) == 1
assert maximal_rectangle([]) == 0
assert maximal_rectangle([[1,1],[1,1]]) == 4
```

Provide the complete code with the helper function, main function, and test cases. Include comments explaining each step of the algorithm.""",
)


CODING_TASKS_TESTS = [_ct1, _ct2, _ct3]
