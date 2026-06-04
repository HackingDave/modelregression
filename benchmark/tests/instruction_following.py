import re
from .base import BaseTest, EvalResult


class ExactListFormat(BaseTest):
    """if-1: List exactly 7 programming languages with specific format."""

    def _eval_regex(self, output: str) -> EvalResult:
        score = 0.0
        details = {"checks": {}}

        # Check for exactly 7 numbered items (1. through 7.)
        numbered_items = re.findall(r'^\s*(\d+)\.\s+', output, re.MULTILINE)
        num_count = len(numbered_items)
        details["checks"]["item_count"] = num_count

        if num_count == 7:
            score += 30.0
            details["checks"]["exactly_7_items"] = True
        elif num_count >= 5 and num_count <= 9:
            score += 10.0
            details["checks"]["exactly_7_items"] = False
        else:
            details["checks"]["exactly_7_items"] = False

        # Check format: "N. LanguageName (YYYY) - one sentence description"
        format_pattern = r'^\s*\d+\.\s+\w[\w\s#+]*\(\d{4}\)\s*[-–—]\s*.+$'
        formatted_items = re.findall(format_pattern, output, re.MULTILINE)
        details["checks"]["correctly_formatted_items"] = len(formatted_items)

        if len(formatted_items) == 7:
            score += 25.0
        elif len(formatted_items) >= 5:
            score += 15.0
        elif len(formatted_items) >= 3:
            score += 8.0

        # Check that years are after 2010
        years = re.findall(r'\((\d{4})\)', output)
        valid_years = [y for y in years if int(y) > 2010]
        details["checks"]["years_found"] = years
        details["checks"]["years_after_2010"] = valid_years

        if len(valid_years) == 7:
            score += 25.0
        elif len(valid_years) >= 5:
            score += 15.0

        # Check that descriptions are single sentences (no period mid-line followed by capital)
        # Each item should have exactly one sentence after the dash
        multi_sentence_items = re.findall(
            r'[-–—]\s*[^.!?]*[.!?]\s+[A-Z]', output
        )
        if len(multi_sentence_items) == 0:
            score += 10.0
            details["checks"]["single_sentence_descriptions"] = True
        else:
            details["checks"]["single_sentence_descriptions"] = False
            details["checks"]["multi_sentence_count"] = len(multi_sentence_items)

        # Check no extra content besides the list (no preamble or postamble)
        lines = [l.strip() for l in output.strip().split('\n') if l.strip()]
        non_item_lines = [l for l in lines if not re.match(r'^\d+\.', l)]
        if len(non_item_lines) == 0:
            score += 10.0
            details["checks"]["no_extra_content"] = True
        else:
            details["checks"]["no_extra_content"] = False
            details["checks"]["extra_lines"] = len(non_item_lines)

        return EvalResult(score=min(100.0, score), details=details)


