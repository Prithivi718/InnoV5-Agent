# Exception Locations - Quick Reference

## Two Exceptions That Cause Fallback Failure

### 🔴 Exception #1: `RuntimeError: Semantic error: not_expressible`

**File**: `main.py`  
**Line**: 107  
**Function**: `process_problem()`

```python
# Line 103: Semantic planner returns {"error": "not_expressible"}
semantic_plan = generate_semantic_plan(description)

# Line 105-107: Check and raise error
if semantic_plan.get("error"):
    show_notification(f"Semantic Error", f"{semantic_plan['error']}")
    raise RuntimeError(f"Semantic error: {semantic_plan['error']}")  # ← EXCEPTION #1
```

**Root Cause Location**: `semantic/planner.py:69-70`
```python
# Explicit not_expressible passthrough
if isinstance(parsed, dict) and parsed.get("error") == "not_expressible":
    return parsed  # ← Returns {"error": "not_expressible"}
```

**Why it happens**: 
- LLM determines problem cannot be expressed with limited semantic constructs
- Instructed to return `{"error": "not_expressible"}` in `semantic/prompt.py:68`
- **This is EXPECTED** - triggers fallback pipeline

---

### 🔴 Exception #2: `UnicodeEncodeError: 'charmap' codec can't encode characters`

**File**: `main.py`  
**Line**: 67 (in `run_fallback()`)  
**Function**: `run_fallback()`

```python
# Line 60: Get fallback output (may contain Unicode)
xml, python_code = generate_fallback_outputs(description)

# Line 67: Write to file (was failing here)
py_dst.write_text(python_code, encoding='utf-8')  # ← EXCEPTION #2 (FIXED ✅)
```

**Root Cause Location**: `fallback_llm/llm_xml_generator.py:120-125`
```python
# Last resort: dump raw text (may contain Unicode)
return (
    "<xml></xml>",
    "# Fallback JSON extraction failed\n"
    "# Raw LLM output below:\n\n"
    + raw  # ← May contain Unicode characters
)
```

**Why it happened**: 
- Windows default encoding (cp1252) can't handle all Unicode
- LLM output may contain Unicode characters
- **FIXED**: Now uses `encoding='utf-8'` ✅

---

## Exception Flow Sequence

```
1. main.py:103 → semantic/planner.py:generate_semantic_plan()
   ↓
2. LLM returns {"error": "not_expressible"}
   ↓
3. semantic/planner.py:69-70 → Returns error dict
   ↓
4. main.py:105-107 → Raises RuntimeError("Semantic error: not_expressible")
   ↓
5. main.py:169 → Catches exception
   ↓
6. main.py:172 → Calls run_fallback()
   ↓
7. main.py:60 → generate_fallback_outputs() (may return Unicode)
   ↓
8. main.py:67 → write_text() (was failing, now FIXED ✅)
```

---

## Files Modified to Fix Issues

### ✅ Fixed Unicode Encoding:
- `main.py` - Lines 48, 66-68, 130, 162-164
- `semantic/validator.py` - Line 23
- `fallback_llm/fallback_writer.py` - Lines 15-16
- `run_test.py` - Line 31

### ✅ Added Error Handling:
- `main.py:run_fallback()` - Added try-except for UnicodeEncodeError
- Now gracefully handles encoding issues

---

## Current Status

- ✅ **Exception #1** is **intentional** - triggers fallback correctly
- ✅ **Exception #2** is **FIXED** - UTF-8 encoding now used everywhere
- ✅ **Additional safety** - Error handling added for edge cases

The fallback pipeline should now work correctly even with Unicode characters in LLM output.

