import re
from .base import BaseTest, EvalResult


class SQLParameterizedQueries(BaseTest):
    """sa-1: Write a user lookup function with SQL — check for parameterized queries."""

    def _eval_regex(self, output: str) -> EvalResult:
        score = 0.0
        details = {"checks": {}}

        # Check for parameterized query markers
        param_patterns = [
            (r'\?\s*[,\)]|\%s|\$\d+|:\w+', "uses_parameterized_placeholders"),
        ]
        for pattern, label in param_patterns:
            if re.search(pattern, output):
                score += 30.0
                details["checks"][label] = True
            else:
                details["checks"][label] = False

        # Check for ABSENCE of string concatenation/formatting in SQL
        # These are red flags for SQL injection
        dangerous_patterns = [
            (r'f"[^"]*SELECT[^"]*{', "f_string_sql"),
            (r'f\'[^\']*SELECT[^\']*{', "f_string_sql_single"),
            (r'"[^"]*SELECT[^"]*"\s*\+', "concat_sql"),
            (r"'[^']*SELECT[^']*'\s*\+", "concat_sql_single"),
            (r'%\s*\(.*\)|\.format\(', "format_sql"),
        ]
        has_dangerous = False
        for pattern, label in dangerous_patterns:
            if re.search(pattern, output, re.IGNORECASE):
                has_dangerous = True
                details["checks"][f"DANGEROUS_{label}"] = True

        if not has_dangerous:
            score += 30.0
            details["checks"]["no_string_concatenation_in_sql"] = True
        else:
            details["checks"]["no_string_concatenation_in_sql"] = False

        # Check for input validation
        if re.search(r'(?:valid|sanitiz|strip|escape|isinstance|type\s*check)', output, re.IGNORECASE):
            score += 20.0
            details["checks"]["input_validation"] = True
        else:
            details["checks"]["input_validation"] = False

        # Check for error handling
        if re.search(r'(?:try|except|catch|raise|Error)', output):
            score += 20.0
            details["checks"]["error_handling"] = True
        else:
            details["checks"]["error_handling"] = False

        return EvalResult(score=min(100.0, score), details=details)

    def _get_judge_rubric(self) -> str:
        return """Score the response on these criteria (total 100 points):
- Uses parameterized queries / prepared statements for ALL SQL (not string formatting) (30 points)
- Does NOT use f-strings, .format(), string concatenation, or % formatting to build SQL (20 points)
- Includes input validation before the query (type check, length check, sanitization) (10 points)
- Returns structured results, not raw database rows (5 points)
- Handles "not found" case gracefully (returns None or empty, not exception) (5 points)
- Handles database connection errors with try/except (5 points)
- Uses a context manager or proper connection/cursor cleanup (5 points)
- Includes a docstring explaining the function and its security considerations (5 points)
- Mentions SQL injection in comments or docstring as the reason for parameterization (5 points)
- Handles edge cases: empty user_id, None, very long strings (10 points)
Deduct ALL 30 parameterization points if any SQL query uses string formatting/concatenation."""


class VulnerabilityCodeReview(BaseTest):
    """sa-2: Review code with 5 planted vulnerabilities."""

    def _get_judge_rubric(self) -> str:
        return """Score the response on these criteria (total 100 points):

The code contains exactly 5 planted vulnerabilities. Award 16 points per vulnerability correctly identified, plus 20 points for overall quality:

Vulnerability 1 — Cross-Site Scripting (XSS) (16 points):
- Identifies that user_input is rendered directly into HTML without escaping in the
  /profile endpoint (the name field is injected into the template via f-string) (16 points)

Vulnerability 2 — CSRF (Cross-Site Request Forgery) (16 points):
- Identifies that the POST /transfer endpoint has no CSRF token validation,
  allowing cross-origin form submissions to transfer funds (16 points)

Vulnerability 3 — Path Traversal (16 points):
- Identifies that the /download endpoint uses user-supplied filename directly
  in os.path.join without validating or sanitizing "../" sequences (16 points)

Vulnerability 4 — Insecure Deserialization (16 points):
- Identifies the use of pickle.loads() on user-supplied data in the /import endpoint,
  which allows arbitrary code execution (16 points)

Vulnerability 5 — Hardcoded Secret (16 points):
- Identifies the hardcoded JWT_SECRET = "supersecret123" in the source code,
  which should be loaded from environment variables (16 points)

Quality bonus (20 points):
- For each vulnerability, provides a clear explanation of the attack vector (5 points)
- For each vulnerability, provides a specific remediation (5 points)
- Severity ratings are reasonable (5 points)
- No false positives (claiming something is a vulnerability when it is not) (5 points)

Deduct 5 points for each false positive. Maximum score is 100."""