class ConstrainedFunction(BaseTest):
    """if-2: Write a function with 5 specific constraints."""

    def _eval_regex(self, output: str) -> EvalResult:
        score = 0.0
        details = {"checks": {}}

        # Constraint 1: Function name must be exactly "transform_records"
        if re.search(r'def\s+transform_records\s*\(', output):
            score += 15.0
            details["checks"]["correct_function_name"] = True
        else:
            details["checks"]["correct_function_name"] = False

        # Constraint 2: Must take exactly 2 parameters: records (list[dict]) and key (str)
        if re.search(r'def\s+transform_records\s*\(\s*records\s*:\s*list\s*\[\s*dict\s*\]\s*,\s*key\s*:\s*str\s*\)', output):
            score += 15.0
            details["checks"]["correct_parameters"] = True
        else:
            details["checks"]["correct_parameters"] = False

        # Constraint 3: Return type must be list[str]
        if re.search(r'->\s*list\s*\[\s*str\s*\]', output):
            score += 15.0
            details["checks"]["correct_return_type"] = True
        else:
            details["checks"]["correct_return_type"] = False

        # Constraint 4: Must use a list comprehension (not a for loop with .append)
        if re.search(r'\[.*\bfor\b.*\bin\b.*\]', output, re.DOTALL):
            score += 15.0
            details["checks"]["uses_list_comprehension"] = True
        else:
            details["checks"]["uses_list_comprehension"] = False

        # Constraint 5: Must have exactly 3 comment lines (# ...) inside the function
        # Find the function body
        func_match = re.search(r'def\s+transform_records\s*\([^)]*\)[^:]*:(.*?)(?=\ndef\s|\Z)', output, re.DOTALL)
        if func_match:
            func_body = func_match.group(1)
            comments = re.findall(r'^\s*#[^!].*$', func_body, re.MULTILINE)
            details["checks"]["comment_count"] = len(comments)
            if len(comments) == 3:
                score += 15.0
                details["checks"]["exactly_3_comments"] = True
            else:
                details["checks"]["exactly_3_comments"] = False
        else:
            details["checks"]["exactly_3_comments"] = False
            details["checks"]["comment_count"] = 0

        # Constraint 6: Function body must be 10 lines or fewer (excluding blank lines)
        if func_match:
            body_lines = [l for l in func_match.group(1).split('\n') if l.strip()]
            details["checks"]["body_line_count"] = len(body_lines)
            if len(body_lines) <= 10:
                score += 15.0
                details["checks"]["under_10_lines"] = True
            else:
                details["checks"]["under_10_lines"] = False
        else:
            details["checks"]["under_10_lines"] = False
            details["checks"]["body_line_count"] = "unknown"

        # Bonus: Check for docstring
        if func_match and re.search(r'""".*?"""|\'\'\'.*?\'\'\'', func_match.group(1), re.DOTALL):
            score += 10.0
            details["checks"]["has_docstring"] = True
        else:
            details["checks"]["has_docstring"] = False

        return EvalResult(score=min(100.0, score), details=details)

    def _get_judge_rubric(self) -> str:
        return """Score the response on constraint compliance (total 100 points):
- Function named exactly 'transform_records' (15 points)
- Parameters exactly 'records: list[dict]' and 'key: str' (15 points)
- Return type annotated as 'list[str]' (15 points)
- Uses a list comprehension for the core logic (not a loop with .append) (15 points)
- Exactly 3 comment lines (# ...) inside the function body (15 points)
- Function body is 10 lines or fewer, excluding blank lines (15 points)
- Has a docstring (10 bonus points, cap at 100)
Deduct full points per constraint for each constraint not met. Partial credit only
if the constraint is approximately met (e.g., 2 or 4 comments instead of 3 = 5 points)."""


class RestrictedExplanation(BaseTest):
    """if-3: Explain hash tables WITHOUT certain words, no bullets, under 200 words."""

    def _eval_regex(self, output: str) -> EvalResult:
        score = 0.0
        details = {"checks": {}}

        # Check word count
        words = output.split()
        word_count = len(words)
        details["checks"]["word_count"] = word_count

        if word_count <= 200:
            score += 25.0
            details["checks"]["under_200_words"] = True
        elif word_count <= 220:
            score += 15.0
            details["checks"]["under_200_words"] = False
        else:
            details["checks"]["under_200_words"] = False

        # Check for forbidden words (case-insensitive)
        forbidden = ["bucket", "collision", "key-value"]
        found_forbidden = []
        for word in forbidden:
            if re.search(r'\b' + re.escape(word) + r'\b', output, re.IGNORECASE):
                found_forbidden.append(word)

        details["checks"]["forbidden_words_found"] = found_forbidden

        if len(found_forbidden) == 0:
            score += 30.0
            details["checks"]["no_forbidden_words"] = True
        elif len(found_forbidden) == 1:
            score += 15.0
            details["checks"]["no_forbidden_words"] = False
        else:
            details["checks"]["no_forbidden_words"] = False

        # Check for NO bullet points (-, *, •, numbered lists 1., 2.)
        bullet_patterns = [
            r'^\s*[-*•]\s+',       # dash, asterisk, bullet
            r'^\s*\d+[.)]\s+',     # numbered lists
        ]
        has_bullets = False
        for pattern in bullet_patterns:
            if re.search(pattern, output, re.MULTILINE):
                has_bullets = True
                break

        if not has_bullets:
            score += 25.0
            details["checks"]["no_bullet_points"] = True
        else:
            details["checks"]["no_bullet_points"] = False

        # Check that the explanation actually discusses hash tables (contains relevant content)
        hash_table_terms = ['hash', 'table', 'array', 'index', 'function', 'store', 'lookup', 'address', 'map']
        found_terms = [t for t in hash_table_terms if re.search(r'\b' + t + r'\b', output, re.IGNORECASE)]
        details["checks"]["relevant_terms_found"] = found_terms

        if len(found_terms) >= 4:
            score += 20.0
            details["checks"]["relevant_content"] = True
        elif len(found_terms) >= 2:
            score += 10.0
            details["checks"]["relevant_content"] = "partial"
        else:
            details["checks"]["relevant_content"] = False

        return EvalResult(score=min(100.0, score), details=details)


