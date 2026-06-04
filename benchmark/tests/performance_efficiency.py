import re
from .base import BaseTest, EvalResult


class OptimizeAlgorithm(BaseTest):
    """pe-1: Optimize an O(n^3) solution to O(n log n)."""

    def _get_judge_rubric(self) -> str:
        return """Score the response on these criteria (total 100 points):

Algorithm improvement (40 points):
- Correctly identifies the original algorithm as O(n^3) due to triple nested loops or
  equivalent cubic approach (5 points)
- Provides an optimized solution that is O(n log n) or better (20 points)
- The optimization strategy is sound: sorting + two pointers, or sorting + binary search,
  or hash map approach (10 points)
- The optimized solution produces the SAME output as the original for all inputs (5 points)

Correctness (25 points):
- Handles the standard case correctly (5 points)
- Handles edge cases: empty array, single element, two elements, all same values,
  negative numbers, duplicates in result (10 points)
- Handles the case where no triplet sums to the target (5 points)
- Returns results in the same format as the original (sorted triplets, no duplicates) (5 points)

Complexity analysis (20 points):
- Correctly analyzes the original O(n^3) time complexity with explanation (5 points)
- Correctly analyzes the optimized time complexity as O(n^2) or O(n log n) with
  clear explanation of where each factor comes from (5 points)
- Discusses space complexity of both solutions (5 points)
- Explains WHY the optimization works (not just "it's faster") (5 points)

Code quality (15 points):
- Clean, readable implementation (5 points)
- Type hints and comments (5 points)
- Explains the optimization strategy before the code (5 points)

Deduct 30 points if the "optimized" solution is still O(n^3) or O(n^2 log n).
Deduct 20 points if the optimized solution gives different results than the original.
Deduct 10 points if no complexity analysis is provided."""


class MemoryEfficientCSV(BaseTest):
    """pe-2: Process a huge CSV memory-efficiently."""

    def _get_judge_rubric(self) -> str:
        return """Score the response on these criteria (total 100 points):

Streaming approach (30 points):
- Reads the CSV file line-by-line or in chunks (NOT loading the entire file into memory) (15 points)
- Uses csv.reader/DictReader with a file iterator, or pandas with chunksize parameter,
  or manual line-by-line reading (10 points)
- Memory usage is O(1) or O(chunk_size), NOT O(n) where n is total rows (5 points)

Correct aggregation (25 points):
- Running totals / accumulators are updated per-row or per-chunk (10 points)
- Aggregation results (sum, average, min, max, count per category) are correct (10 points)
- Final statistics are computed from accumulators, not from a fully-loaded dataset (5 points)

Error handling (15 points):
- Handles malformed rows gracefully (skip with warning, don't crash) (5 points)
- Handles encoding issues (utf-8, latin-1, BOM) (3 points)
- Handles missing values / empty fields (3 points)
- Handles the file not existing (2 points)
- Handles interrupt/cleanup (close file handles properly) (2 points)

Performance considerations (15 points):
- Uses appropriate buffer sizes or chunk sizes (5 points)
- Avoids string concatenation in a loop (use join or write directly) (3 points)
- Uses generators or iterators where appropriate (4 points)
- Mentions or implements progress reporting for long-running processing (3 points)

Output (10 points):
- Writes output incrementally (streaming output too, not collecting all results in memory) (5 points)
- Produces correct summary statistics at the end (5 points)

Code quality (5 points):
- Type hints and docstrings (3 points)
- Clean code structure (2 points)

Deduct 40 points if the entire CSV is loaded into memory (e.g., pandas.read_csv() without chunksize,
or readlines(), or csv.reader into a list).
Deduct 15 points if output is accumulated in a list that grows with input size."""


