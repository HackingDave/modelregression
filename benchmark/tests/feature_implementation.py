import re
from .base import BaseTest, EvalResult


class RealTimeSearchDebounce(BaseTest):
    """fi-1: Add real-time search with debounce to a React list component."""

    def _get_judge_rubric(self) -> str:
        return """Score the response on these criteria (total 100 points):
- Implements a debounce mechanism (either custom hook or lodash/debounce) with a configurable
  delay of 300ms as specified (15 points)
- Search input is controlled (uses useState) and filters the displayed list in real time (15 points)
- Correctly implements case-insensitive substring matching on the name field (10 points)
- Uses useCallback or useMemo appropriately to prevent unnecessary re-renders of filtered
  results and the debounce function (10 points)
- Shows a loading indicator during the debounce delay period (10 points)
- Handles edge cases: empty search term shows all items, whitespace-only input is
  treated as empty, special regex characters in search don't crash (10 points)
- Highlights matching text in the results (the prompt asks for this) (10 points)
- Cleans up the debounce timer on unmount to prevent memory leaks and state updates
  on unmounted components (10 points)
- Code is well-structured, uses proper React patterns, and is syntactically valid JSX (10 points)
Deduct 15 points if debounce is not actually implemented (just immediate filtering).
Deduct 10 points if the component would crash on special characters in search input."""


class SlidingWindowRateLimiter(BaseTest):
    """fi-2: Add sliding window rate limiting middleware to Express.js."""

    def _get_judge_rubric(self) -> str:
        return """Score the response on these criteria (total 100 points):
- Implements a TRUE sliding window algorithm (not just fixed window with reset). The window
  slides continuously — requests are tracked by timestamp, and old ones are pruned (20 points)
- Correctly prunes requests older than the window from the tracking store (15 points)
- Returns HTTP 429 with a JSON error body and Retry-After header when limit exceeded (10 points)
- Sets rate limit headers: X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset (10 points)
- Identifies clients by IP address (req.ip) with a note about proxy considerations (5 points)
- Uses an in-memory store (Map or object) with the structure specified: IP -> array of
  timestamps or sorted set (10 points)
- Middleware signature is correct: (req, res, next) => {} and calls next() on success (10 points)
- Configurable: windowMs and maxRequests are parameters, not hardcoded (5 points)
- Memory management: includes a periodic cleanup mechanism or LRU eviction to prevent
  unbounded growth of the IP store (10 points)
- Code is valid JavaScript/TypeScript and ready to use as Express middleware (5 points)
Deduct 20 points for a fixed-window implementation disguised as sliding window.
Deduct 10 points if the middleware never calls next() on allowed requests."""


class CursorPagination(BaseTest):
    """fi-3: Convert offset pagination to cursor-based pagination."""

    def _get_judge_rubric(self) -> str:
        return """Score the response on these criteria (total 100 points):
- Replaces OFFSET/LIMIT with WHERE clause using a cursor (e.g., WHERE id > :cursor) (20 points)
- Cursor is opaque: encodes the sort column value (usually id) as base64 or similar,
  not raw database IDs exposed to the client (10 points)
- Returns a response structure with: items array, nextCursor (null if no more), hasMore boolean,
  and does NOT include totalCount (which requires a separate COUNT query) (15 points)
- Handles the first page (no cursor provided) correctly by omitting the WHERE filter (10 points)
- Supports both forward pagination (after cursor) correctly (10 points)
- Uses LIMIT N+1 fetch trick to determine hasMore without a count query (10 points)
- Preserves the original sort order (ORDER BY created_at DESC, id DESC) with a
  compound cursor for stable pagination (10 points)
- Explains the advantages: consistent results during concurrent inserts/deletes,
  O(1) page fetch vs O(offset) for offset pagination (10 points)
- Code is syntactically valid and handles edge cases: empty result set, invalid cursor (5 points)
Deduct 20 points if OFFSET is still used anywhere in the solution.
Deduct 15 points if cursors are just raw integer IDs without encoding."""


# ── Build test instances ──────────────────────────────────────────────

_fi1 = RealTimeSearchDebounce(
    id="fi-1",
    name="Real-time Search with Debounce",
    category_id="feature-implementation",
    description="Add real-time filtered search with debounce to an existing React list component.",
    eval_type="llm_judge",
    prompt="""Add real-time search with debounce functionality to the following React component. The search should filter the displayed list as the user types, with a 300ms debounce to avoid excessive re-renders.

Existing component:
```jsx
import React, { useState } from 'react';

const ITEMS = [
    { id: 1, name: 'JavaScript Framework Guide', category: 'frontend' },
    { id: 2, name: 'Python Data Science Handbook', category: 'data' },
    { id: 3, name: 'React Performance Optimization', category: 'frontend' },
    { id: 4, name: 'Node.js Backend Architecture', category: 'backend' },
    { id: 5, name: 'SQL Query Optimization Techniques', category: 'database' },
    { id: 6, name: 'TypeScript Advanced Patterns', category: 'frontend' },
    { id: 7, name: 'Docker Container Security', category: 'devops' },
    { id: 8, name: 'GraphQL API Design', category: 'backend' },
    { id: 9, name: 'CSS Grid Layout Mastery', category: 'frontend' },
    { id: 10, name: 'Machine Learning with Python', category: 'data' },
];

function ResourceList() {
    return (
        <div>
            <h2>Resources</h2>
            <ul>
                {ITEMS.map(item => (
                    <li key={item.id}>
                        <strong>{item.name}</strong> <span>({item.category})</span>
                    </li>
                ))}
            </ul>
        </div>
    );
}

export default ResourceList;
```

Requirements:
1. Add a search input field at the top of the component.
2. Implement debounce with a 300ms delay — do NOT use lodash, implement debounce yourself (custom hook or inline).
3. Filter items by case-insensitive substring match on the `name` field.
4. Show a "Searching..." indicator during the debounce delay.
5. When search input is empty, show all items.
6. Highlight the matching portion of text in each result (wrap matches in <mark> tags).
7. Show a "No results found" message when nothing matches.
8. Clean up the debounce timeout on unmount to prevent memory leaks.
9. Handle edge cases: whitespace-only input should be treated as empty, special characters in the query should not cause regex errors.

Provide the complete, updated component code.""",
)

