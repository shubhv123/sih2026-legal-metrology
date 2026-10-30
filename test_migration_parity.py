# Auto-generated Differential Parity Test Suite by DriftZero
# Target Library: numpy (2.5.4)
import os
import sys
import json
import pytest
from pathlib import Path
from decimal import Decimal
from datetime import datetime, date

# Ensure workspace root and src directory are on sys.path
_repo_root = Path(__file__).resolve().parent
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))
_src_dir = _repo_root / "src"
if _src_dir.exists() and str(_src_dir) not in sys.path:
    sys.path.insert(0, str(_src_dir))

# Compatibility fix for Python 3.14+ PEP 649 deferred annotations with legacy Pydantic v1
try:
    import pydantic.main
    if hasattr(pydantic.main, "ModelMetaclass"):
        _orig_model_meta_new = pydantic.main.ModelMetaclass.__new__
        def _compat_model_meta_new(mcs, name, bases, namespace, **kwargs):
            if "__annotate_func__" in namespace and not namespace.get("__annotations__"):
                try:
                    namespace["__annotations__"] = namespace["__annotate_func__"](1)
                except Exception:
                    pass
            return _orig_model_meta_new(mcs, name, bases, namespace, **kwargs)
        pydantic.main.ModelMetaclass.__new__ = _compat_model_meta_new
except Exception:
    pass

GOLDEN_FILE = Path(__file__).resolve().parent / "golden.json"
IS_RECORDING = os.getenv("DRIFTZERO_RECORD_GOLDEN", "0") == "1"

# Module-level golden store
_golden_store: dict = {}

def _load_golden() -> dict:
    global _golden_store
    if _golden_store:
        return _golden_store
    if not GOLDEN_FILE.exists():
        if not IS_RECORDING:
            raise AssertionError(
                f"Golden baseline file '{GOLDEN_FILE}' not found! "
                "The old-version container must run with DRIFTZERO_RECORD_GOLDEN=1 first "
                "to record golden baseline outputs before running differential verification."
            )
        return _golden_store
    try:
        _golden_store.clear()
        _golden_store.update(json.loads(GOLDEN_FILE.read_text(encoding="utf-8")))
        return _golden_store
    except Exception as exc:
        raise AssertionError(f"Failed to read golden baseline file: {exc}")

def _save_golden():
    global _golden_store
    GOLDEN_FILE.write_text(json.dumps(_golden_store, indent=2, default=str), encoding="utf-8")


def _generate_sample_input_for_field(field_name: str, type_annotation: str = ""):
    name = field_name.lower()
    t_clean = type_annotation.lower().strip()

    if name == "postal_code":
        return "94105"
    if "email" in name:
        return "dev@example.com"
    if name in ("sender_country", "receiver_country", "country"):
        return "US"
    if name in ("amount", "amount_usd", "price", "rate", "fee", "balance", "cost", "fx_rate"):
        return 100.0
    if name in ("quantity", "count", "limit", "retries", "max_retries", "timeout_seconds", "attempt_count", "unit_price_cents", "qty"):
        return 5
    if name in ("created_at", "updated_at", "timestamp", "date"):
        return "2025-01-01T12:00:00"
    if name in ("is_", "has_", "active", "enabled", "requires_manual_compliance_review"):
        return False
    if name in ("tags", "list", "categories"):
        return ["item_1", "item_2"]
    if name in ("payload", "data", "meta", "metadata", "config", "data_object", "payload_snapshot"):
        return {"status": "ok", "env": "test"}
    if name == "street":
        return "123 Market St"
    if name == "city":
        return "San Francisco"
    if name == "sku":
        return "SKU-TEST-001"
    if name.endswith("_id") or name == "id" or name in ("order_id", "customer_id", "transaction_id", "trace_id", "actor_id", "event_id"):
        return f"test_{field_name}_123"
    if name == "primary_address":
        return {"street": "123 Market St", "city": "San Francisco", "postal_code": "94105"}
    if name == "items":
        return [{"sku": "SKU-001", "quantity": 2, "unit_price_cents": 500}]
    if name == "order":
        return {"order_id": "test_order_123", "created_at": "2025-01-01T12:00:00", "items": [{"sku": "SKU-1", "quantity": 1, "unit_price_cents": 100}]}
    if name == "raw_dict":
        return {"order_id": "test_order_123", "created_at": "2025-01-01T12:00:00", "items": [{"sku": "SKU-1", "quantity": 1, "unit_price_cents": 100}]}
    if name == "raw_json":
        return json.dumps({"order_id": "test_order_123", "created_at": "2025-01-01T12:00:00", "items": [{"sku": "SKU-1", "quantity": 1, "unit_price_cents": 100}]})
    if name == "raw_list" or ("list" in t_clean and "dict" in t_clean):
        return [{"trace_id": "test_trace_123", "attempt_count": 1, "payload": {"status": "ok"}, "scores": [0.2, 0.5, 0.8]}]
    if name == "prompt":
        return {"system_instruction": "Summarize", "user_transcript": "User dialog", "temperature": 0.5}
    if name in ("scores", "__root__", "root"):
        return [0.2, 0.5, 0.8]

    if "int" in t_clean and "list" not in t_clean:
        return 5
    if "float" in t_clean and "list" not in t_clean:
        return 10.5
    if "bool" in t_clean:
        return True
    if "list" in t_clean:
        if "float" in t_clean:
            return [0.2, 0.5, 0.8]
        if "int" in t_clean:
            return [1, 2, 3]
        return ["item_1", "item_2"]
    if "dict" in t_clean:
        return {"key": "value"}
    if "datetime" in t_clean or "date" in t_clean:
        return "2025-01-01T12:00:00"

    return f"sample_{field_name}"


def _build_model_sample_inputs(cls_obj, fallback=None):
    """
    Builds sample inputs at test runtime from the model's own fields
    (model_fields in Pydantic v2 or __fields__ in Pydantic v1, including all inherited ones).
    """
    fields_dict = getattr(cls_obj, "model_fields", None)
    if fields_dict is None:
        fields_dict = getattr(cls_obj, "__fields__", None)

    if not isinstance(fields_dict, dict):
        return dict(fallback or {})

    kwargs = dict(fallback or {})
    for f_name, f_info in fields_dict.items():
        type_str = ""
        if hasattr(f_info, "annotation") and f_info.annotation is not None:
            type_str = getattr(f_info.annotation, "__name__", str(f_info.annotation))
        elif hasattr(f_info, "type_") and f_info.type_ is not None:
            type_str = getattr(f_info.type_, "__name__", str(f_info.type_))
        elif hasattr(f_info, "outer_type_") and f_info.outer_type_ is not None:
            type_str = getattr(f_info.outer_type_, "__name__", str(f_info.outer_type_))

        if f_name not in kwargs or kwargs[f_name] is None:
            kwargs[f_name] = _generate_sample_input_for_field(f_name, type_str)
        elif kwargs[f_name] == f"sample_{f_name}" and type_str:
            kwargs[f_name] = _generate_sample_input_for_field(f_name, type_str)

    return kwargs


def _serialize_value(val, mode="json"):
    """
    Serializes models and Python values across legacy and modern library versions.
    Normalizes both sides through mode='json' (converts Decimals, datetimes, Enums, sets to JSON-safe types).
    """
    if val is None:
        return None

    if hasattr(val, "value"):
        return _serialize_value(val.value, mode=mode)

    # Modern Pydantic v2 / dataclasses with model_dump
    if hasattr(val, "model_dump") and callable(getattr(val, "model_dump")):
        if mode == "json":
            try:
                dumped = val.model_dump(mode="json")
                return _serialize_value(dumped, mode=mode)
            except Exception:
                try:
                    return json.loads(json.dumps(val.model_dump(), default=str))
                except Exception:
                    pass
        return val.model_dump()

    # Legacy Pydantic v1 / objects with dict()
    if hasattr(val, "dict") and callable(getattr(val, "dict")):
        if mode == "json":
            if hasattr(val, "json") and callable(getattr(val, "json")):
                try:
                    return json.loads(val.json())
                except Exception:
                    pass
            try:
                return json.loads(json.dumps(val.dict(), default=str))
            except Exception:
                pass
        return val.dict()

    if isinstance(val, str):
        s_val = val.strip()
        if (s_val.startswith("{") and s_val.endswith("}")) or (s_val.startswith("[") and s_val.endswith("]")):
            try:
                parsed_json = json.loads(s_val)
                return _serialize_value(parsed_json, mode=mode)
            except Exception:
                pass
        return val.replace("#/$defs/", "#/definitions/")

    if isinstance(val, (int, float, bool)):
        return val
    if isinstance(val, (list, tuple)):
        return [_serialize_value(item, mode=mode) for item in val]
    if isinstance(val, (set, frozenset)):
        serialized_items = [_serialize_value(item, mode=mode) for item in val]
        return sorted(serialized_items, key=lambda x: json.dumps(x, default=str) if isinstance(x, (dict, list)) else str(x))
    if isinstance(val, dict):
        norm_dict = {}
        for k, v in val.items():
            str_k = str(k)
            if str_k in ("$defs", "definitions"):
                str_k = "definitions"
            norm_dict[str_k] = _serialize_value(v, mode=mode)
        return norm_dict
    if isinstance(val, Decimal):
        return str(val) if mode == "json" else float(val)
    if isinstance(val, (datetime, date)):
        return val.isoformat()

    return str(val)


