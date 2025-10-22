# Test‑Suite Evaluation

## 1. Coverage Snapshot

**Statement Coverage**: `<nn.%>`
**Branch Coverage**: `<nn.%>`

```text
<Explain which uncovered statements are:
- Actually testable and represent gaps
- Unreachable in the current environment (e.g., platform-specific code, error handlers for impossible conditions)
- Not requiring coverage (e.g., debug statements, defensive programming)>
```

---

## 2. Execution Summary

| Item                     | Count | % of Total |
|--------------------------|------:|-----------:|
| **Total Tests Executed** | `<N>` |      100 % |
| **Passing Tests**        | `<N>` |   `<nn.%>` |
| **Failing Tests**        | `<N>` |   `<nn.%>` |
| **Skipped / Ignored**    | `<N>` |   `<nn.%>` |

**Total Runtime:** `<hh:mm:ss>`

---

## 3. Analysis of Requirements Coverage

<!-- If all requirements are covered sufficently, state "✅ All requirements covered" -->

<For EACH requirement with missing coverage, provide the following structure:>

### Requirement `<id>`
**Title**: `<title>`
**Acceptance**: `<acceptance>`

**Covered Behavior:**
`<Describe which part of the accptance is already covered by which test.>`

**Missing Behavior:**
`<Describe which part of the acceptance is currently uncovered by any test. Add important information like values to test.>`

---

## 4. Areas for Improvement

### Missing Test Coverage (Testable Gaps)
- `<Specific module/function lacking tests that COULD be tested>`
- `<Edge cases not covered>`
- `<Error handling paths not tested (that are reachable)>`

### Untestable Code (Acceptable Gaps)
- `<Code that cannot be tested in current environment with explanation>`
- `<Platform-specific code not executable>`
- `<Defensive checks for impossible states>`

### Test Quality Issues
- `<Tests with unclear assertions>`
- `<Tests missing important edge cases>`
- `<Slow or flaky tests needing refactor>`

---

## 5. Future Work

### Verdict: `<REWORK | FINAL>`

**Justification:**
```text
<Clear explanation of the decision:
- If REWORK: List specific critical testable gaps that must be addressed
- If FINAL: Confirm all tests pass and coverage is adequate given the context and mention possible improvements>
```
