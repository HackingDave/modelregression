import re
from .base import BaseTest, EvalResult


class AddCachingWithoutBreaking(BaseTest):
    """bi-1: Add caching to existing function without breaking tests."""

    def _get_judge_rubric(self) -> str:
        return """Score the response on these criteria (total 100 points):

Caching implementation (40 points):
- Adds a caching layer (dict, lru_cache, or custom cache) that stores results
  keyed by the function arguments (10 points)
- Cache is checked BEFORE calling the underlying function (5 points)
- Cache is populated AFTER a successful function call (5 points)
- Cache has a TTL/expiration mechanism so stale data doesn't persist forever (10 points)
- Cache has a max size or eviction policy to prevent unbounded memory growth (5 points)
- Includes a way to invalidate/clear the cache (5 points)

No regressions (40 points):
- ALL 6 existing test cases still pass with the cached version (20 points)
  - test_basic_lookup passes (4 points each)
  - test_not_found passes
  - test_case_sensitivity passes
  - test_special_characters passes
  - test_empty_input passes
  - test_concurrent_calls passes
- The function signature remains compatible (same parameters and return type) (10 points)
- Side effects (database calls) still happen on cache miss (5 points)
- Error cases still raise the same exceptions (5 points)

Code quality (20 points):
- Cache logic is cleanly separated (decorator pattern or wrapper, not interleaved
  with business logic) (10 points)
- Thread safety considered (if using threading) or async safety (if async) (5 points)
- Code is readable and well-commented (5 points)

Deduct 25 points for each existing test that would fail.
Deduct 15 points if the cache never expires (no TTL).
Deduct 10 points if the cache grows without bound."""


class RefactorCallbacksToAsync(BaseTest):
    """bi-2: Refactor callbacks to async/await while maintaining behavior."""

    def _get_judge_rubric(self) -> str:
        return """Score the response on these criteria (total 100 points):

Correct async/await conversion (35 points):
- All callback-based functions are converted to async functions (10 points)
- Nested callbacks ("callback hell") are flattened into sequential await calls (10 points)
- Error handling callbacks (err, result) are converted to try/except blocks (10 points)
- The converted code produces the SAME outputs in the SAME order as the original (5 points)

Behavior preservation (35 points):
- The order of operations is preserved: readFile -> parseData -> validateData -> saveResult (10 points)
- Error messages remain the same (5 points)
- The function still returns/resolves with the same result type (5 points)
- Side effects (file reads, saves) happen in the same sequence (5 points)
- Edge case: if readFile fails, parseData is NOT called (same as original) (5 points)
- Edge case: partial failure cleanup is preserved (5 points)

Async patterns (20 points):
- Uses async/await consistently (not mixing with .then() or callbacks) (5 points)
- Properly awaits all async operations (no fire-and-forget) (5 points)
- Uses try/except/finally for cleanup, not nested callbacks (5 points)
- Handles the case where multiple async operations could run in parallel
  (uses asyncio.gather or Promise.all where appropriate) (5 points)

Code quality (10 points):
- Async functions are properly marked with async keyword (3 points)
- No callback parameters remain in function signatures (4 points)
- Clean, readable code without unnecessary nesting (3 points)

Deduct 20 points if the order of operations changes.
Deduct 15 points for each behavior difference from the original.
Deduct 10 points if any callback pattern remains in the "converted" code."""


class AddLoggingToLegacyCode(BaseTest):
    """bi-3: Add logging to legacy code without changing behavior."""

    def _get_judge_rubric(self) -> str:
        return """Score the response on these criteria (total 100 points):

Logging additions (35 points):
- Adds logging at function entry with parameters (5 points)
- Adds logging at function exit with return value (5 points)
- Adds logging for each significant decision point / branch (5 points)
- Adds logging for exception/error paths (5 points)
- Uses appropriate log levels: DEBUG for flow, INFO for operations,
  WARNING for recoverable issues, ERROR for failures (10 points)
- Includes contextual information in log messages (user_id, order_id, etc.) (5 points)

Behavior preservation (40 points):
- Return values are IDENTICAL for all inputs (10 points)
- Exception types and messages are unchanged (10 points)
- Side effects (database writes, API calls) happen in the same order (10 points)
- No new exceptions are introduced (logging failures must not propagate) (5 points)
- Performance characteristics are not significantly altered (5 points)

Logging best practices (15 points):
- Uses Python logging module (not print statements) (5 points)
- Creates a module-level logger: logger = logging.getLogger(__name__) (3 points)
- Sensitive data (passwords, tokens, full credit card numbers) is NOT logged (5 points)
- Uses structured logging or at least consistent format (2 points)

Code quality (10 points):
- Logging statements do not clutter the business logic (not more than 1 log line
  between every line of business code) (5 points)
- Original code structure and indentation is preserved (5 points)

Deduct 30 points if any return value changes.
Deduct 20 points if any exception behavior changes.
Deduct 15 points if passwords or tokens are logged.
Deduct 10 points if print() is used instead of logging module."""