def _is_base_settings_subclass(cls_obj):
    try:
        if isinstance(cls_obj, type) and cls_obj.__name__ != "BaseSettings":
            return any(base.__name__ == "BaseSettings" for base in cls_obj.__mro__)
    except Exception:
        pass
    return False


def _get_field_env_vars_to_set(cls_obj, sample_kwargs):
    env_vars = {}
    env_prefix = ""
    model_config = getattr(cls_obj, "model_config", None)
    if isinstance(model_config, dict):
        env_prefix = model_config.get("env_prefix", "") or ""
    elif hasattr(model_config, "env_prefix"):
        env_prefix = getattr(model_config, "env_prefix", "") or ""

    if not env_prefix:
        cfg = getattr(cls_obj, "Config", None)
        if cfg and hasattr(cfg, "env_prefix"):
            env_prefix = getattr(cfg, "env_prefix", "") or ""

    fields_dict = getattr(cls_obj, "model_fields", None)
    if fields_dict is None:
        fields_dict = getattr(cls_obj, "__fields__", None)
    if not isinstance(fields_dict, dict):
        fields_dict = {k: None for k in sample_kwargs}

    for f_name, val in (sample_kwargs or {}).items():
        f_info = fields_dict.get(f_name)
        var_name = ""

        if f_info is not None:
            extra = getattr(getattr(f_info, "field_info", None), "extra", {})
            env_val = getattr(f_info, "env", None)
            if isinstance(extra, dict) and extra.get("env"):
                var_name = extra["env"]
            elif isinstance(env_val, str) and env_val:
                var_name = env_val
            elif getattr(getattr(f_info, "field_info", None), "env", None):
                var_name = getattr(f_info.field_info, "env")

            if not var_name:
                v_alias = getattr(f_info, "validation_alias", None)
                if isinstance(v_alias, str) and v_alias:
                    var_name = v_alias
                elif getattr(f_info, "has_alias", False) and isinstance(getattr(f_info, "alias", None), str):
                    var_name = f_info.alias

        if not var_name:
            var_name = f"{env_prefix}{f_name}".upper()

        if hasattr(val, "value"):
            val = val.value

        if isinstance(val, bool):
            str_val = "true" if val else "false"
        elif isinstance(val, (dict, list)):
            str_val = json.dumps(val)
        elif isinstance(val, (datetime, date)):
            str_val = val.isoformat()
        else:
            str_val = str(val)

        env_vars[var_name] = str_val
        env_vars[f"{env_prefix}{f_name}".upper()] = str_val

    return env_vars


def verify_base_settings_env_differential(mod_name: str, cls_name: str, cls_obj, sample_kwargs: dict = None):
    """
    Differential parity assertion for BaseSettings subclasses:
    Sets each field's environment variable, instantiates the model with no arguments,
    and records/verifies the resulting instance against golden.json.
    Restores original environment variables afterward.
    """
    global _golden_store
    golden_key = f"settings_env::{mod_name}.{cls_name}"

    final_kwargs = _build_model_sample_inputs(cls_obj, fallback=sample_kwargs)
    env_vars = _get_field_env_vars_to_set(cls_obj, final_kwargs)

    saved_env = {}
    keys_to_clean = []
    try:
        for k, v in env_vars.items():
            if k in os.environ:
                saved_env[k] = os.environ[k]
            else:
                keys_to_clean.append(k)
            os.environ[k] = v

        if IS_RECORDING:
            record = {}
            try:
                try:
                    instance = cls_obj(_env_file=None)
                except (TypeError, ValueError):
                    instance = cls_obj()
                record["status"] = "ok"
                record["output"] = _serialize_value(instance, mode="json")
            except Exception as exc:
                record["status"] = "error"
                record["error_type"] = type(exc).__name__

            _load_golden()
            _golden_store[golden_key] = record
            _save_golden()
            return

        golden = _load_golden()
        if golden_key not in golden:
            raise AssertionError(
                f"Missing golden baseline entry for BaseSettings '{mod_name}.{cls_name}'. "
                "Old-version container must record golden.json before verification."
            )

        expected = golden[golden_key]
        if expected["status"] == "ok":
            try:
                instance = cls_obj(_env_file=None)
            except (TypeError, ValueError):
                instance = cls_obj()
            actual_norm = _serialize_value(instance, mode="json")
            expected_norm = _serialize_value(expected["output"], mode="json")
            assert actual_norm == expected_norm, (
                f"Differential BaseSettings Parity Mismatch for '{cls_name}' when loaded from env vars:\n"
                f"Expected (Golden): {expected_norm}\n"
                f"Actual   (New):    {actual_norm}"
            )
        else:
            with pytest.raises(Exception) as exc_info:
                cls_obj()
            actual_type = exc_info.value.__class__.__name__
            expected_type = expected["error_type"]
            assert actual_type == expected_type, (
                f"Error type mismatch for BaseSettings '{cls_name}' loaded from env vars: "
                f"expected {expected_type}, got {actual_type}"
            )
    finally:
        for k in keys_to_clean:
            os.environ.pop(k, None)
        for k, v in saved_env.items():
            os.environ[k] = v


def verify_model_differential(mod_name: str, cls_name: str, cls_obj, sample_kwargs: dict = None):
    """
    Differential parity assertion for models:
    - Builds inputs at test runtime from model_fields or __fields__, including inherited ones.
    - Normalizes both sides through _serialize_value(mode="json") before comparing.
    - Compares error type only, not message.
    - For BaseSettings subclasses, runs environment variable check.
    """
    global _golden_store
    golden_key = f"model::{mod_name}.{cls_name}"

    runtime_inputs = _build_model_sample_inputs(cls_obj, fallback=sample_kwargs)
    final_kwargs = runtime_inputs if runtime_inputs else dict(sample_kwargs or {})

    if IS_RECORDING:
        record = {}
        try:
            instance = cls_obj(**final_kwargs)
            record["status"] = "ok"
            record["output"] = _serialize_value(instance, mode="json")
            record["model_dump"] = record["output"]
            record["model_dump_json"] = record["output"]
        except Exception as exc:
            record["status"] = "error"
            record["error_type"] = type(exc).__name__

        # Record error type on invalid / empty inputs
        try:
            cls_obj()
            record["empty_input_status"] = "ok"
        except Exception as exc:
            record["empty_input_status"] = "error"
            record["invalid_error_type"] = type(exc).__name__

        _load_golden()
        _golden_store[golden_key] = record
        _save_golden()

        # Runtime check for BaseSettings subclasses: set each field's env var and compare against golden
        if _is_base_settings_subclass(cls_obj):
            verify_base_settings_env_differential(mod_name, cls_name, cls_obj, sample_kwargs=final_kwargs)
        return

    # Verification Mode (New Container)
    golden = _load_golden()
    if golden_key not in golden:
        raise AssertionError(
            f"Missing golden baseline entry for model '{mod_name}.{cls_name}'. "
            "Old-version container must record golden.json before verification."
        )

    expected = golden[golden_key]

    if expected["status"] == "ok":
        instance = cls_obj(**final_kwargs)

        # Normalize both sides through _serialize_value(mode="json") before comparing
        actual_norm = _serialize_value(instance, mode="json")
        expected_norm = _serialize_value(
            expected.get("output") or expected.get("model_dump_json") or expected.get("model_dump"),
            mode="json"
        )
        assert actual_norm == expected_norm, (
            f"Differential Model Parity Mismatch for '{cls_name}':\n"
            f"Expected (Golden): {expected_norm}\n"
            f"Actual   (New):    {actual_norm}"
        )
    else:
        # Expected error on instantiation: compare error type only, not message
        with pytest.raises(Exception) as exc_info:
            cls_obj(**final_kwargs)
        actual_type = exc_info.value.__class__.__name__
        expected_type = expected["error_type"]
        assert actual_type == expected_type, (
            f"Error type mismatch for '{cls_name}': expected {expected_type}, got {actual_type}"
        )

    # Assert error type on invalid / empty inputs: compare error type only, not message
    if expected.get("empty_input_status") == "error":
        with pytest.raises(Exception) as exc_info:
            cls_obj()
        actual_type = exc_info.value.__class__.__name__
        expected_type = expected["invalid_error_type"]
        assert actual_type == expected_type, (
            f"Validation error type mismatch for invalid inputs on '{cls_name}': "
            f"expected {expected_type}, got {actual_type}"
        )

    # Runtime check for BaseSettings subclasses: set each field's env var and compare against golden
    if _is_base_settings_subclass(cls_obj):
        verify_base_settings_env_differential(mod_name, cls_name, cls_obj, sample_kwargs=final_kwargs)


