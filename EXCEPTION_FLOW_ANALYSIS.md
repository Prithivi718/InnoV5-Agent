# Exception Flow Analysis: Two Exceptions Causing Fallback Failure

## Problem Summary
Two exceptions occur in sequence, causing the fallback pipeline to fail:
1. **First Exception**: `RuntimeError: Semantic error: not_expressible` 
2. **Second Exception**: `UnicodeEncodeError: 'charmap' codec can't encode characters`

---

## Exception Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│ main.py:process_problem() - Line 99                            │
│ ┌───────────────────────────────────────────────────────────┐ │
│ │ try:                                                       │ │
│ │   Line 103: semantic_plan = generate_semantic_plan(...)   │ │
│ │             ↓                                              │ │
│ │   ┌─────────────────────────────────────────────────────┐  │ │
│ │   │ semantic/planner.py:generate_semantic_plan()       │  │ │
│ │   │                                                      │  │ │
│ │   │ Line 31: expand_problem(problem_text)               │  │ │
│ │   │ Line 43-53: LLM API call                            │  │ │
│ │   │ Line 60: extract_json_from_text(raw_output)        │  │ │
│ │   │ Line 69-70: Check for "not_expressible" error       │  │ │
│ │   │   if parsed.get("error") == "not_expressible":      │  │ │
│ │   │       return parsed  ← Returns {"error": "not_expressible"} │
│ │   └─────────────────────────────────────────────────────┘  │ │
│ │             ↓                                              │ │
│ │   Line 105-107: Check for error                            │ │
│ │   if semantic_plan.get("error"):                          │ │
│ │       raise RuntimeError(f"Semantic error: {semantic_plan['error']}") │
│ │       ❌ EXCEPTION #1: RuntimeError("Semantic error: not_expressible") │
│ │                                                             │ │
│ └───────────────────────────────────────────────────────────┘ │
│             ↓                                                  │
│   Line 169: except Exception as e:  ← Catches Exception #1     │
│   Line 170: print(f"❌ Strict pipeline failed...")            │
│   Line 172: run_fallback(problem_dir, team_id, pid, description) │
│             ↓                                                  │
│   ┌─────────────────────────────────────────────────────────┐ │
│   │ main.py:run_fallback() - Line 57                       │ │
│   │                                                          │ │
│   │ Line 60: xml, python_code = generate_fallback_outputs(...) │
│   │          ↓                                               │ │
│   │   ┌───────────────────────────────────────────────────┐  │ │
│   │   │ fallback_llm/llm_xml_generator.py                │  │ │
│   │   │ generate_fallback_outputs(problem_text)           │  │ │
│   │   │                                                    │  │ │
│   │   │ Line 66-74: LLM API call                           │  │ │
│   │   │ Line 76: raw = response.choices[0].message.content │ │
│   │   │ Line 97: data = extract_json_from_text(raw)        │  │ │
│   │   │ Line 99-100: xml = data.get("xml"), py = data.get("python") │
│   │   │                                                    │  │ │
│   │   │ OR (if JSON extraction fails):                     │  │ │
│   │   │ Line 113: xml, py = separate_xml_and_python(raw)   │  │ │
│   │   │                                                    │  │ │
│   │   │ OR (last resort):                                  │  │ │
│   │   │ Line 120-125: return ("<xml></xml>", raw)         │  │ │
│   │   │          ↑                                         │  │ │
│   │   │          │ May contain Unicode characters!         │  │ │
│   │   └───────────────────────────────────────────────────┘  │ │
│   │          ↓                                               │ │
│   │   Line 67: py_dst.write_text(python_code)               │ │
│   │            ❌ EXCEPTION #2: UnicodeEncodeError          │ │
│   │            (if python_code contains Unicode chars)      │ │
│   └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

---

## Detailed Exception Locations

### Exception #1: `RuntimeError: Semantic error: not_expressible`

**Location**: `main.py:107`

**Root Cause**: 
- The LLM in `semantic/planner.py` determines the problem cannot be expressed using the limited semantic constructs
- The LLM returns `{"error": "not_expressible"}` as instructed in `semantic/prompt.py:68`
- This is a **legitimate failure** that triggers the fallback

**Code Path**:
1. `semantic/planner.py:69-70` - Checks for `not_expressible` and passes it through
2. `main.py:105-107` - Detects error and raises `RuntimeError`

**This is EXPECTED behavior** - it means the problem is too complex for the semantic planner.

---

### Exception #2: `UnicodeEncodeError: 'charmap' codec can't encode characters`

**Location**: `main.py:67` (in `run_fallback()`)

**Root Cause**:
- The fallback LLM (`generate_fallback_outputs()`) may return Python code containing Unicode characters
- `write_text()` on Windows defaults to `cp1252` encoding which can't handle all Unicode
- **FIXED**: Now uses `encoding='utf-8'` ✅

**Potential Unicode Sources**:
1. `fallback_llm/llm_xml_generator.py:124` - Returns raw LLM output which may contain Unicode
2. LLM-generated code may include Unicode characters in strings/comments
3. Special characters in problem descriptions

---

## Why Both Exceptions Occur Together

1. **First Exception** is **intentional** - it signals that the semantic planner cannot express the problem
2. **Second Exception** is a **bug** - it occurs when trying to write the fallback output
3. The second exception **masks** the first one, making debugging harder

---

## Files Involved

### Where "not_expressible" is Generated:
- **`semantic/prompt.py:65-68`** - Instructions to LLM to return `{"error": "not_expressible"}`
- **`semantic/planner.py:69-70`** - Passes through `not_expressible` errors

### Where "not_expressible" is Handled:
- **`main.py:105-107`** - Checks for error and raises `RuntimeError`
- **`main.py:169-172`** - Catches exception and calls `run_fallback()`

### Where Unicode Error Occurs:
- **`main.py:67`** - `py_dst.write_text(python_code)` ← **FIXED** ✅
- **`fallback_llm/llm_xml_generator.py:120-125`** - May return raw Unicode text

---

## Solutions Applied

### ✅ Fixed: Unicode Encoding
- All `write_text()` calls now use `encoding='utf-8'`
- All `read_text()` calls now use `encoding='utf-8'`
- Files fixed:
  - `main.py` (4 locations)
  - `semantic/validator.py` (1 location)
  - `fallback_llm/fallback_writer.py` (2 locations)
  - `run_test.py` (1 location)

### 🔍 Recommendation: Better Error Handling
Consider wrapping `run_fallback()` in a try-except to handle encoding errors gracefully:

```python
def run_fallback(problem_dir: Path, team_id: str, pid: str, description: str):
    try:
        # ... existing code ...
    except UnicodeEncodeError as e:
        # Fallback to ASCII-safe version
        python_code_safe = python_code.encode('ascii', 'replace').decode('ascii')
        py_dst.write_text(python_code_safe, encoding='utf-8')
        # Log the error
        print(f"⚠️ Unicode characters replaced in fallback output for {pid}")
```

---

## Summary

- **Exception #1** (`not_expressible`) is **expected** and triggers fallback ✅
- **Exception #2** (`UnicodeEncodeError`) was a **bug** and is now **fixed** ✅
- The fallback should now work correctly even with Unicode characters in LLM output