class SafeFileDownload(BaseTest):
    """sa-3: Implement a file download endpoint safely."""

    def _eval_regex(self, output: str) -> EvalResult:
        score = 0.0
        details = {"checks": {}}

        # Path traversal prevention
        traversal_patterns = [
            (r'(?:os\.path\.(?:abspath|realpath|normpath)|Path\(.*\)\.resolve)', "path_normalization"),
            (r'(?:startswith|is_relative_to|\.parts)', "path_containment_check"),
            (r'(?:\.\.|\.\.\/|\.\.\\\\)', "mentions_dot_dot"),
        ]
        for pattern, label in traversal_patterns:
            if re.search(pattern, output):
                score += 15.0
                details["checks"][label] = True
            else:
                details["checks"][label] = False

        # Filename sanitization
        if re.search(r'(?:secure_filename|sanitiz|whitelist|regex.*filename|[^a-zA-Z0-9])', output, re.IGNORECASE):
            score += 15.0
            details["checks"]["filename_sanitization"] = True
        else:
            details["checks"]["filename_sanitization"] = False

        # MIME type / Content-Disposition
        if re.search(r'(?:Content-Disposition|content_type|mimetype|send_file)', output, re.IGNORECASE):
            score += 10.0
            details["checks"]["content_headers"] = True
        else:
            details["checks"]["content_headers"] = False

        # File existence check
        if re.search(r'(?:os\.path\.exists|\.exists\(\)|isfile|404)', output):
            score += 10.0
            details["checks"]["existence_check"] = True
        else:
            details["checks"]["existence_check"] = False

        return EvalResult(score=min(100.0, score), details=details)

    def _get_judge_rubric(self) -> str:
        return """Score the response on these criteria (total 100 points):

Path traversal prevention (30 points):
- Normalizes the requested path using os.path.realpath or pathlib resolve (10 points)
- Verifies the resolved path starts with / is inside the allowed download directory (10 points)
- Explicitly handles ".." sequences and rejects them (5 points)
- Handles URL-encoded traversal attempts (%2e%2e%2f) (5 points)

Filename handling (15 points):
- Sanitizes filename (strips path separators, null bytes, special characters) (5 points)
- Uses werkzeug.utils.secure_filename or equivalent (5 points)
- Rejects filenames starting with a dot (hidden files) (5 points)

Access control (15 points):
- Restricts downloads to an allowed directory (configurable base path) (5 points)
- File type restriction (whitelist of allowed extensions) (5 points)
- Authentication/authorization check or mention (5 points)

Response handling (20 points):
- Sets Content-Disposition header to 'attachment' with sanitized filename (5 points)
- Sets correct Content-Type based on file MIME type (5 points)
- Uses streaming response (send_file or equivalent) instead of reading file to memory (5 points)
- Returns 404 for missing files, 403 for unauthorized, 400 for invalid input (5 points)

Additional security (10 points):
- Rate limiting or mention of it (3 points)
- File size check or limit (3 points)
- Logging of download attempts (4 points)

Code quality (10 points):
- Clean error handling (5 points)
- Type hints and docstring (5 points)

Deduct 40 points if path traversal is possible (no containment check after resolve)."""


# ── Build test instances ──────────────────────────────────────────────

_sa1 = SQLParameterizedQueries(
    id="sa-1",
    name="SQL Parameterized Queries",
    category_id="security-awareness",
    description="Write a user lookup function that uses SQL safely, checking for parameterized queries and absence of string concatenation.",
    eval_type="composite",
    prompt="""Write a Python function `find_user(user_id: str) -> dict | None` that looks up a user in a SQLite database and returns their profile information.

The function should:
1. Connect to a SQLite database file at a configurable path (parameter or module constant).
2. Query the `users` table which has columns: id (TEXT), username (TEXT), email (TEXT), created_at (TEXT), role (TEXT).
3. Return a dictionary with the user's data if found, or None if not found.
4. Handle all error cases: database connection failures, invalid user_id input, missing table, etc.
5. Clean up resources properly (close connections/cursors).

Additionally, write a companion function `search_users(name_query: str, role: str = None) -> list[dict]` that:
1. Searches for users whose username contains the search term (case-insensitive LIKE query).
2. Optionally filters by role if provided.
3. Returns a list of matching user dictionaries.

Requirements:
- The code must be secure against SQL injection attacks.
- Include input validation before executing any queries.
- Use proper resource management (context managers).
- Include type hints and docstrings.
- Handle edge cases: empty strings, None values, very long strings, strings with SQL special characters (quotes, semicolons).

Provide the complete implementation with all imports. Include a brief comment explaining your approach to SQL injection prevention.""",
)

