import re
from .base import BaseTest, EvalResult


class FileUploadHandler(BaseTest):
    """cth-1: Implement a file upload handler with comprehensive failure mode handling."""

    def _get_judge_rubric(self) -> str:
        return """Score the response on these criteria. Award points for each failure mode properly handled (total 100 points):

File validation failure modes (30 points):
- File size exceeds maximum (check BEFORE reading entire file into memory) (5 points)
- File type/MIME type validation (not just extension, but magic bytes / content-type header) (5 points)
- Empty file / zero-byte upload (3 points)
- Filename sanitization (path traversal characters, null bytes, special chars) (5 points)
- Duplicate filename handling (rename or reject) (3 points)
- Missing file in the request / no file field (3 points)
- File extension does not match MIME type (spoofed extension) (3 points)
- Malformed multipart form data (3 points)

Storage failure modes (25 points):
- Disk full / write permission denied (5 points)
- Storage directory does not exist (create it or error) (5 points)
- Partial write / interrupted upload (cleanup temp files) (5 points)
- Atomic write pattern (write to temp, then rename) (5 points)
- Virus/malware scanning hook or mention (5 points)

Concurrency and resource failure modes (20 points):
- Concurrent uploads with same filename (5 points)
- Request timeout during upload (5 points)
- Memory limits (streaming vs buffering entire file) (5 points)
- Connection drop mid-upload (cleanup) (5 points)

Response and logging (15 points):
- Proper HTTP status codes: 400 (bad request), 413 (too large), 415 (unsupported type),
  500 (server error), 201 (created) (5 points)
- Structured error responses with error codes, not just messages (5 points)
- Logging of upload attempts, failures, and successes (5 points)

Code quality (10 points):
- Clean separation of validation, storage, and response logic (5 points)
- Type hints and docstrings (5 points)

Deduct 10 points if the handler reads the entire file into memory before checking size.
The more failure modes handled, the higher the score."""


class UserRegistrationValidation(BaseTest):
    """cth-2: User registration with thorough input validation."""

    def _eval_regex(self, output: str) -> EvalResult:
        score = 0.0
        details = {"checks": {}}

        validations = [
            (r'(?:email|e-mail).*(?:valid|regex|format|@)', "email_validation"),
            (r'(?:password|passwd).*(?:length|min|max|strong|entropy|hash|bcrypt|argon)', "password_strength"),
            (r'(?:username|user_name).*(?:length|character|alphanumeric|regex|sanitize)', "username_validation"),
            (r'(?:SQL|inject|sqlinjection|parameteriz|prepared\s*statement)', "sql_injection"),
            (r'(?:XSS|cross.site|sanitiz|escape|html)', "xss_prevention"),
            (r'(?:rate.limit|throttl|brute.force|too\s*many)', "rate_limiting"),
            (r'(?:duplicate|unique|already\s*exists|conflict)', "duplicate_check"),
            (r'(?:strip|trim|whitespace|normalize)', "input_normalization"),
            (r'(?:unicode|homoglyph|confusable|IDN|punycode)', "unicode_handling"),
            (r'(?:disposable|temporary|throwaway).*(?:email|domain)', "disposable_email"),
        ]

        for pattern, label in validations:
            if re.search(pattern, output, re.IGNORECASE):
                score += 10.0
                details["checks"][label] = True
            else:
                details["checks"][label] = False

        return EvalResult(score=min(100.0, score), details=details)

    def _get_judge_rubric(self) -> str:
        return """Score the response on these criteria (total 100 points):

Email validation (15 points):
- Format validation using regex or library (5 points)
- Domain existence check / MX record lookup mention (3 points)
- Normalization (lowercase, trim whitespace) (3 points)
- Disposable email domain blocking or mention (2 points)
- Unicode/IDN domain handling or mention (2 points)

Username validation (15 points):
- Length constraints (min 3, max specified) (3 points)
- Character whitelist (alphanumeric + limited special chars) (3 points)
- Reserved word blocking (admin, root, etc.) (3 points)
- Profanity/offensive word filtering or mention (3 points)
- Unicode homoglyph attack prevention or mention (3 points)

Password validation (20 points):
- Minimum length (at least 8, preferably 12+) (3 points)
- Complexity requirements OR entropy-based scoring (3 points)
- Breached password check (HaveIBeenPwned API or similar) (4 points)
- NOT storing plaintext — uses bcrypt/argon2 with salt (5 points)
- Maximum length cap to prevent bcrypt DoS (72 byte limit) (3 points)
- Prevents password = username or email (2 points)

Security measures (25 points):
- SQL injection prevention via parameterized queries (5 points)
- XSS prevention via output encoding / input sanitization (5 points)
- CSRF protection mention (3 points)
- Rate limiting on registration endpoint (5 points)
- Account enumeration prevention (same response for existing/new email) (4 points)
- Input length limits on all fields to prevent DoS (3 points)

Edge cases and error handling (15 points):
- Duplicate email/username (with timing-safe comparison) (5 points)
- Concurrent registration race condition (unique constraint in DB) (5 points)
- Proper error messages that don't leak internal details (5 points)

Code quality (10 points):
- Clean separation of validation logic (5 points)
- Type hints and structured error responses (5 points)"""