# ── Build test instances ──────────────────────────────────────────────

_bi1 = AddCachingWithoutBreaking(
    id="bi-1",
    name="Add Caching Without Breaking Tests",
    category_id="bug-introduction-rate",
    description="Add a caching layer to an existing function without causing any of the existing tests to fail.",
    eval_type="llm_judge",
    prompt="""Add a caching layer to the following Python function WITHOUT breaking any of the existing tests. The function looks up user data from a (simulated) database. After your change, repeated calls with the same user_id should return cached results instead of hitting the database every time.

Function to modify:
```python
import time
from typing import Optional

# Simulated database
_DATABASE = {
    "user_001": {"name": "Alice", "email": "alice@example.com", "role": "admin"},
    "user_002": {"name": "Bob", "email": "bob@example.com", "role": "user"},
    "user_003": {"name": "Charlie", "email": "charlie@example.com", "role": "user"},
}

_call_count = 0  # Track DB calls for testing

def lookup_user(user_id: str) -> Optional[dict]:
    \"\"\"Look up a user by ID. Returns user dict or None if not found.
    Raises ValueError if user_id is empty.
    Raises TypeError if user_id is not a string.
    \"\"\"
    global _call_count
    if not isinstance(user_id, str):
        raise TypeError(f"user_id must be a string, got {type(user_id).__name__}")
    if not user_id.strip():
        raise ValueError("user_id cannot be empty")

    _call_count += 1
    time.sleep(0.1)  # Simulate DB latency

    return _DATABASE.get(user_id)
```

Existing tests (ALL must continue to pass):
```python
import pytest
import threading

def test_basic_lookup():
    result = lookup_user("user_001")
    assert result is not None
    assert result["name"] == "Alice"
    assert result["email"] == "alice@example.com"

def test_not_found():
    result = lookup_user("user_999")
    assert result is None

def test_case_sensitivity():
    result = lookup_user("User_001")  # Capital U
    assert result is None  # Should NOT find "user_001"

def test_special_characters():
    result = lookup_user("user-with-dashes")
    assert result is None

def test_empty_input():
    with pytest.raises(ValueError):
        lookup_user("")
    with pytest.raises(ValueError):
        lookup_user("   ")
    with pytest.raises(TypeError):
        lookup_user(None)
    with pytest.raises(TypeError):
        lookup_user(123)

def test_concurrent_calls():
    results = []
    def call_lookup():
        results.append(lookup_user("user_002"))
    threads = [threading.Thread(target=call_lookup) for _ in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert all(r is not None and r["name"] == "Bob" for r in results)
```

Requirements:
1. Add caching so that the second call to `lookup_user("user_001")` returns instantly from cache.
2. Cache must have a TTL (time-to-live) — cached entries expire after a configurable duration (default 60 seconds).
3. Cache must have a maximum size to prevent unbounded memory growth.
4. Include a `clear_cache()` function to manually invalidate the cache.
5. ALL 6 existing tests must still pass without modification.
6. The function signature must remain `lookup_user(user_id: str) -> Optional[dict]`.
7. Cache must be thread-safe (test_concurrent_calls uses threads).
8. None results (user not found) should also be cached to prevent repeated DB lookups for missing users.

Provide the complete modified code including the caching implementation.""",
)

