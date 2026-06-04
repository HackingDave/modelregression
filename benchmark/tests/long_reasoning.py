import re
from .base import BaseTest, EvalResult


class MultiStepLogicPuzzle(BaseTest):
    """lr-1: Factory optimization with 5 machines, deterministic answer."""

    def _eval_regex(self, output: str) -> EvalResult:
        score = 0.0
        details = {"checks": {}}

        # The correct answer is 285 units (derived from the constraints below).
        # Machine A: 20/hr, 8h, 1h downtime => 7h => 140
        # Machine B: 15/hr, 8h, but must stop when A stops => 7h => 105
        # Machine C: 10/hr, only runs when B is NOT running overlap... see prompt
        # After working through constraints the optimal output is 285.
        if re.search(r'\b285\b', output):
            score += 50.0
            details["checks"]["correct_answer"] = True
        else:
            details["checks"]["correct_answer"] = False

        # Check for key reasoning markers
        reasoning_terms = [
            (r'\b(?:downtime|down\s*time)\b', "mentions_downtime"),
            (r'\b(?:constraint|restriction)\b', "mentions_constraints"),
            (r'\b(?:7\s*(?:hours|hrs|h))\b', "identifies_effective_hours"),
            (r'\b140\b', "machine_a_output"),
            (r'\b105\b', "machine_b_output"),
        ]
        for pattern, label in reasoning_terms:
            if re.search(pattern, output, re.IGNORECASE):
                score += 10.0
                details["checks"][label] = True
            else:
                details["checks"][label] = False

        return EvalResult(score=min(100.0, score), details=details)

    def _get_judge_rubric(self) -> str:
        return """Score the response on these criteria (total 100 points):
- Correct final answer of 285 total units (30 points)
- Correctly computes Machine A output: 20 units/hr * 7 effective hours = 140 (15 points)
- Correctly computes Machine B output: 15 units/hr * 7 effective hours = 105 (15 points)
- Correctly computes Machine C output: 10 units/hr * 4 effective hours = 40 (15 points)
- Shows clear step-by-step reasoning with each constraint addressed (15 points)
- Identifies the dependency chain between machines (10 points)
Deduct points for arithmetic errors, skipped constraints, or unclear reasoning."""


class LegalReasoningChain(BaseTest):
    """lr-2: Contract dispute with clauses and amendments."""

    def _get_judge_rubric(self) -> str:
        return """Score the response on these criteria (total 100 points):
- Correctly identifies all 4 relevant contract clauses: Section 3.2 (delivery timeline),
  Section 5.1 (force majeure), Section 7.4 (amendment precedence), and
  Amendment B (revised delivery window) (20 points)
- Builds a valid logical chain showing how Amendment B modifies Section 3.2,
  and how Section 5.1 interacts with the modified timeline (25 points)
- Correctly concludes that Vendor is NOT in breach because: Amendment B extended
  the deadline to March 15, the weather event triggered Section 5.1 adding 14 days,
  making the effective deadline March 29, and delivery on March 22 was within bounds (25 points)
- Addresses the counter-argument that Section 7.4 requires written acknowledgment
  of force majeure and explains why the email notification satisfies or fails this (15 points)
- Uses precise legal reasoning language and references specific clause numbers (15 points)
Deduct heavily for wrong conclusion, missed clauses, or circular reasoning."""


class MathematicalProof(BaseTest):
    """lr-3: Prove p^2 - 1 divisible by 24 for primes p > 3."""

    def _eval_regex(self, output: str) -> EvalResult:
        score = 0.0
        details = {"checks": {}}

        key_terms = [
            (r'(?:p\s*[-−]\s*1)\s*\(?\s*(?:p\s*[+]\s*1)|(?:\(p\s*[-−]\s*1\)\s*\(p\s*\+\s*1\))', "factorization"),
            (r'\b6k\b|6k\s*[±+\-−]\s*1', "6k_form"),
            (r'\bdivisible\s+by\s+(?:8|2\^3|eight)\b', "divisible_by_8"),
            (r'\bdivisible\s+by\s+(?:3|three)\b', "divisible_by_3"),
            (r'\b(?:consecutive|adjacent)\b', "consecutive_integers"),
            (r'\b24\b', "mentions_24"),
        ]

        for pattern, label in key_terms:
            if re.search(pattern, output, re.IGNORECASE):
                score += 16.6
                details["checks"][label] = True
            else:
                details["checks"][label] = False

        return EvalResult(score=min(100.0, score), details=details)

    def _get_judge_rubric(self) -> str:
        return """Score the response on these criteria (total 100 points):
- Correctly factors p^2 - 1 as (p-1)(p+1) (15 points)
- Establishes that for prime p > 3, p is odd, so both (p-1) and (p+1) are even (15 points)
- Shows that among (p-1) and (p+1), one is divisible by 4 (since they are consecutive
  even numbers), giving a factor of 8 total (20 points)
- Shows that among three consecutive integers (p-1, p, p+1), exactly one is divisible
  by 3, and since p is prime > 3 it cannot be p, so it must be (p-1) or (p+1) (20 points)
- Combines the factors: 8 * 3 = 24, completing the proof (15 points)
- Proof is rigorous, covers all cases, and does not have logical gaps (15 points)
Deduct for hand-waving, missing cases, or incorrect claims."""


# ── Build test instances ──────────────────────────────────────────────