_fi2 = SlidingWindowRateLimiter(
    id="fi-2",
    name="Sliding Window Rate Limiter",
    category_id="feature-implementation",
    description="Implement sliding window rate limiting middleware for an Express.js application.",
    eval_type="llm_judge",
    prompt="""Implement a sliding window rate limiting middleware for Express.js. This must be a TRUE sliding window algorithm, not a fixed window with periodic resets.

Requirements:
1. Create a middleware function `createRateLimiter(options)` where options include:
   - `windowMs`: Window size in milliseconds (default: 60000, i.e., 1 minute)
   - `maxRequests`: Maximum requests per window (default: 100)

2. The sliding window algorithm must:
   - Track each request's timestamp per client IP
   - On each request, remove all timestamps older than `windowMs` from the current time
   - Count remaining timestamps — if count >= maxRequests, reject; otherwise, add current timestamp and allow
   - This ensures a truly sliding window, not a fixed interval reset

3. When a request is allowed (under the limit):
   - Call `next()` to pass to the next middleware
   - Set headers: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset` (epoch seconds)

4. When a request is rejected (over the limit):
   - Return HTTP 429 with JSON body: `{"error": "Rate limit exceeded", "retryAfter": <seconds>}`
   - Set the `Retry-After` header (in seconds)
   - Do NOT call `next()`

5. Memory management:
   - Include a periodic cleanup interval (every 60 seconds) that removes entries for IPs
     with no requests in the last `windowMs`
   - The cleanup interval must be clearable (return a `close()` method or similar) to prevent
     the timer from keeping the process alive

6. Add a note about `req.ip` behavior behind proxies (trust proxy setting).

Provide the complete middleware code as a single JavaScript/Node.js module that exports `createRateLimiter`. Include a brief usage example showing how to apply it to an Express app.""",
)

_fi3 = CursorPagination(
    id="fi-3",
    name="Cursor-based Pagination",
    category_id="feature-implementation",
    description="Convert an existing offset-based pagination endpoint to cursor-based pagination.",
    eval_type="llm_judge",
    prompt="""Convert the following offset-based pagination endpoint to cursor-based pagination. The existing code uses a PostgreSQL database via a query helper function.

Existing code (offset-based):
```javascript
// GET /api/posts?page=1&limit=20
async function getPosts(req, res) {
    const page = parseInt(req.query.page) || 1;
    const limit = parseInt(req.query.limit) || 20;
    const offset = (page - 1) * limit;

    const countResult = await db.query('SELECT COUNT(*) FROM posts WHERE published = true');
    const totalCount = parseInt(countResult.rows[0].count);

    const result = await db.query(
        'SELECT id, title, content, author_id, created_at FROM posts WHERE published = true ORDER BY created_at DESC, id DESC LIMIT $1 OFFSET $2',
        [limit, offset]
    );

    res.json({
        posts: result.rows,
        pagination: {
            page,
            limit,
            totalCount,
            totalPages: Math.ceil(totalCount / limit),
        }
    });
}
```

Requirements for the cursor-based version:
1. Replace OFFSET with a WHERE clause that uses a cursor. Do NOT use OFFSET anywhere.
2. Use a compound cursor based on (created_at, id) since the sort is by created_at DESC, id DESC.
3. Encode the cursor as a base64-encoded JSON string (opaque to the client).
4. API should be: `GET /api/posts?limit=20&after=<cursor>` — no `page` parameter.
5. Use the LIMIT N+1 trick: fetch `limit + 1` rows, and if you get `limit + 1` results, there are more pages (set hasMore=true and return only `limit` rows).
6. Response format:
   ```json
   {
       "posts": [...],
       "pagination": {
           "hasMore": true,
           "nextCursor": "base64encodedstring",
           "limit": 20
       }
   }
   ```
7. When no `after` cursor is provided, return the first page (no WHERE filter on cursor).
8. Handle invalid/malformed cursors gracefully (return 400 error).
9. Remove the COUNT query — it is not needed and is expensive on large tables.

Provide the complete converted function. Include helper functions for encoding/decoding cursors. Explain briefly why cursor-based pagination is superior for this use case.""",
)


FEATURE_IMPLEMENTATION_TESTS = [_fi1, _fi2, _fi3]