_bi2 = RefactorCallbacksToAsync(
    id="bi-2",
    name="Refactor Callbacks to Async/Await",
    category_id="bug-introduction-rate",
    description="Convert callback-based code to async/await without altering its observable behavior.",
    eval_type="llm_judge",
    prompt="""Convert the following callback-based JavaScript code to use async/await. The converted code MUST produce the same results in the same order. Do not change the behavior — only the control flow pattern.

Original callback-based code:
```javascript
const fs = require('fs');
const path = require('path');

function processDataPipeline(inputPath, outputPath, callback) {
    // Step 1: Read input file
    fs.readFile(inputPath, 'utf-8', (err, rawData) => {
        if (err) {
            callback(new Error(`Failed to read input: ${err.message}`));
            return;
        }

        console.log(`Read ${rawData.length} bytes from ${inputPath}`);

        // Step 2: Parse the data
        parseData(rawData, (err, parsedRecords) => {
            if (err) {
                callback(new Error(`Failed to parse data: ${err.message}`));
                return;
            }

            console.log(`Parsed ${parsedRecords.length} records`);

            // Step 3: Validate each record
            validateRecords(parsedRecords, (err, validRecords, invalidCount) => {
                if (err) {
                    callback(new Error(`Validation failed: ${err.message}`));
                    return;
                }

                console.log(`Validated: ${validRecords.length} valid, ${invalidCount} invalid`);

                if (validRecords.length === 0) {
                    callback(new Error('No valid records to process'));
                    return;
                }

                // Step 4: Transform records
                transformRecords(validRecords, (err, transformed) => {
                    if (err) {
                        callback(new Error(`Transform failed: ${err.message}`));
                        return;
                    }

                    // Step 5: Write output
                    const output = JSON.stringify(transformed, null, 2);
                    fs.writeFile(outputPath, output, 'utf-8', (err) => {
                        if (err) {
                            callback(new Error(`Failed to write output: ${err.message}`));
                            return;
                        }

                        console.log(`Wrote ${transformed.length} records to ${outputPath}`);
                        callback(null, {
                            inputPath,
                            outputPath,
                            totalRecords: parsedRecords.length,
                            validRecords: validRecords.length,
                            invalidRecords: invalidCount,
                            outputRecords: transformed.length,
                        });
                    });
                });
            });
        });
    });
}

function parseData(raw, callback) {
    try {
        const lines = raw.split('\\n').filter(line => line.trim());
        const records = lines.map((line, index) => {
            const parts = line.split(',');
            if (parts.length < 3) throw new Error(`Line ${index + 1}: expected 3+ fields`);
            return { id: parts[0].trim(), name: parts[1].trim(), value: parts[2].trim() };
        });
        setTimeout(() => callback(null, records), 10); // Simulate async
    } catch (e) {
        setTimeout(() => callback(e), 10);
    }
}

function validateRecords(records, callback) {
    let invalidCount = 0;
    const valid = records.filter(record => {
        if (!record.id || !record.name || !record.value) {
            invalidCount++;
            return false;
        }
        if (isNaN(Number(record.value))) {
            invalidCount++;
            return false;
        }
        return true;
    });
    setTimeout(() => callback(null, valid, invalidCount), 10);
}

function transformRecords(records, callback) {
    try {
        const transformed = records.map(record => ({
            ...record,
            value: Number(record.value),
            processedAt: new Date().toISOString(),
        }));
        setTimeout(() => callback(null, transformed), 10);
    } catch (e) {
        setTimeout(() => callback(e), 10);
    }
}
```

Requirements:
1. Convert ALL functions to use async/await (use `fs.promises` for file I/O).
2. Convert the callback-based helper functions (parseData, validateRecords, transformRecords) to async functions.
3. The main function should return a Promise that resolves with the same result object (or rejects with the same error).
4. Preserve ALL console.log messages in the exact same order.
5. Error messages must remain IDENTICAL (same prefix strings).
6. The "no valid records" check must still happen at the same point in the pipeline.
7. Do NOT use .then() or .catch() — use async/await with try/catch exclusively.
8. Remove all callback parameters from function signatures.

Provide the complete converted code.""",
)

