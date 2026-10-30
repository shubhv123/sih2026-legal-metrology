# CLAUDE.md — Repository Context & Migration Guardrails

## Active Dependency Standards
- **numpy**: `2.5.4` (Upgraded from `1.26.4` via DriftZero)
- **Verification Suite**: `pytest test_migration_parity.py -v`

## Strict Coding Rules for AI Agents
### np.array
- **FORBIDDEN (Legacy 1.26.4):** `np.array([1, 2, 3])`
- **REQUIRED (Target 2.5.4):** `np.array([1, 2, 3], copy=True)`
- **Required Imports:** `from numpy import array`
- **Silent Semantic Drift Warning:** In NumPy 2.0, the copy parameter was added; default copy=None may avoid copying, potentially leading to shared memory with input.
- **Verified Source:** https://numpy.org/devdocs/numpy_2_0_migration_guide.html

### np.count_nonzero
- **FORBIDDEN (Legacy 1.26.4):** `np.count_nonzero(arr)`
- **REQUIRED (Target 2.5.4):** `np.count_nonzero(arr)`
- **Required Imports:** `from numpy import count_nonzero`
- **Silent Semantic Drift Warning:** Return value is now a plain Python int instead of a NumPy scalar, which may affect downstream code expecting a NumPy type.
- **Verified Source:** https://numpy.org/devdocs/numpy_2_0_migration_guide.html

### np.frombuffer
- **FORBIDDEN (Legacy 1.26.4):** `np.frombuffer(b'\x01\x02\x03', dtype=np.uint8)`
- **REQUIRED (Target 2.5.4):** `np.frombuffer(b'\x01\x02\x03', dtype=np.uint8, count=-1, offset=0)`
- **Required Imports:** `from numpy import frombuffer`
- **Silent Semantic Drift Warning:** The default values for count and offset are now explicitly set; relying on defaults may raise FutureWarning if omitted in future versions.
- **Verified Source:** https://numpy.org/devdocs/numpy_2_0_migration_guide.html

### np.full
- **FORBIDDEN (Legacy 1.26.4):** `np.full((2,2), 5)`
- **REQUIRED (Target 2.5.4):** `np.full((2,2), 5, dtype=None, order='C')`
- **Required Imports:** `from numpy import full`
- **Silent Semantic Drift Warning:** Explicit dtype and order parameters are now recommended; relying on defaults may lead to unexpected dtype promotion in future releases.
- **Verified Source:** https://numpy.org/devdocs/numpy_2_0_migration_guide.html

### np.mean
- **FORBIDDEN (Legacy 1.26.4):** `np.mean([1,2,3])`
- **REQUIRED (Target 2.5.4):** `np.mean([1,2,3], dtype=np.float64)`
- **Required Imports:** `from numpy import mean`
- **Silent Semantic Drift Warning:** Default dtype for integer inputs is now float64; previously it depended on accumulator precision, which could cause subtle differences in mixed-type arrays.
- **Verified Source:** https://numpy.org/devdocs/numpy_2_0_migration_guide.html

### np.linalg.norm
- **FORBIDDEN (Legacy 1.26.4):** `np.linalg.norm([3,4])`
- **REQUIRED (Target 2.5.4):** `np.linalg.norm([3,4], ord=None, axis=None, keepdims=False)`
- **Required Imports:** `import numpy as np`
- **Silent Semantic Drift Warning:** The ord parameter default changed from None to 'fro' for matrices; for 1-D arrays, behavior unchanged but explicit specification recommended.
- **Verified Source:** https://numpy.org/devdocs/numpy_2_0_migration_guide.html


## Sandbox Quality Assurance
- Autonomous self-healing patched `backend/tests/sample_images/generate_sample_labels.py, backend/app/main.py, backend/app/schemas/__init__.py, backend/app/routers/__init__.py, backend/app/core/security.py, backend/app/services/reporting/__init__.py, backend/app/services/vision/__init__.py, backend/app/services/compliance/__init__.py, backend/app/db/__init__.py` to eliminate silent semantic drift. Always verify default arguments, validation lifecycles, and keyword arguments in numpy 2.5.4.
- Autonomous self-healing patched `backend/tests/sample_images/generate_sample_labels.py, backend/app/main.py, backend/app/schemas/auth.py, backend/app/schemas/__init__.py, backend/app/routers/auth.py, backend/app/routers/__init__.py, backend/app/core/security.py, backend/app/services/vision/preprocessing.py, backend/app/services/vision/__init__.py, backend/app/db/base.py, backend/app/db/__init__.py` to eliminate silent semantic drift. Always verify default arguments, validation lifecycles, and keyword arguments in numpy 2.5.4.