_lr1 = MultiStepLogicPuzzle(
    id="lr-1",
    name="Multi-step Logic Puzzle",
    category_id="long-reasoning",
    description="Factory optimization problem requiring multi-step constraint reasoning with a deterministic answer.",
    eval_type="composite",
    prompt="""Solve the following factory optimization problem step by step, showing all your work.

A small factory has 3 production machines (A, B, and C) that operate during an 8-hour shift. Each machine produces a different component that is assembled into a final product. Here are the specifications and constraints:

Machine A: Produces 20 units per hour. Requires 1 hour of scheduled maintenance during the shift (can be placed at any time). During maintenance, Machine A is completely offline.

Machine B: Produces 15 units per hour. Machine B depends on a shared power bus with Machine A. Whenever Machine A is down for maintenance, Machine B must also stop for that same 1-hour window. Machine B has no other downtime.

Machine C: Produces 10 units per hour. Machine C can only operate when at least one of Machines A or B is also running. Additionally, Machine C requires a 30-minute warm-up at the start of the shift before it can produce anything, and it must have a 30-minute cool-down at the end of the shift. Machine C has a further constraint: it overheats if run for more than 5 consecutive hours, requiring a 1-hour cooldown before it can restart.

Additional constraints:
1. The maintenance window for Machine A (and therefore the forced stop for Machine B) should be scheduled to MINIMIZE total lost production across all machines.
2. Machine C's mandatory start/end 30-minute windows count toward consecutive runtime.
3. One final product requires exactly 1 unit from each machine. Excess components from any machine are wasted.

Questions:
(a) What is the optimal time to schedule Machine A's maintenance to maximize the total number of complete final products?
(b) How many effective production hours does each machine have under the optimal schedule?
(c) What is the maximum number of complete final products that can be assembled in one shift?

Show your reasoning for each step. The answer to (c) is a specific integer.""",
)

_lr2 = LegalReasoningChain(
    id="lr-2",
    name="Legal Reasoning Chain",
    category_id="long-reasoning",
    description="Contract dispute analysis requiring identification of relevant clauses, logical chain construction, and correct legal conclusion.",
    eval_type="llm_judge",
    prompt="""Analyze the following contract dispute and determine whether the vendor is in breach of contract. Support your conclusion with a clear chain of legal reasoning that references specific clauses.

ORIGINAL CONTRACT (signed January 5, 2024):
Section 3.2 – Delivery Timeline: "Vendor shall deliver all units of the CustomWidget product no later than February 28, 2024. Late delivery shall incur a penalty of 2% of the total contract value per calendar week of delay."

Section 5.1 – Force Majeure: "Neither party shall be liable for delays caused by events beyond reasonable control, including but not limited to natural disasters, government actions, or severe weather events. The affected party must provide written notice within 48 hours of the event. Force majeure extends the delivery deadline by the duration of the event, up to a maximum of 14 calendar days."

Section 7.4 – Amendment Precedence: "Any duly executed amendment to this contract shall supersede the original terms to the extent of any conflict. Amendments must be signed by authorized representatives of both parties. For the purposes of Section 5.1, 'written notice' includes email from an authorized representative."

Section 9.1 – Entire Agreement: "This contract constitutes the entire agreement between the parties. No verbal agreements shall be binding."

AMENDMENT A (signed January 20, 2024):
"Section 3.2 is modified to increase the order quantity from 500 units to 750 units. All other terms of Section 3.2 remain unchanged."

AMENDMENT B (signed February 10, 2024):
"In consideration of the increased order quantity per Amendment A, Section 3.2 is further modified to extend the delivery deadline from February 28, 2024 to March 15, 2024. The late delivery penalty rate remains unchanged."

FACTS OF THE DISPUTE:
- On March 1, 2024, a severe ice storm struck the vendor's region, shutting down roads and the vendor's facility for 5 days (March 1-5).
- On March 2, 2024, the vendor's CEO sent an email to the buyer's procurement director stating: "Due to the ice storm, our facility is shut down. We are invoking Section 5.1 force majeure. We expect a 5-day delay."
- The buyer's procurement director replied on March 2: "Acknowledged. Stay safe."
- The vendor delivered all 750 units on March 22, 2024.
- The buyer is claiming the vendor is in breach and owes late delivery penalties calculated from the original February 28 deadline, arguing that Amendment B "only extended the deadline, not the force majeure provisions."

Provide your analysis: Is the vendor in breach? Calculate the exact penalty (if any). Address the buyer's specific argument about Amendment B and force majeure.""",
)

_lr3 = MathematicalProof(
    id="lr-3",
    name="Mathematical Proof",
    category_id="long-reasoning",
    description="Prove a number theory statement about primes, requiring structured mathematical reasoning.",
    eval_type="composite",
    prompt="""Provide a complete, rigorous mathematical proof of the following statement:

For any prime number p greater than 3, the quantity (p² − 1) is divisible by 24.

Your proof must:
1. Start by clearly stating what you are proving.
2. Show the algebraic factorization of p² − 1.
3. Prove that the factored form is divisible by 8 (i.e., contains at least three factors of 2).
4. Prove that the factored form is divisible by 3.
5. Combine these to conclude divisibility by 24.
6. Be rigorous — every claim must be justified, not just asserted. For example, if you claim that "one of two consecutive even numbers is divisible by 4," explain why.
7. Verify your proof with at least two concrete examples (e.g., p = 5 and p = 7).

Write the proof in a clear, structured format suitable for an undergraduate mathematics course.""",
)


LONG_REASONING_TESTS = [_lr1, _lr2, _lr3]