class ComprehensiveTestSuite(BaseTest):
    """cth-3: Write comprehensive tests for a utility function."""

    def _get_judge_rubric(self) -> str:
        return """Score the response on these criteria (total 100 points):

Test coverage breadth (40 points):
- Happy path tests: normal input produces expected output (5 points)
- Empty input: empty string, empty list, None (5 points)
- Single element input (3 points)
- Boundary values: 0, -1, 1, MAX_INT, MIN_INT equivalents (5 points)
- Large input: very long strings or lists (3 points)
- Type errors: wrong type passed (int instead of str, etc.) (5 points)
- Special characters: unicode, emoji, null bytes, newlines (5 points)
- Duplicate values in input (3 points)
- Already-sorted / reverse-sorted input (where applicable) (3 points)
- Whitespace edge cases: spaces, tabs, mixed (3 points)

Test quality (30 points):
- Each test has a clear, descriptive name explaining what it tests (5 points)
- Each test tests ONE thing (single assertion focus, not kitchen-sink tests) (5 points)
- Uses parameterized tests where appropriate to reduce duplication (5 points)
- Tests are independent — no shared mutable state between tests (5 points)
- Uses appropriate assertion methods (assertEqual, assertRaises, assertIn, etc.) (5 points)
- Includes at least one test using assertRaises for expected exceptions (5 points)

Test structure (15 points):
- Uses a proper test framework (pytest or unittest) (5 points)
- Tests are organized in a logical order (happy path first, edge cases, error cases) (5 points)
- Setup/teardown or fixtures used where appropriate (5 points)

Error case testing (15 points):
- Tests that expected exceptions are raised with correct exception type (5 points)
- Tests that error messages are informative (5 points)
- Tests that the function does not mutate input data (5 points)

The more distinct test scenarios covered, the higher the score. Deduct 10 points
if tests share mutable state. Deduct 15 points if fewer than 10 test cases total."""


# ── Build test instances ──────────────────────────────────────────────

_cth1 = FileUploadHandler(
    id="cth-1",
    name="File Upload Handler",
    category_id="code-thoroughness",
    description="Implement a file upload handler that addresses as many failure modes as possible.",
    eval_type="llm_judge",
    prompt="""Implement a robust file upload handler in Python (using Flask or FastAPI) that handles as many failure modes as possible. The handler should accept image uploads (JPEG, PNG, GIF, WebP) up to 10MB.

Endpoint: POST /api/upload

Your implementation will be scored based on how many failure modes and edge cases you address. Think about everything that can go wrong with a file upload and handle it. Here are the categories to consider:

1. INPUT VALIDATION: What could be wrong with the uploaded file itself? Think about size, type, format, filename, content.

2. STORAGE: What could go wrong when writing the file to disk? Think about disk space, permissions, partial writes, atomicity.

3. CONCURRENCY: What happens with simultaneous uploads? Race conditions? Resource exhaustion?

4. SECURITY: What attack vectors exist through file uploads? Path traversal, malicious content, spoofed types?

5. RELIABILITY: What happens if the connection drops? If the server restarts mid-upload? If disk is full halfway through?

Requirements:
- Use proper HTTP status codes (400, 413, 415, 500, 201)
- Return structured JSON error responses with error codes
- Log all upload attempts (success and failure)
- Use streaming/chunked reading — do NOT read the entire file into memory
- Use atomic write pattern (write to temp file, then rename)
- Sanitize filenames thoroughly
- Validate MIME type by checking magic bytes, not just the Content-Type header or file extension

Provide the complete implementation with all imports. The more failure modes you handle, the higher your score. Include comments explaining each failure mode you are addressing.""",
)

