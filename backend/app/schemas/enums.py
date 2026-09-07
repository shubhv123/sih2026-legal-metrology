from enum import Enum


class ComplianceStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"


class RoleEnum(str, Enum):
    INSPECTOR = "inspector"
    ADMIN = "admin"


class CalibrationMethod(str, Enum):
    ARUCO = "aruco"
    KNOWN_OBJECT = "known_object"
    REFERENCE_OBJECT = "reference_object"  # alias for backward compatibility
    NONE = "none"


class ProductCategory(str, Enum):
    STANDARD_RETAIL = "standard_retail"
    FOOD_EXPIRY = "food_expiry"
    MEDICAL_DEVICE = "medical_device"
    BULK_EXEMPT = "bulk_exempt"