def verify_function_differential(mod_name: str, fn_name: str, fn_obj, sample_kwargs: dict = None):
    """
    Differential parity assertion for functions:
    - Normalizes both sides through _serialize_value(mode="json") before comparing.
    - Compares error type only, not message.
    """
    global _golden_store
    golden_key = f"func::{mod_name}.{fn_name}"
    final_kwargs = dict(sample_kwargs or {})

    if IS_RECORDING:
        record = {}
        try:
            res = fn_obj(**final_kwargs)
            record["status"] = "ok"
            record["output"] = _serialize_value(res, mode="json")
        except Exception as exc:
            record["status"] = "error"
            record["error_type"] = type(exc).__name__

        _load_golden()
        _golden_store[golden_key] = record
        _save_golden()
        return

    # Verification Mode (New Container)
    golden = _load_golden()
    if golden_key not in golden:
        raise AssertionError(
            f"Missing golden baseline entry for function '{mod_name}.{fn_name}'. "
            "Old-version container must record golden.json before verification."
        )

    expected = golden[golden_key]

    if expected["status"] == "ok":
        res = fn_obj(**final_kwargs)
        actual_norm = _serialize_value(res, mode="json")
        expected_norm = _serialize_value(expected["output"], mode="json")
        assert actual_norm == expected_norm, (
            f"Differential Function Parity Mismatch for '{fn_name}':\n"
            f"Expected (Golden): {expected_norm}\n"
            f"Actual   (New):    {actual_norm}"
        )
    else:
        # Expected error on function execution: compare error type only, not message
        with pytest.raises(Exception) as exc_info:
            fn_obj(**final_kwargs)
        actual_type = exc_info.value.__class__.__name__
        expected_type = expected["error_type"]
        assert actual_type == expected_type, (
            f"Function error type mismatch for '{fn_name}': expected {expected_type}, got {actual_type}"
        )


def test_differential_parity_0_backend_tests_sample_images_generate_sample_labels():
    # Direct import: fails loudly with ImportError if the symbol was renamed or deleted
    from backend.tests.sample_images.generate_sample_labels import create_sample_labels

    # Differential Parity Test for Function: backend.tests.sample_images.generate_sample_labels.create_sample_labels
    sample_kwargs = {}
    verify_function_differential("backend.tests.sample_images.generate_sample_labels", "create_sample_labels", create_sample_labels, sample_kwargs)



def test_differential_parity_1_backend_app_main():
    # Direct import: fails loudly with ImportError if the symbol was renamed or deleted
    from backend.app.main import lifespan, root, health, health_v1, global_exception_handler

    # Differential Parity Test for Function: backend.app.main.lifespan
    sample_kwargs = {'app': 'sample_app'}
    verify_function_differential("backend.app.main", "lifespan", lifespan, sample_kwargs)

    # Differential Parity Test for Function: backend.app.main.root
    sample_kwargs = {}
    verify_function_differential("backend.app.main", "root", root, sample_kwargs)

    # Differential Parity Test for Function: backend.app.main.health
    sample_kwargs = {}
    verify_function_differential("backend.app.main", "health", health, sample_kwargs)

    # Differential Parity Test for Function: backend.app.main.health_v1
    sample_kwargs = {}
    verify_function_differential("backend.app.main", "health_v1", health_v1, sample_kwargs)

    # Differential Parity Test for Function: backend.app.main.global_exception_handler
    sample_kwargs = {'request': 'sample_request', 'exc': 'sample_exc'}
    verify_function_differential("backend.app.main", "global_exception_handler", global_exception_handler, sample_kwargs)



def test_differential_parity_2_backend_app_schemas_auth():
    # Direct import: fails loudly with ImportError if the symbol was renamed or deleted
    from backend.app.schemas.auth import LoginRequest, TokenResponse, UserResponse

    # Differential Parity Test for Model: backend.app.schemas.auth.LoginRequest
    sample_kwargs = _build_model_sample_inputs(LoginRequest, fallback={'username': 'sample_username', 'password': 'sample_password'})
    verify_model_differential("backend.app.schemas.auth", "LoginRequest", LoginRequest, sample_kwargs)

    # Differential Parity Test for Model: backend.app.schemas.auth.TokenResponse
    sample_kwargs = _build_model_sample_inputs(TokenResponse, fallback={'access_token': 'sample_access_token', 'token_type': 'sample_token_type', 'role': 'sample_role', 'username': 'sample_username', 'full_name': 'sample_full_name'})
    verify_model_differential("backend.app.schemas.auth", "TokenResponse", TokenResponse, sample_kwargs)

    # Differential Parity Test for Model: backend.app.schemas.auth.UserResponse
    sample_kwargs = _build_model_sample_inputs(UserResponse, fallback={'id': 'test_id_123', 'username': 'sample_username', 'role': 'sample_role', 'full_name': 'sample_full_name', 'created_at': '2025-01-01T12:00:00'})
    verify_model_differential("backend.app.schemas.auth", "UserResponse", UserResponse, sample_kwargs)



def test_differential_parity_3_backend_app_schemas_compliance():
    # Direct import: fails loudly with ImportError if the symbol was renamed or deleted
    from backend.app.schemas.compliance import ExtractedField, ComplianceResultSchema

    # Differential Parity Test for Model: backend.app.schemas.compliance.ExtractedField
    sample_kwargs = _build_model_sample_inputs(ExtractedField, fallback={'field_name': 'sample_field_name', 'raw_text': 'sample_raw_text', 'normalized_value': 'sample_normalized_value', 'unit': 'sample_unit', 'confidence': 10.5, 'bounding_box': [1, 2, 3]})
    verify_model_differential("backend.app.schemas.compliance", "ExtractedField", ExtractedField, sample_kwargs)

    # Differential Parity Test for Model: backend.app.schemas.compliance.ComplianceResultSchema
    sample_kwargs = _build_model_sample_inputs(ComplianceResultSchema, fallback={'rule_id': 'test_rule_id_123', 'rule_name': 'sample_rule_name', 'field_name': 'sample_field_name', 'status': 'sample_status', 'confidence': 10.5, 'measured_value': 'sample_measured_value', 'expected_value': 'sample_expected_value', 'violation_reason': 'sample_violation_reason', 'rule_version': 'sample_rule_version'})
    verify_model_differential("backend.app.schemas.compliance", "ComplianceResultSchema", ComplianceResultSchema, sample_kwargs)