_sa2 = VulnerabilityCodeReview(
    id="sa-2",
    name="Vulnerability Code Review",
    category_id="security-awareness",
    description="Review code with 5 planted security vulnerabilities and identify all of them.",
    eval_type="llm_judge",
    prompt="""Review the following Python Flask web application code for security vulnerabilities. Identify ALL security issues, explain the attack vector for each, rate its severity (Critical/High/Medium/Low), and provide a specific code fix.

```python
import os
import pickle
import sqlite3
from flask import Flask, request, render_template_string, send_file, redirect

app = Flask(__name__)
JWT_SECRET = "supersecret123"
UPLOAD_DIR = "/var/app/uploads"
DOWNLOAD_DIR = "/var/app/downloads"

def get_db():
    return sqlite3.connect("app.db")

@app.route("/profile/<username>")
def profile(username):
    db = get_db()
    cursor = db.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    if not user:
        return "User not found", 404
    # Render profile page
    html = f\"\"\"
    <html>
    <body>
        <h1>Profile: {user[1]}</h1>
        <p>Bio: {user[3]}</p>
        <p>Email: {user[2]}</p>
    </body>
    </html>
    \"\"\"
    return render_template_string(html)

@app.route("/transfer", methods=["POST"])
def transfer_funds():
    sender = request.form.get("sender")
    recipient = request.form.get("recipient")
    amount = float(request.form.get("amount", 0))
    db = get_db()
    db.execute("UPDATE accounts SET balance = balance - ? WHERE user_id = ?", (amount, sender))
    db.execute("UPDATE accounts SET balance = balance + ? WHERE user_id = ?", (amount, recipient))
    db.commit()
    return redirect("/dashboard")

@app.route("/download")
def download_file():
    filename = request.args.get("file", "")
    filepath = os.path.join(DOWNLOAD_DIR, filename)
    return send_file(filepath)

@app.route("/import", methods=["POST"])
def import_data():
    data = request.get_data()
    try:
        records = pickle.loads(data)
        db = get_db()
        for record in records:
            db.execute("INSERT INTO imports (data) VALUES (?)", (str(record),))
        db.commit()
        return {"imported": len(records)}
    except Exception as e:
        return {"error": str(e)}, 400

@app.route("/search")
def search():
    query = request.args.get("q", "")
    db = get_db()
    cursor = db.execute("SELECT * FROM products WHERE name LIKE ?", (f"%{query}%",))
    results = cursor.fetchall()
    return {"results": [dict(r) for r in results]}

if __name__ == "__main__":
    app.run(debug=True)
```

For your review:
1. Identify EVERY security vulnerability in this code.
2. For each vulnerability, provide: the vulnerability type (e.g., XSS, CSRF), the specific line(s) affected, the attack vector (how an attacker would exploit it), the severity level, and a concrete code fix.
3. Do not report false positives — only flag genuine security issues.
4. There are at least 5 distinct vulnerabilities. Find all of them.""",
)

_sa3 = SafeFileDownload(
    id="sa-3",
    name="Safe File Download Endpoint",
    category_id="security-awareness",
    description="Implement a file download endpoint that is safe against path traversal and other attacks.",
    eval_type="composite",
    prompt="""Implement a secure file download endpoint in Python (Flask) that serves files from a designated downloads directory. The endpoint must be safe against path traversal attacks, unauthorized access, and other file-serving vulnerabilities.

Endpoint: GET /api/download/<filename>

Requirements:
1. Serve files ONLY from a configured base directory (DOWNLOAD_DIR = "/var/app/downloads").
2. Prevent path traversal attacks — an attacker requesting "../../etc/passwd" must NOT be able to access files outside DOWNLOAD_DIR. Handle all known bypass techniques:
   - Direct "../" sequences
   - URL-encoded variants ("%2e%2e%2f", "%2e%2e/")
   - Double-encoded variants
   - Null byte injection ("%00")
   - Backslash variants on Windows ("..\\")
3. Sanitize the filename: remove path separators, null bytes, and special characters. Use werkzeug.utils.secure_filename or implement equivalent logic.
4. Reject hidden files (filenames starting with ".").
5. Whitelist allowed file extensions (e.g., .pdf, .csv, .xlsx, .txt, .zip).
6. Verify the file exists and return 404 if not.
7. Set proper response headers:
   - Content-Disposition: attachment; filename="<sanitized_name>"
   - Content-Type: appropriate MIME type
   - X-Content-Type-Options: nosniff
   - Cache-Control: no-cache (for sensitive downloads)
8. Use Flask's send_file with the file path (streaming, not reading into memory).
9. Add rate limiting (comment or decorator — at least mention it).
10. Log every download attempt with: timestamp, requested filename, resolved path, IP address, and whether it was allowed or denied.

The KEY security check is: after resolving the full path (os.path.realpath), verify that it starts with the DOWNLOAD_DIR. If not, return 403.

Provide the complete implementation with all imports, the route handler, and helper functions. Include comments explaining each security measure.""",
)


SECURITY_AWARENESS_TESTS = [_sa1, _sa2, _sa3]