class OptimizeSlowSQL(BaseTest):
    """pe-3: Optimize a slow SQL query with bad joins."""

    def _get_judge_rubric(self) -> str:
        return """Score the response on these criteria (total 100 points):

Query optimization (35 points):
- Removes or restructures the unnecessary cartesian join / cross join pattern (10 points)
- Eliminates the SELECT * in subqueries and selects only needed columns (5 points)
- Restructures nested subqueries into JOINs or CTEs where appropriate (10 points)
- Removes redundant DISTINCT that hides a join multiplicity problem (5 points)
- Moves filtering conditions to the most restrictive position (WHERE before JOIN
  when possible, or INTO the JOIN ON clause) (5 points)

Index recommendations (25 points):
- Recommends indexes on the JOIN columns (foreign keys) (10 points)
- Recommends indexes on the WHERE clause filter columns (5 points)
- Recommends a composite index for the most selective filter combination (5 points)
- Index recommendations include the column order rationale (5 points)

Explain plan awareness (15 points):
- Mentions EXPLAIN/EXPLAIN ANALYZE to verify improvements (5 points)
- Identifies likely full table scans in the original query (5 points)
- Explains how the proposed indexes would change the execution plan (5 points)

Correctness (15 points):
- The optimized query returns the SAME results as the original (10 points)
- Edge cases preserved: NULL handling, empty result sets (5 points)

Additional optimizations (10 points):
- Suggests LIMIT/pagination if results could be large (3 points)
- Mentions query caching or materialized views for repeated expensive queries (3 points)
- Suggests denormalization or summary tables if the query runs frequently (2 points)
- Considers the impact of data distribution (selective vs non-selective filters) (2 points)

Deduct 20 points if the optimized query returns different results.
Deduct 15 points if no indexes are recommended.
Deduct 10 points if EXPLAIN is not mentioned."""


# ── Build test instances ──────────────────────────────────────────────

_pe1 = OptimizeAlgorithm(
    id="pe-1",
    name="Optimize Algorithm Complexity",
    category_id="performance-efficiency",
    description="Optimize an O(n^3) three-sum solution to O(n^2) or O(n log n).",
    eval_type="llm_judge",
    prompt="""The following Python function finds all unique triplets in a list that sum to a target value. It works correctly but is extremely slow for large inputs due to its O(n^3) time complexity. Optimize it to O(n^2) or better while producing IDENTICAL results.

Slow O(n^3) solution:
```python
from typing import List, Tuple

def find_triplets(nums: List[int], target: int) -> List[Tuple[int, int, int]]:
    \"\"\"Find all unique triplets that sum to target.
    Returns sorted list of sorted triplets, no duplicates.
    \"\"\"
    n = len(nums)
    result = set()
    for i in range(n):
        for j in range(i + 1, n):
            for k in range(j + 1, n):
                if nums[i] + nums[j] + nums[k] == target:
                    triplet = tuple(sorted([nums[i], nums[j], nums[k]]))
                    result.add(triplet)
    return sorted(list(result))
```

Test cases (the optimized solution must produce the same output):
```python
assert find_triplets([1, 2, 3, 4, 5, 6], 10) == [(1, 3, 6), (1, 4, 5), (2, 3, 5)]
assert find_triplets([0, 0, 0, 0], 0) == [(0, 0, 0)]
assert find_triplets([-1, 0, 1, 2, -1, -4], 0) == [(-1, -1, 2), (-1, 0, 1)]
assert find_triplets([1, 2], 3) == []  # Less than 3 elements
assert find_triplets([], 0) == []
assert find_triplets([1, 1, 1, 1], 3) == [(1, 1, 1)]
```

Requirements:
1. Provide the optimized function with the SAME signature and return type.
2. The optimized solution must produce IDENTICAL output for all inputs.
3. Analyze the time complexity of BOTH solutions and explain why yours is faster.
4. Analyze the space complexity of both solutions.
5. Explain your optimization strategy step by step before the code.
6. Handle all edge cases: empty array, less than 3 elements, all duplicates, negative numbers, large arrays.
7. The target complexity should be O(n^2) using a sort + two-pointer approach.

Provide the optimized code followed by the complexity analysis.""",
)