def test_differential_parity_4_backend_app_schemas_dashboard():
    # Direct import: fails loudly with ImportError if the symbol was renamed or deleted
    from backend.app.schemas.dashboard import CommonViolationItem, RecentActivityItem, DashboardStatsResponse

    # Differential Parity Test for Model: backend.app.schemas.dashboard.CommonViolationItem
    sample_kwargs = _build_model_sample_inputs(CommonViolationItem, fallback={'rule_id': 'test_rule_id_123', 'label': 'sample_label', 'count': 5})
    verify_model_differential("backend.app.schemas.dashboard", "CommonViolationItem", CommonViolationItem, sample_kwargs)

    # Differential Parity Test for Model: backend.app.schemas.dashboard.RecentActivityItem
    sample_kwargs = _build_model_sample_inputs(RecentActivityItem, fallback={'scan_id': 'test_scan_id_123', 'product_name': 'sample_product_name', 'overall_status': 'sample_overall_status', 'created_at': '2025-01-01T12:00:00'})
    verify_model_differential("backend.app.schemas.dashboard", "RecentActivityItem", RecentActivityItem, sample_kwargs)

    # Differential Parity Test for Model: backend.app.schemas.dashboard.DashboardStatsResponse
    sample_kwargs = _build_model_sample_inputs(DashboardStatsResponse, fallback={'total_scans': 5, 'pass_count': 5, 'fail_count': 5, 'review_required_count': 5, 'compliance_rate_pct': 10.5, 'most_common_violations': ['item_1', 'item_2'], 'recent_activity': ['item_1', 'item_2']})
    verify_model_differential("backend.app.schemas.dashboard", "DashboardStatsResponse", DashboardStatsResponse, sample_kwargs)



def test_differential_parity_5_backend_app_schemas_enums():
    # Direct import: fails loudly with ImportError if the symbol was renamed or deleted
    from backend.app.schemas.enums import ComplianceStatus, RoleEnum, CalibrationMethod, ProductCategory

    # Differential Parity Test for Model: backend.app.schemas.enums.ComplianceStatus
    sample_kwargs = _build_model_sample_inputs(ComplianceStatus, fallback={})
    verify_model_differential("backend.app.schemas.enums", "ComplianceStatus", ComplianceStatus, sample_kwargs)

    # Differential Parity Test for Model: backend.app.schemas.enums.RoleEnum
    sample_kwargs = _build_model_sample_inputs(RoleEnum, fallback={})
    verify_model_differential("backend.app.schemas.enums", "RoleEnum", RoleEnum, sample_kwargs)

    # Differential Parity Test for Model: backend.app.schemas.enums.CalibrationMethod
    sample_kwargs = _build_model_sample_inputs(CalibrationMethod, fallback={})
    verify_model_differential("backend.app.schemas.enums", "CalibrationMethod", CalibrationMethod, sample_kwargs)

    # Differential Parity Test for Model: backend.app.schemas.enums.ProductCategory
    sample_kwargs = _build_model_sample_inputs(ProductCategory, fallback={})
    verify_model_differential("backend.app.schemas.enums", "ProductCategory", ProductCategory, sample_kwargs)



def test_differential_parity_6_backend_app_schemas_history():
    # Direct import: fails loudly with ImportError if the symbol was renamed or deleted
    from backend.app.schemas.history import PaginatedScansResponse

    # Differential Parity Test for Model: backend.app.schemas.history.PaginatedScansResponse
    sample_kwargs = _build_model_sample_inputs(PaginatedScansResponse, fallback={'total': 5, 'page': 5, 'page_size': 5, 'total_pages': 5, 'items': [{'sku': 'SKU-001', 'quantity': 2, 'unit_price_cents': 500}]})
    verify_model_differential("backend.app.schemas.history", "PaginatedScansResponse", PaginatedScansResponse, sample_kwargs)



def test_differential_parity_7_backend_app_schemas_product():
    # Direct import: fails loudly with ImportError if the symbol was renamed or deleted
    from backend.app.schemas.product import ProductBase, ProductCreate, ProductResponse

    # Differential Parity Test for Model: backend.app.schemas.product.ProductBase
    sample_kwargs = _build_model_sample_inputs(ProductBase, fallback={'product_name': 'sample_product_name', 'brand_name': 'sample_brand_name', 'category': 'sample_category', 'net_quantity_declared': 'sample_net_quantity_declared', 'mrp_declared': 10.5, 'country_of_origin': 'sample_country_of_origin', 'manufacturer_details': 'sample_manufacturer_details', 'mfg_date': 'sample_mfg_date', 'expiry_date': 'sample_expiry_date', 'consumer_care': 'sample_consumer_care'})
    verify_model_differential("backend.app.schemas.product", "ProductBase", ProductBase, sample_kwargs)

    # Differential Parity Test for Model: backend.app.schemas.product.ProductCreate
    sample_kwargs = _build_model_sample_inputs(ProductCreate, fallback={})
    verify_model_differential("backend.app.schemas.product", "ProductCreate", ProductCreate, sample_kwargs)

    # Differential Parity Test for Model: backend.app.schemas.product.ProductResponse
    sample_kwargs = _build_model_sample_inputs(ProductResponse, fallback={'id': 'test_id_123', 'created_at': '2025-01-01T12:00:00'})
    verify_model_differential("backend.app.schemas.product", "ProductResponse", ProductResponse, sample_kwargs)



def test_differential_parity_8_backend_app_schemas_scan():
    # Direct import: fails loudly with ImportError if the symbol was renamed or deleted
    from backend.app.schemas.scan import DetectionMethod, BoundingBox, Detection, ExtractedField, FontAnalysisField, FontAnalysis, PlacementCheck, ComplianceResult, ScanSummaryItem, ScanResponse, ScanRequest

    # Differential Parity Test for Model: backend.app.schemas.scan.DetectionMethod
    sample_kwargs = _build_model_sample_inputs(DetectionMethod, fallback={})
    verify_model_differential("backend.app.schemas.scan", "DetectionMethod", DetectionMethod, sample_kwargs)

    # Differential Parity Test for Model: backend.app.schemas.scan.BoundingBox
    sample_kwargs = _build_model_sample_inputs(BoundingBox, fallback={'x_min': 5, 'y_min': 5, 'x_max': 5, 'y_max': 5})
    verify_model_differential("backend.app.schemas.scan", "BoundingBox", BoundingBox, sample_kwargs)

    # Differential Parity Test for Model: backend.app.schemas.scan.Detection
    sample_kwargs = _build_model_sample_inputs(Detection, fallback={'method': 'sample_method', 'confidence': 10.5, 'pdp_bbox': 'sample_pdp_bbox'})
    verify_model_differential("backend.app.schemas.scan", "Detection", Detection, sample_kwargs)

    # Differential Parity Test for Model: backend.app.schemas.scan.ExtractedField
    sample_kwargs = _build_model_sample_inputs(ExtractedField, fallback={'field_name': 'sample_field_name', 'raw_ocr_text': 'sample_raw_ocr_text', 'raw_text': 'sample_raw_text', 'normalized_value': 'sample_normalized_value', 'unit': 'sample_unit', 'confidence': 10.5, 'bbox': 'sample_bbox', 'bounding_box': [1, 2, 3]})
    verify_model_differential("backend.app.schemas.scan", "ExtractedField", ExtractedField, sample_kwargs)

    # Differential Parity Test for Model: backend.app.schemas.scan.FontAnalysisField
    sample_kwargs = _build_model_sample_inputs(FontAnalysisField, fallback={'field_name': 'sample_field_name', 'measured_height_mm': 10.5, 'required_height_mm': 10.5, 'status': 'sample_status', 'calibration_confidence': 10.5})
    verify_model_differential("backend.app.schemas.scan", "FontAnalysisField", FontAnalysisField, sample_kwargs)

    # Differential Parity Test for Model: backend.app.schemas.scan.FontAnalysis
    sample_kwargs = _build_model_sample_inputs(FontAnalysis, fallback={'calibration_method': 'sample_calibration_method', 'mm_per_pixel': 10.5, 'fields': ['item_1', 'item_2']})
    verify_model_differential("backend.app.schemas.scan", "FontAnalysis", FontAnalysis, sample_kwargs)

    # Differential Parity Test for Model: backend.app.schemas.scan.PlacementCheck
    sample_kwargs = _build_model_sample_inputs(PlacementCheck, fallback={'field_name': 'sample_field_name', 'within_pdp': True, 'confidence': 10.5})
    verify_model_differential("backend.app.schemas.scan", "PlacementCheck", PlacementCheck, sample_kwargs)

    # Differential Parity Test for Model: backend.app.schemas.scan.ComplianceResult
    sample_kwargs = _build_model_sample_inputs(ComplianceResult, fallback={'rule_id': 'test_rule_id_123', 'rule_name': 'sample_rule_name', 'field_name': 'sample_field_name', 'status': 'sample_status', 'confidence': 10.5, 'message': 'sample_message', 'violation_reason': 'sample_violation_reason', 'measured_value': 'sample_measured_value', 'expected_value': 'sample_expected_value', 'rule_version': 'sample_rule_version'})
    verify_model_differential("backend.app.schemas.scan", "ComplianceResult", ComplianceResult, sample_kwargs)

    # Differential Parity Test for Model: backend.app.schemas.scan.ScanSummaryItem
    sample_kwargs = _build_model_sample_inputs(ScanSummaryItem, fallback={'scan_id': 'test_scan_id_123', 'product_name': 'sample_product_name', 'brand_name': 'sample_brand_name', 'category': 'sample_category', 'overall_status': 'sample_overall_status', 'overall_confidence': 10.5, 'rule_version': 'sample_rule_version', 'evidence_image_url': 'sample_evidence_image_url', 'violations_count': 5, 'created_at': '2025-01-01T12:00:00'})
    verify_model_differential("backend.app.schemas.scan", "ScanSummaryItem", ScanSummaryItem, sample_kwargs)

    # Differential Parity Test for Model: backend.app.schemas.scan.ScanResponse
    sample_kwargs = _build_model_sample_inputs(ScanResponse, fallback={'scan_id': 'test_scan_id_123', 'product_id': 'test_product_id_123', 'product_name': 'sample_product_name', 'product_name_hint': 'sample_product_name_hint', 'brand_name': 'sample_brand_name', 'category': 'sample_category', 'overall_status': 'sample_overall_status', 'overall_confidence': 10.5, 'calibrated_scale_factor': 10.5, 'calibration_method': 'sample_calibration_method', 'rule_version': 'sample_rule_version', 'original_image_url': 'sample_original_image_url', 'evidence_image_url': 'sample_evidence_image_url', 'created_at': '2025-01-01T12:00:00', 'timestamp': '2025-01-01T12:00:00', 'detection': 'sample_detection', 'extracted_fields': [{'trace_id': 'test_trace_123', 'attempt_count': 1, 'payload': {'status': 'ok'}, 'scores': [0.2, 0.5, 0.8]}], 'font_analysis': 'sample_font_analysis', 'placement_checks': ['item_1', 'item_2'], 'compliance_results': ['item_1', 'item_2']})
    verify_model_differential("backend.app.schemas.scan", "ScanResponse", ScanResponse, sample_kwargs)

    # Differential Parity Test for Model: backend.app.schemas.scan.ScanRequest
    sample_kwargs = _build_model_sample_inputs(ScanRequest, fallback={'calibration_method': 'sample_calibration_method', 'known_object_size_mm': 10.5})
    verify_model_differential("backend.app.schemas.scan", "ScanRequest", ScanRequest, sample_kwargs)