_cth2 = UserRegistrationValidation(
    id="cth-2",
    name="User Registration Validation",
    category_id="code-thoroughness",
    description="Implement user registration with thorough input validation covering security edge cases.",
    eval_type="composite",
    prompt="""Implement a user registration endpoint in Python (Flask or FastAPI) with THOROUGH input validation. The endpoint accepts: email, username, password, and display_name.

Endpoint: POST /api/register

Your implementation will be scored on how many validation checks and security measures you include. Be as thorough as possible — think about every possible invalid input, attack vector, and edge case.

Consider these areas:
1. EMAIL: Format validation, normalization, domain checks, disposable email blocking, unicode/IDN handling.
2. USERNAME: Length limits, character restrictions, reserved words, offensive content, homoglyph attacks.
3. PASSWORD: Strength requirements, breached password checks, hashing (bcrypt/argon2), maximum length DoS prevention, no similarity to username/email.
4. SECURITY: SQL injection, XSS, CSRF, rate limiting, account enumeration prevention, timing-safe comparisons.
5. EDGE CASES: Duplicate registration, concurrent signups, input normalization (whitespace, unicode), proper error messages that don't leak information.

Requirements:
- Use parameterized queries (not string concatenation) for any database operations
- Hash passwords with bcrypt or argon2 (NOT MD5, SHA-256, or plain text)
- Return structured error responses that list ALL validation failures, not just the first one
- Do not reveal whether an email is already registered (account enumeration prevention)
- Include rate limiting logic or decorator
- Sanitize all inputs before storage
- Use proper HTTP status codes

Provide the complete implementation. The more validation checks and security measures you include, the higher your score.""",
)

_cth3 = ComprehensiveTestSuite(
    id="cth-3",
    name="Comprehensive Test Suite",
    category_id="code-thoroughness",
    description="Write a comprehensive test suite for a utility function, covering as many edge cases as possible.",
    eval_type="llm_judge",
    prompt="""Write a comprehensive test suite for the following Python utility function. Your score depends on how many distinct, meaningful test cases you write. Aim for maximum coverage of edge cases, boundary values, and error conditions.

```python
def parse_duration(input_string: str) -> int:
    \"\"\"Parse a human-readable duration string and return total seconds.

    Supported formats:
        "30s" or "30 seconds" -> 30
        "5m" or "5 minutes" -> 300
        "2h" or "2 hours" -> 7200
        "1d" or "1 day" -> 86400
        "1h 30m" or "1 hour 30 minutes" -> 5400
        "1d 2h 30m 15s" -> 95415

    Rules:
        - Units can be abbreviated (s, m, h, d) or full words (seconds, minutes, hours, days)
        - Singular and plural forms accepted (hour/hours, minute/minutes)
        - Whitespace between number and unit is optional ("5m" == "5 m" == "5 minutes")
        - Multiple components can be combined ("1h 30m 15s")
        - Values must be non-negative integers
        - Raises ValueError for invalid input (empty string, negative values, unknown units, non-numeric values)
        - Raises TypeError if input is not a string
        - Components can appear in any order ("30m 1h" == "1h 30m")
        - Duplicate units are allowed and summed ("1h 2h" == "3h" == 10800)
    \"\"\"
    pass  # Implementation not shown
```

Requirements for your test suite:
- Use pytest (not unittest)
- Use `pytest.mark.parametrize` for related test groups
- Each test should have a descriptive name starting with `test_`
- Each test should test ONE specific behavior
- Include tests for: happy path, edge cases, boundary values, error cases, type errors, special inputs
- Tests must be independent (no shared mutable state)
- Include at least 25 distinct test cases
- Organize tests logically: basic cases first, then edge cases, then error cases

Provide the complete test file with all imports.""",
)


CODE_THOROUGHNESS_TESTS = [_cth1, _cth2, _cth3]