_bi3 = AddLoggingToLegacyCode(
    id="bi-3",
    name="Add Logging to Legacy Code",
    category_id="bug-introduction-rate",
    description="Add comprehensive logging to messy legacy code without changing any observable behavior.",
    eval_type="llm_judge",
    prompt="""Add comprehensive logging to the following legacy Python code WITHOUT changing any of its observable behavior. The return values, exceptions, side effects, and execution order must remain identical.

Legacy code:
```python
import smtplib
from email.mime.text import MIMEText
from datetime import datetime, timedelta

SMTP_HOST = "mail.example.com"
SMTP_PORT = 587
SMTP_USER = "noreply@example.com"
SMTP_PASS = "s3cretMailP@ss"  # Yes, this is hardcoded. Don't change it.

def process_order(order_data):
    if not order_data or not isinstance(order_data, dict):
        raise ValueError("Invalid order data")

    order_id = order_data.get("order_id")
    items = order_data.get("items", [])
    customer_email = order_data.get("customer_email")
    payment_method = order_data.get("payment_method")
    coupon_code = order_data.get("coupon_code")

    if not order_id or not items:
        raise ValueError("Missing order_id or items")

    # Calculate total
    total = 0
    for item in items:
        price = item.get("price", 0)
        qty = item.get("quantity", 1)
        total += price * qty

    # Apply coupon
    discount = 0
    if coupon_code:
        if coupon_code == "SAVE10":
            discount = total * 0.10
        elif coupon_code == "SAVE20":
            discount = total * 0.20
        elif coupon_code == "FLAT50":
            discount = min(50, total)
        else:
            pass  # Unknown coupon, silently ignored

    final_total = total - discount

    # Payment processing (simulated)
    if payment_method == "credit_card":
        cc_number = order_data.get("cc_number", "")
        if len(cc_number) != 16:
            raise ValueError("Invalid credit card number")
        charge_result = _charge_card(cc_number, final_total)
    elif payment_method == "paypal":
        charge_result = _charge_paypal(customer_email, final_total)
    else:
        raise ValueError(f"Unsupported payment method: {payment_method}")

    if not charge_result.get("success"):
        raise RuntimeError(f"Payment failed: {charge_result.get('error', 'unknown')}")

    # Send confirmation email
    if customer_email:
        try:
            _send_email(
                customer_email,
                f"Order {order_id} Confirmed",
                f"Your order total: ${final_total:.2f}"
            )
        except Exception:
            pass  # Email failure is not critical

    return {
        "order_id": order_id,
        "status": "completed",
        "total": final_total,
        "discount": discount,
        "items_count": len(items),
    }

def _charge_card(cc_number, amount):
    # Simulate credit card charge
    if amount <= 0:
        return {"success": False, "error": "Invalid amount"}
    return {"success": True, "transaction_id": f"txn_{datetime.now().timestamp()}"}

def _charge_paypal(email, amount):
    # Simulate PayPal charge
    if not email:
        return {"success": False, "error": "No email for PayPal"}
    return {"success": True, "transaction_id": f"pp_{datetime.now().timestamp()}"}

def _send_email(to_addr, subject, body):
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = SMTP_USER
    msg["To"] = to_addr
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.send_message(msg)
```

Requirements:
1. Add logging using Python's `logging` module (NOT print statements).
2. Create a module-level logger: `logger = logging.getLogger(__name__)`
3. Add log statements for:
   - Function entry with relevant parameters
   - Function exit with return value summary
   - Each major decision point (coupon applied, payment method chosen, email sent)
   - All error/exception paths
   - Warnings for unusual but valid situations (unknown coupon, missing email)
4. Use appropriate log levels: DEBUG for flow tracing, INFO for operations, WARNING for issues, ERROR for failures.
5. CRITICAL: Do NOT log sensitive data. Specifically:
   - Do NOT log the full credit card number (mask it: log only last 4 digits)
   - Do NOT log the SMTP_PASS password
   - Do NOT log the full customer email in DEBUG-level messages (mask it)
6. Return values, exceptions, and side effects must remain IDENTICAL.
7. If logging itself throws an exception, it must NOT propagate (wrap in try/except if needed).
8. Keep the original code structure intact — do not refactor the business logic.

Provide the complete modified code with logging added.""",
)


BUG_INTRODUCTION_TESTS = [_bi1, _bi2, _bi3]