def test_differential_parity_9_backend_app_routers_auth():
    # Direct import: fails loudly with ImportError if the symbol was renamed or deleted
    from backend.app.routers.auth import login, get_me
    from backend.app.db.models import User
    from backend.app.schemas.auth import LoginRequest

    # Differential Parity Test for Function: backend.app.routers.auth.login
    sample = _build_model_sample_inputs(LoginRequest, fallback={'username': 'sample_username', 'password': 'sample_password'})
    sample_kwargs = {'request': LoginRequest(**sample), 'db': 'sample_db'}
    verify_function_differential("backend.app.routers.auth", "login", login, sample_kwargs)

    # Differential Parity Test for Function: backend.app.routers.auth.get_me
    sample = _build_model_sample_inputs(User, fallback={'id': 'test_id_123', 'username': 'sample_username', 'hashed_password': 'sample_hashed_password', 'role': 'sample_role', 'full_name': 'sample_full_name', 'is_active': True, 'created_at': '2025-01-01T12:00:00', 'scans': ['item_1', 'item_2']})
    sample_kwargs = {'current_user': User(**sample)}
    verify_function_differential("backend.app.routers.auth", "get_me", get_me, sample_kwargs)



def test_differential_parity_10_backend_app_routers_dashboard():
    # Direct import: fails loudly with ImportError if the symbol was renamed or deleted
    from backend.app.routers.dashboard import get_dashboard_statistics

    # Differential Parity Test for Function: backend.app.routers.dashboard.get_dashboard_statistics
    sample_kwargs = {'db': 'sample_db'}
    verify_function_differential("backend.app.routers.dashboard", "get_dashboard_statistics", get_dashboard_statistics, sample_kwargs)



def test_differential_parity_11_backend_app_routers_history():
    # Direct import: fails loudly with ImportError if the symbol was renamed or deleted
    from backend.app.routers.history import list_inspection_history, get_scan_details
    from backend.app.db.models import User

    # Differential Parity Test for Function: backend.app.routers.history.list_inspection_history
    sample = _build_model_sample_inputs(User, fallback={'id': 'test_id_123', 'username': 'sample_username', 'hashed_password': 'sample_hashed_password', 'role': 'sample_role', 'full_name': 'sample_full_name', 'is_active': True, 'created_at': '2025-01-01T12:00:00', 'scans': ['item_1', 'item_2']})
    sample_kwargs = {'page': 5, 'page_size': 5, 'status_filter': 'sample_status_filter', 'category_filter': 'sample_category_filter', 'product_name': 'sample_product_name', 'from_date': 'sample_from_date', 'to_date': 'sample_to_date', 'current_user': User(**sample), 'db': 'sample_db'}
    verify_function_differential("backend.app.routers.history", "list_inspection_history", list_inspection_history, sample_kwargs)

    # Differential Parity Test for Function: backend.app.routers.history.get_scan_details
    sample = _build_model_sample_inputs(User, fallback={'id': 'test_id_123', 'username': 'sample_username', 'hashed_password': 'sample_hashed_password', 'role': 'sample_role', 'full_name': 'sample_full_name', 'is_active': True, 'created_at': '2025-01-01T12:00:00', 'scans': ['item_1', 'item_2']})
    sample_kwargs = {'scan_id': 'test_scan_id_123', 'current_user': User(**sample), 'db': 'sample_db'}
    verify_function_differential("backend.app.routers.history", "get_scan_details", get_scan_details, sample_kwargs)



def test_differential_parity_12_backend_app_routers_reports():
    # Direct import: fails loudly with ImportError if the symbol was renamed or deleted
    from backend.app.routers.reports import export_pdf_report, export_docx_report, export_json_report

    # Differential Parity Test for Function: backend.app.routers.reports.export_pdf_report
    sample_kwargs = {'scan_id': 'test_scan_id_123', 'db': 'sample_db'}
    verify_function_differential("backend.app.routers.reports", "export_pdf_report", export_pdf_report, sample_kwargs)

    # Differential Parity Test for Function: backend.app.routers.reports.export_docx_report
    sample_kwargs = {'scan_id': 'test_scan_id_123', 'db': 'sample_db'}
    verify_function_differential("backend.app.routers.reports", "export_docx_report", export_docx_report, sample_kwargs)

    # Differential Parity Test for Function: backend.app.routers.reports.export_json_report
    sample_kwargs = {'scan_id': 'test_scan_id_123', 'db': 'sample_db'}
    verify_function_differential("backend.app.routers.reports", "export_json_report", export_json_report, sample_kwargs)



def test_differential_parity_13_backend_app_routers_scan():
    # Direct import: fails loudly with ImportError if the symbol was renamed or deleted
    from backend.app.routers.scan import scan_label
    from backend.app.schemas.enums import CalibrationMethod

    # Differential Parity Test for Function: backend.app.routers.scan.scan_label
    sample = _build_model_sample_inputs(CalibrationMethod, fallback={})
    sample_kwargs = {'image': 'sample_image', 'file': 'sample_file', 'calibration_method': CalibrationMethod(**sample), 'known_object_size_mm': 10.5, 'known_marker_size_mm': 10.5, 'product_category': 'sample_product_category', 'category': 'sample_category', 'db': 'sample_db'}
    verify_function_differential("backend.app.routers.scan", "scan_label", scan_label, sample_kwargs)