_pe2 = MemoryEfficientCSV(
    id="pe-2",
    name="Memory-Efficient CSV Processing",
    category_id="performance-efficiency",
    description="Process a multi-gigabyte CSV file without loading it entirely into memory.",
    eval_type="llm_judge",
    prompt="""Write a Python script that processes a CSV file that is too large to fit in memory (e.g., 50GB, hundreds of millions of rows). The script must compute summary statistics without ever loading the entire file into memory.

The CSV file format:
```
transaction_id,customer_id,category,amount,currency,timestamp
TXN001,CUST_42,electronics,299.99,USD,2024-01-15T10:30:00
TXN002,CUST_17,groceries,45.50,USD,2024-01-15T10:31:00
...
```

Required output (computed in a streaming fashion):
1. Total number of transactions
2. Total amount across all transactions
3. Average transaction amount
4. Min and max transaction amounts
5. Count and total amount per category (e.g., electronics: 15000 transactions, $2.3M total)
6. Count and total amount per currency
7. Top 10 customers by total spending
8. Transactions per hour distribution (0-23)

Requirements:
1. NEVER load the entire file into memory. Process row-by-row or in small chunks.
2. Memory usage must be O(1) relative to file size (proportional to the number of unique categories/currencies/customers, which is assumed to be much smaller than total rows).
3. Use Python's csv module or pandas with chunksize — NOT pd.read_csv() without chunksize.
4. Handle malformed rows gracefully: log a warning and skip, do not crash.
5. Handle encoding issues (try utf-8, fall back to latin-1).
6. Handle missing or empty amount fields (skip them for amount calculations).
7. Show progress every 1 million rows (print rows processed so far).
8. Use a context manager to ensure the file is properly closed.
9. For the "top 10 customers" statistic, you may keep a dict of customer_id -> total_amount in memory since the number of unique customers is much smaller than total rows. If there could be millions of unique customers, discuss the tradeoff and suggest an approach (e.g., approximate top-k using a min-heap of size 10).
10. Write the output summary to both stdout and an output file.

Provide the complete, runnable Python script. Include type hints and docstrings. Add comments explaining why each design decision supports memory efficiency.""",
)

_pe3 = OptimizeSlowSQL(
    id="pe-3",
    name="Optimize Slow SQL Query",
    category_id="performance-efficiency",
    description="Optimize a poorly written SQL query with bad joins, missing indexes, and unnecessary subqueries.",
    eval_type="llm_judge",
    prompt="""The following SQL query runs against a PostgreSQL database and takes over 30 seconds on a table with 10 million orders, 2 million customers, and 500,000 products. Optimize it to run in under 1 second. Provide the optimized query AND index recommendations.

Slow query:
```sql
SELECT DISTINCT
    c.customer_name,
    c.email,
    o.order_id,
    o.order_date,
    o.total_amount,
    p.product_name,
    oi.quantity,
    oi.unit_price,
    (SELECT AVG(o2.total_amount)
     FROM orders o2
     WHERE o2.customer_id = c.customer_id) as avg_order_amount,
    (SELECT COUNT(*)
     FROM orders o3
     WHERE o3.customer_id = c.customer_id) as total_orders
FROM
    customers c,
    orders o,
    order_items oi,
    products p
WHERE
    c.customer_id = o.customer_id
    AND o.order_id = oi.order_id
    AND oi.product_id = p.product_id
    AND o.order_date >= '2024-01-01'
    AND o.order_date < '2024-07-01'
    AND o.status = 'completed'
    AND c.country = 'US'
    AND p.category IN ('electronics', 'clothing', 'home')
ORDER BY
    o.order_date DESC,
    c.customer_name ASC;
```

Table schemas:
```sql
CREATE TABLE customers (
    customer_id SERIAL PRIMARY KEY,
    customer_name VARCHAR(200),
    email VARCHAR(200),
    country VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE orders (
    order_id SERIAL PRIMARY KEY,
    customer_id INTEGER REFERENCES customers(customer_id),
    order_date TIMESTAMP,
    total_amount DECIMAL(10, 2),
    status VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE order_items (
    item_id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES orders(order_id),
    product_id INTEGER REFERENCES products(product_id),
    quantity INTEGER,
    unit_price DECIMAL(10, 2)
);

CREATE TABLE products (
    product_id SERIAL PRIMARY KEY,
    product_name VARCHAR(200),
    category VARCHAR(100),
    price DECIMAL(10, 2)
);
```

Your response must include:
1. Identify ALL performance problems in the original query (there are at least 5).
2. Provide the optimized SQL query that returns the SAME results.
3. Explain each optimization you made and why it helps.
4. Provide CREATE INDEX statements for all recommended indexes, with an explanation of why each index helps and the column order rationale.
5. Mention EXPLAIN ANALYZE and how to verify the improvement.
6. Estimate the expected improvement factor.

Problems to look for: implicit cross joins (FROM a, b, c), correlated subqueries in SELECT, unnecessary DISTINCT, missing indexes on foreign keys and filter columns, suboptimal join order.""",
)


PERFORMANCE_EFFICIENCY_TESTS = [_pe1, _pe2, _pe3]