# ── Build test instances ──────────────────────────────────────────────

_if1 = ExactListFormat(
    id="if-1",
    name="Exact List Format",
    category_id="instruction-following",
    description="List exactly 7 programming languages released after 2010 in a specific format, with no extra content.",
    eval_type="regex",
    prompt="""List exactly 7 programming languages that were first released after the year 2010.

You MUST follow this exact format for each item:
<number>. <LanguageName> (<year>) - <one sentence description>

Rules:
1. List EXACTLY 7 languages — not 6, not 8.
2. Each language must have been first released (v1.0 or initial public release) AFTER 2010, meaning 2011 or later.
3. Each item must be on its own line.
4. The format must be exactly: number, period, space, language name, space, year in parentheses, space, dash, space, one sentence description.
5. Each description must be exactly ONE sentence (one period at the end, no additional sentences).
6. Do NOT include any text before the list (no introduction, no "Here are..." preamble).
7. Do NOT include any text after the list (no summary, no notes, no caveats).
8. Output ONLY the 7 numbered items, nothing else.

Example of the correct format (do NOT use this language, it's just to show format):
1. ExampleLang (2015) - A language designed for example purposes only.""",
)

_if2 = ConstrainedFunction(
    id="if-2",
    name="Constrained Function",
    category_id="instruction-following",
    description="Write a Python function that satisfies exactly 6 specific constraints on naming, parameters, return type, style, and length.",
    eval_type="composite",
    prompt="""Write a Python function that meets ALL of the following constraints. Every constraint is mandatory — violating any one of them reduces your score.

Constraint 1 — Name: The function MUST be named exactly `transform_records`.

Constraint 2 — Parameters: The function MUST take exactly 2 parameters:
  - `records: list[dict]` — a list of dictionaries
  - `key: str` — a dictionary key to extract

Constraint 3 — Return type: The return type annotation MUST be `list[str]`.

Constraint 4 — Implementation: The core logic MUST use a list comprehension. Do NOT use a for loop with .append().

Constraint 5 — Comments: The function body MUST contain EXACTLY 3 comment lines (lines starting with #). Not 2, not 4 — exactly 3.

Constraint 6 — Length: The function body (everything after the def line, excluding blank lines) MUST be 10 lines or fewer.

The function should:
- Extract the value of `key` from each dictionary in `records`
- Convert each value to a string
- Skip dictionaries that don't have the key (don't include them in output)
- Return the list of string values

Include a docstring (this does not count toward the comment lines or the line limit).

Output ONLY the function definition — no explanation, no usage examples, no test code. Just the function.""",
)

_if3 = RestrictedExplanation(
    id="if-3",
    name="Restricted Explanation",
    category_id="instruction-following",
    description="Explain hash tables without using certain forbidden words, no bullet points, under 200 words.",
    eval_type="regex",
    prompt="""Explain how a hash table works to a computer science student.

You must follow ALL of these rules:
1. Do NOT use the word "bucket" anywhere in your explanation.
2. Do NOT use the word "collision" anywhere in your explanation.
3. Do NOT use the hyphenated term "key-value" anywhere in your explanation.
4. Do NOT use bullet points, dashes as list markers, asterisks as list markers, or numbered lists. Write in paragraph form ONLY.
5. Your explanation must be UNDER 200 words total.
6. Despite these restrictions, your explanation must be accurate, clear, and cover: how data is stored, how the hash function maps data to positions, and how retrieval works.

Write your explanation as flowing prose paragraphs. Do not start with "Sure," or "Here's an explanation" or any preamble — begin directly with the explanation content.""",
)


INSTRUCTION_FOLLOWING_TESTS = [_if1, _if2, _if3]