def test_differential_parity_14_backend_app_routers_search():
    # Direct import: fails loudly with ImportError if the symbol was renamed or deleted
    from backend.app.routers.search import universal_search
    from backend.app.db.models import User

    # Differential Parity Test for Function: backend.app.routers.search.universal_search
    sample = _build_model_sample_inputs(User, fallback={'id': 'test_id_123', 'username': 'sample_username', 'hashed_password': 'sample_hashed_password', 'role': 'sample_role', 'full_name': 'sample_full_name', 'is_active': True, 'created_at': '2025-01-01T12:00:00', 'scans': ['item_1', 'item_2']})
    sample_kwargs = {'q': 'sample_q', 'status_filter': 'sample_status_filter', 'category_filter': 'sample_category_filter', 'limit': 5, 'current_user': User(**sample), 'db': 'sample_db'}
    verify_function_differential("backend.app.routers.search", "universal_search", universal_search, sample_kwargs)



def test_differential_parity_15_backend_app_core_config():
    # Direct import: fails loudly with ImportError if the symbol was renamed or deleted
    from backend.app.core.config import Settings

    # Differential Parity Test for Model: backend.app.core.config.Settings
    sample_kwargs = _build_model_sample_inputs(Settings, fallback={'PROJECT_NAME': 'sample_PROJECT_NAME', 'API_V1_STR': 'sample_API_V1_STR', 'DATABASE_URL': 'sample_DATABASE_URL', 'SECRET_KEY': 'sample_SECRET_KEY', 'RULE_CONFIG_PATH': 'sample_RULE_CONFIG_PATH', 'CONFIDENCE_THRESHOLD': 10.5, 'STATIC_UPLOAD_DIR': 'sample_STATIC_UPLOAD_DIR', 'CORS_ORIGINS': ['item_1', 'item_2']})
    verify_model_differential("backend.app.core.config", "Settings", Settings, sample_kwargs)



def test_differential_parity_16_backend_app_core_security():
    # Direct import: fails loudly with ImportError if the symbol was renamed or deleted
    from backend.app.core.security import hash_password, verify_password, create_access_token, decode_access_token, get_current_user, require_role

    # Differential Parity Test for Function: backend.app.core.security.hash_password
    sample_kwargs = {'password': 'sample_password'}
    verify_function_differential("backend.app.core.security", "hash_password", hash_password, sample_kwargs)

    # Differential Parity Test for Function: backend.app.core.security.verify_password
    sample_kwargs = {'plain_password': 'sample_plain_password', 'hashed_password': 'sample_hashed_password'}
    verify_function_differential("backend.app.core.security", "verify_password", verify_password, sample_kwargs)

    # Differential Parity Test for Function: backend.app.core.security.create_access_token
    sample_kwargs = {'username': 'sample_username', 'role': 'sample_role', 'expires_in_seconds': 5}
    verify_function_differential("backend.app.core.security", "create_access_token", create_access_token, sample_kwargs)

    # Differential Parity Test for Function: backend.app.core.security.decode_access_token
    sample_kwargs = {'token': 'sample_token'}
    verify_function_differential("backend.app.core.security", "decode_access_token", decode_access_token, sample_kwargs)

    # Differential Parity Test for Function: backend.app.core.security.get_current_user
    sample_kwargs = {'authorization': 'sample_authorization', 'db': 'sample_db'}
    verify_function_differential("backend.app.core.security", "get_current_user", get_current_user, sample_kwargs)

    # Differential Parity Test for Function: backend.app.core.security.require_role
    sample_kwargs = {'allowed_roles': ['item_1', 'item_2']}
    verify_function_differential("backend.app.core.security", "require_role", require_role, sample_kwargs)



def test_differential_parity_17_backend_app_services_reporting_docx_report():
    # Direct import: fails loudly with ImportError if the symbol was renamed or deleted
    from backend.app.services.reporting.docx_report import generate_docx_report
    from backend.app.schemas.scan import ScanResponse

    # Differential Parity Test for Function: backend.app.services.reporting.docx_report.generate_docx_report
    sample = _build_model_sample_inputs(ScanResponse, fallback={'scan_id': 'test_scan_id_123', 'product_id': 'test_product_id_123', 'product_name': 'sample_product_name', 'product_name_hint': 'sample_product_name_hint', 'brand_name': 'sample_brand_name', 'category': 'sample_category', 'overall_status': 'sample_overall_status', 'overall_confidence': 10.5, 'calibrated_scale_factor': 10.5, 'calibration_method': 'sample_calibration_method', 'rule_version': 'sample_rule_version', 'original_image_url': 'sample_original_image_url', 'evidence_image_url': 'sample_evidence_image_url', 'created_at': '2025-01-01T12:00:00', 'timestamp': '2025-01-01T12:00:00', 'detection': 'sample_detection', 'extracted_fields': [{'trace_id': 'test_trace_123', 'attempt_count': 1, 'payload': {'status': 'ok'}, 'scores': [0.2, 0.5, 0.8]}], 'font_analysis': 'sample_font_analysis', 'placement_checks': ['item_1', 'item_2'], 'compliance_results': ['item_1', 'item_2']})
    sample_kwargs = {'scan': ScanResponse(**sample)}
    verify_function_differential("backend.app.services.reporting.docx_report", "generate_docx_report", generate_docx_report, sample_kwargs)



def test_differential_parity_18_backend_app_services_reporting_pdf_report():
    # Direct import: fails loudly with ImportError if the symbol was renamed or deleted
    from backend.app.services.reporting.pdf_report import generate_pdf_report

    # Differential Parity Test for Function: backend.app.services.reporting.pdf_report.generate_pdf_report
    sample_kwargs = {'scan_data': {'key': 'value'}, 'output_path': 'sample_output_path'}
    verify_function_differential("backend.app.services.reporting.pdf_report", "generate_pdf_report", generate_pdf_report, sample_kwargs)



def test_differential_parity_19_backend_app_services_vision_calibration():
    # Direct import: fails loudly with ImportError if the symbol was renamed or deleted
    from backend.app.services.vision.calibration import load_rules, calibrate_aruco, calibrate_known_object, get_calibration, get_mm_per_pixel, get_required_font_height, evaluate_font_heights
    from backend.app.schemas.enums import CalibrationMethod

    # Differential Parity Test for Function: backend.app.services.vision.calibration.load_rules
    sample_kwargs = {}
    verify_function_differential("backend.app.services.vision.calibration", "load_rules", load_rules, sample_kwargs)

    # Differential Parity Test for Function: backend.app.services.vision.calibration.calibrate_aruco
    sample_kwargs = {'image': 'sample_image', 'known_marker_size_mm': 10.5}
    verify_function_differential("backend.app.services.vision.calibration", "calibrate_aruco", calibrate_aruco, sample_kwargs)

    # Differential Parity Test for Function: backend.app.services.vision.calibration.calibrate_known_object
    sample_kwargs = {'object_bbox_px_height': 10.5, 'known_size_mm': 10.5}
    verify_function_differential("backend.app.services.vision.calibration", "calibrate_known_object", calibrate_known_object, sample_kwargs)

    # Differential Parity Test for Function: backend.app.services.vision.calibration.get_calibration
    sample = _build_model_sample_inputs(CalibrationMethod, fallback={})
    sample_kwargs = {'image': 'sample_image', 'method': CalibrationMethod(**sample), 'known_object_size_mm': 10.5, 'known_object_bbox_px_height': 10.5, 'aruco_marker_size_mm': 10.5}
    verify_function_differential("backend.app.services.vision.calibration", "get_calibration", get_calibration, sample_kwargs)

    # Differential Parity Test for Function: backend.app.services.vision.calibration.get_mm_per_pixel
    sample = _build_model_sample_inputs(CalibrationMethod, fallback={})
    sample_kwargs = {'image': 'sample_image', 'method': CalibrationMethod(**sample), 'known_object_size_mm': 10.5, 'known_object_bbox_px_height': 10.5}
    verify_function_differential("backend.app.services.vision.calibration", "get_mm_per_pixel", get_mm_per_pixel, sample_kwargs)

    # Differential Parity Test for Function: backend.app.services.vision.calibration.get_required_font_height
    sample_kwargs = {'field_name': 'sample_field_name', 'normalized_value': 'sample_normalized_value', 'pdp_area_cm2': 10.5, 'is_blown_or_molded': True, 'rules_data': {'key': 'value'}}
    verify_function_differential("backend.app.services.vision.calibration", "get_required_font_height", get_required_font_height, sample_kwargs)

    # Differential Parity Test for Function: backend.app.services.vision.calibration.evaluate_font_heights
    sample = _build_model_sample_inputs(CalibrationMethod, fallback={})
    sample_kwargs = {'extracted_fields': ['item_1', 'item_2'], 'mm_per_pixel': 10.5, 'calibration_method': CalibrationMethod(**sample), 'calibration_confidence': 10.5, 'pdp_area_cm2': 10.5, 'is_blown_or_molded': True, 'rules_data': {'key': 'value'}}
    verify_function_differential("backend.app.services.vision.calibration", "evaluate_font_heights", evaluate_font_heights, sample_kwargs)



def test_differential_parity_20_backend_app_services_vision_detection():
    # Direct import: fails loudly with ImportError if the symbol was renamed or deleted
    from backend.app.services.vision.detection import detect_pdp, opencv_fallback_detect

    # Differential Parity Test for Function: backend.app.services.vision.detection.detect_pdp
    sample_kwargs = {'image': 'sample_image'}
    verify_function_differential("backend.app.services.vision.detection", "detect_pdp", detect_pdp, sample_kwargs)

    # Differential Parity Test for Function: backend.app.services.vision.detection.opencv_fallback_detect
    sample_kwargs = {'image': 'sample_image'}
    verify_function_differential("backend.app.services.vision.detection", "opencv_fallback_detect", opencv_fallback_detect, sample_kwargs)



def test_differential_parity_21_backend_app_services_vision_extraction():
    # Direct import: fails loudly with ImportError if the symbol was renamed or deleted
    from backend.app.services.vision.extraction import parse_date, date_norm_to_months, parse_mrp, parse_net_quantity, parse_unit_sale_price, parse_consumer_care, parse_manufacturer, parse_generic_name, parse_country_of_origin, match_field_label, merge_bounding_boxes, find_spatial_neighbors, extract_fields
    from backend.app.schemas.scan import BoundingBox

    # Differential Parity Test for Function: backend.app.services.vision.extraction.parse_date
    sample_kwargs = {'text': 'sample_text'}
    verify_function_differential("backend.app.services.vision.extraction", "parse_date", parse_date, sample_kwargs)

    # Differential Parity Test for Function: backend.app.services.vision.extraction.date_norm_to_months
    sample_kwargs = {'norm_str': 'sample_norm_str'}
    verify_function_differential("backend.app.services.vision.extraction", "date_norm_to_months", date_norm_to_months, sample_kwargs)

    # Differential Parity Test for Function: backend.app.services.vision.extraction.parse_mrp
    sample_kwargs = {'text': 'sample_text', 'matched_kw': 'sample_matched_kw'}
    verify_function_differential("backend.app.services.vision.extraction", "parse_mrp", parse_mrp, sample_kwargs)

    # Differential Parity Test for Function: backend.app.services.vision.extraction.parse_net_quantity
    sample_kwargs = {'text': 'sample_text', 'matched_kw': 'sample_matched_kw'}
    verify_function_differential("backend.app.services.vision.extraction", "parse_net_quantity", parse_net_quantity, sample_kwargs)

    # Differential Parity Test for Function: backend.app.services.vision.extraction.parse_unit_sale_price
    sample_kwargs = {'text': 'sample_text'}
    verify_function_differential("backend.app.services.vision.extraction", "parse_unit_sale_price", parse_unit_sale_price, sample_kwargs)

    # Differential Parity Test for Function: backend.app.services.vision.extraction.parse_consumer_care
    sample_kwargs = {'text': 'sample_text'}
    verify_function_differential("backend.app.services.vision.extraction", "parse_consumer_care", parse_consumer_care, sample_kwargs)

    # Differential Parity Test for Function: backend.app.services.vision.extraction.parse_manufacturer
    sample_kwargs = {'text': 'sample_text', 'matched_kw': 'sample_matched_kw'}
    verify_function_differential("backend.app.services.vision.extraction", "parse_manufacturer", parse_manufacturer, sample_kwargs)

    # Differential Parity Test for Function: backend.app.services.vision.extraction.parse_generic_name
    sample_kwargs = {'text': 'sample_text', 'matched_kw': 'sample_matched_kw'}
    verify_function_differential("backend.app.services.vision.extraction", "parse_generic_name", parse_generic_name, sample_kwargs)

    # Differential Parity Test for Function: backend.app.services.vision.extraction.parse_country_of_origin
    sample_kwargs = {'text': 'sample_text'}
    verify_function_differential("backend.app.services.vision.extraction", "parse_country_of_origin", parse_country_of_origin, sample_kwargs)

    # Differential Parity Test for Function: backend.app.services.vision.extraction.match_field_label
    sample_kwargs = {'text': 'sample_text', 'threshold': 10.5}
    verify_function_differential("backend.app.services.vision.extraction", "match_field_label", match_field_label, sample_kwargs)

    # Differential Parity Test for Function: backend.app.services.vision.extraction.merge_bounding_boxes
    sample_b1 = _build_model_sample_inputs(BoundingBox, fallback={'x_min': 5, 'y_min': 5, 'x_max': 5, 'y_max': 5})
    sample_b2 = _build_model_sample_inputs(BoundingBox, fallback={'x_min': 5, 'y_min': 5, 'x_max': 5, 'y_max': 5})
    sample_kwargs = {'b1': BoundingBox(**sample_b1), 'b2': BoundingBox(**sample_b2)}
    verify_function_differential("backend.app.services.vision.extraction", "merge_bounding_boxes", merge_bounding_boxes, sample_kwargs)

    # Differential Parity Test for Function: backend.app.services.vision.extraction.find_spatial_neighbors
    sample_kwargs = {'target_idx': 5, 'ocr_results': [{'trace_id': 'test_trace_123', 'attempt_count': 1, 'payload': {'status': 'ok'}, 'scores': [0.2, 0.5, 0.8]}], 'max_horizontal_gap': 5, 'max_vertical_gap': 5}
    verify_function_differential("backend.app.services.vision.extraction", "find_spatial_neighbors", find_spatial_neighbors, sample_kwargs)

    # Differential Parity Test for Function: backend.app.services.vision.extraction.extract_fields
    sample_kwargs = {'ocr_results': [{'trace_id': 'test_trace_123', 'attempt_count': 1, 'payload': {'status': 'ok'}, 'scores': [0.2, 0.5, 0.8]}]}
    verify_function_differential("backend.app.services.vision.extraction", "extract_fields", extract_fields, sample_kwargs)



def test_differential_parity_22_backend_app_services_vision_ocr():
    # Direct import: fails loudly with ImportError if the symbol was renamed or deleted
    from backend.app.services.vision.ocr import get_ocr_reader, run_ocr

    # Differential Parity Test for Function: backend.app.services.vision.ocr.get_ocr_reader
    sample_kwargs = {}
    verify_function_differential("backend.app.services.vision.ocr", "get_ocr_reader", get_ocr_reader, sample_kwargs)

    # Differential Parity Test for Function: backend.app.services.vision.ocr.run_ocr
    sample_kwargs = {'image': 'sample_image', 'use_clahe': True, 'min_confidence': 10.5, 'max_dim': 5}
    verify_function_differential("backend.app.services.vision.ocr", "run_ocr", run_ocr, sample_kwargs)



def test_differential_parity_23_backend_app_services_vision_preprocessing():
    # Direct import: fails loudly with ImportError if the symbol was renamed or deleted
    from backend.app.services.vision.preprocessing import decode_image, resize_to_max_dimension, to_grayscale, apply_clahe, apply_bilateral_filter, apply_adaptive_threshold, preprocess_for_ocr

    # Differential Parity Test for Function: backend.app.services.vision.preprocessing.decode_image
    sample_kwargs = {'image_bytes': 'sample_image_bytes'}
    verify_function_differential("backend.app.services.vision.preprocessing", "decode_image", decode_image, sample_kwargs)

    # Differential Parity Test for Function: backend.app.services.vision.preprocessing.resize_to_max_dimension
    sample_kwargs = {'image': 'sample_image', 'max_dim': 5}
    verify_function_differential("backend.app.services.vision.preprocessing", "resize_to_max_dimension", resize_to_max_dimension, sample_kwargs)

    # Differential Parity Test for Function: backend.app.services.vision.preprocessing.to_grayscale
    sample_kwargs = {'image': 'sample_image'}
    verify_function_differential("backend.app.services.vision.preprocessing", "to_grayscale", to_grayscale, sample_kwargs)

    # Differential Parity Test for Function: backend.app.services.vision.preprocessing.apply_clahe
    sample_kwargs = {'image': 'sample_image', 'clip_limit': 10.5, 'tile_grid_size': 5}
    verify_function_differential("backend.app.services.vision.preprocessing", "apply_clahe", apply_clahe, sample_kwargs)

    # Differential Parity Test for Function: backend.app.services.vision.preprocessing.apply_bilateral_filter
    sample_kwargs = {'image': 'sample_image', 'd': 5, 'sigma_color': 10.5, 'sigma_space': 10.5}
    verify_function_differential("backend.app.services.vision.preprocessing", "apply_bilateral_filter", apply_bilateral_filter, sample_kwargs)

    # Differential Parity Test for Function: backend.app.services.vision.preprocessing.apply_adaptive_threshold
    sample_kwargs = {'image': 'sample_image', 'block_size': 5, 'c': 5}
    verify_function_differential("backend.app.services.vision.preprocessing", "apply_adaptive_threshold", apply_adaptive_threshold, sample_kwargs)

    # Differential Parity Test for Function: backend.app.services.vision.preprocessing.preprocess_for_ocr
    sample_kwargs = {'image': 'sample_image', 'max_dim': 5}
    verify_function_differential("backend.app.services.vision.preprocessing", "preprocess_for_ocr", preprocess_for_ocr, sample_kwargs)



def test_differential_parity_24_backend_app_services_compliance_rule_engine():
    # Direct import: fails loudly with ImportError if the symbol was renamed or deleted
    from backend.app.services.compliance.rule_engine import load_rules, reload_rules, load_lmpc_rules, get_rule_version, evaluate_compliance, determine_overall_status
    from backend.app.schemas.scan import FontAnalysis

    # Differential Parity Test for Function: backend.app.services.compliance.rule_engine.load_rules
    sample_kwargs = {}
    verify_function_differential("backend.app.services.compliance.rule_engine", "load_rules", load_rules, sample_kwargs)

    # Differential Parity Test for Function: backend.app.services.compliance.rule_engine.reload_rules
    sample_kwargs = {}
    verify_function_differential("backend.app.services.compliance.rule_engine", "reload_rules", reload_rules, sample_kwargs)

    # Differential Parity Test for Function: backend.app.services.compliance.rule_engine.load_lmpc_rules
    sample_kwargs = {}
    verify_function_differential("backend.app.services.compliance.rule_engine", "load_lmpc_rules", load_lmpc_rules, sample_kwargs)

    # Differential Parity Test for Function: backend.app.services.compliance.rule_engine.get_rule_version
    sample_kwargs = {}
    verify_function_differential("backend.app.services.compliance.rule_engine", "get_rule_version", get_rule_version, sample_kwargs)

    # Differential Parity Test for Function: backend.app.services.compliance.rule_engine.evaluate_compliance
    sample = _build_model_sample_inputs(FontAnalysis, fallback={'calibration_method': 'sample_calibration_method', 'mm_per_pixel': 10.5, 'fields': ['item_1', 'item_2']})
    sample_kwargs = {'extracted_fields': ['item_1', 'item_2'], 'font_analysis': FontAnalysis(**sample), 'placement_checks': ['item_1', 'item_2'], 'category': 'sample_category'}
    verify_function_differential("backend.app.services.compliance.rule_engine", "evaluate_compliance", evaluate_compliance, sample_kwargs)

    # Differential Parity Test for Function: backend.app.services.compliance.rule_engine.determine_overall_status
    sample_kwargs = {'results': ['item_1', 'item_2']}
    verify_function_differential("backend.app.services.compliance.rule_engine", "determine_overall_status", determine_overall_status, sample_kwargs)



def test_differential_parity_25_backend_app_db_base():
    # Direct import: fails loudly with ImportError if the symbol was renamed or deleted
    from backend.app.db.base import Base

    # Differential Parity Test for Model: backend.app.db.base.Base
    sample_kwargs = _build_model_sample_inputs(Base, fallback={})
    verify_model_differential("backend.app.db.base", "Base", Base, sample_kwargs)



def test_differential_parity_26_backend_app_db_models():
    # Direct import: fails loudly with ImportError if the symbol was renamed or deleted
    from backend.app.db.models import User, Product, Scan, ComplianceResult, utc_now

    # Differential Parity Test for Model: backend.app.db.models.User
    sample_kwargs = _build_model_sample_inputs(User, fallback={'id': 'test_id_123', 'username': 'sample_username', 'hashed_password': 'sample_hashed_password', 'role': 'sample_role', 'full_name': 'sample_full_name', 'is_active': True, 'created_at': '2025-01-01T12:00:00', 'scans': ['item_1', 'item_2']})
    verify_model_differential("backend.app.db.models", "User", User, sample_kwargs)

    # Differential Parity Test for Model: backend.app.db.models.Product
    sample_kwargs = _build_model_sample_inputs(Product, fallback={'id': 'test_id_123', 'product_name': 'sample_product_name', 'brand_name': 'sample_brand_name', 'category': 'sample_category', 'net_quantity_declared': 'sample_net_quantity_declared', 'mrp_declared': 10.5, 'country_of_origin': 'sample_country_of_origin', 'manufacturer_details': 'sample_manufacturer_details', 'mfg_date': 'sample_mfg_date', 'expiry_date': 'sample_expiry_date', 'consumer_care': 'sample_consumer_care', 'created_at': '2025-01-01T12:00:00', 'scans': ['item_1', 'item_2']})
    verify_model_differential("backend.app.db.models", "Product", Product, sample_kwargs)

    # Differential Parity Test for Model: backend.app.db.models.Scan
    sample_kwargs = _build_model_sample_inputs(Scan, fallback={'id': 'test_id_123', 'product_id': 'test_product_id_123', 'original_image_path': 'sample_original_image_path', 'evidence_image_path': 'sample_evidence_image_path', 'overall_status': 'sample_overall_status', 'overall_confidence': 10.5, 'calibrated_scale_factor': 10.5, 'calibration_method': 'sample_calibration_method', 'rule_version': 'sample_rule_version', 'inspector_id': 'test_inspector_id_123', 'extracted_fields_json': 'sample_extracted_fields_json', 'notes': 'sample_notes', 'created_at': '2025-01-01T12:00:00', 'product': 'sample_product', 'inspector': 'sample_inspector', 'compliance_results': ['item_1', 'item_2']})
    verify_model_differential("backend.app.db.models", "Scan", Scan, sample_kwargs)

    # Differential Parity Test for Model: backend.app.db.models.ComplianceResult
    sample_kwargs = _build_model_sample_inputs(ComplianceResult, fallback={'id': 'test_id_123', 'scan_id': 'test_scan_id_123', 'rule_id': 'test_rule_id_123', 'rule_name': 'sample_rule_name', 'field_name': 'sample_field_name', 'status': 'sample_status', 'confidence': 10.5, 'measured_value': 'sample_measured_value', 'expected_value': 'sample_expected_value', 'violation_reason': 'sample_violation_reason', 'bounding_box_json': 'sample_bounding_box_json', 'rule_version': 'sample_rule_version', 'created_at': '2025-01-01T12:00:00', 'scan': 'sample_scan'})
    verify_model_differential("backend.app.db.models", "ComplianceResult", ComplianceResult, sample_kwargs)

    # Differential Parity Test for Function: backend.app.db.models.utc_now
    sample_kwargs = {}
    verify_function_differential("backend.app.db.models", "utc_now", utc_now, sample_kwargs)



def test_differential_parity_27_backend_app_db_seed():
    # Direct import: fails loudly with ImportError if the symbol was renamed or deleted
    from backend.app.db.seed import seed_database

    # Differential Parity Test for Function: backend.app.db.seed.seed_database
    sample_kwargs = {'force_reseed': True}
    verify_function_differential("backend.app.db.seed", "seed_database", seed_database, sample_kwargs)



def test_differential_parity_28_backend_app_db_session():
    # Direct import: fails loudly with ImportError if the symbol was renamed or deleted
    from backend.app.db.session import get_db, init_db

    # Differential Parity Test for Function: backend.app.db.session.get_db
    sample_kwargs = {}
    verify_function_differential("backend.app.db.session", "get_db", get_db, sample_kwargs)

    # Differential Parity Test for Function: backend.app.db.session.init_db
    sample_kwargs = {}
    verify_function_differential("backend.app.db.session", "init_db", init_db, sample_kwargs)


