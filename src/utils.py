from uuid import uuid4

import logging
from exceptions import InvalidOperationError


ALLOWED_STATUS_LIST = ["active", "frozen", "closed"]
ALLOWED_CURRENCY_LIST = ["RUB", "USD", "EUR", "KZT", "CNY"]
ALLOWED_PORTFOLIO_ASSETS_LIST = ["stocks", "bonds", "etf"]
ALLOWED_CLIENT_STATUS_LIST = ["active", "blocked"]
ALLOWED_ACCOUNT_ATTRIBUTES = ["account_id", "owner", "status", "balance", "currency"]
ALLOWED_TRANSACTION_TYPE_LIST = ["transfer", "external_transfer", "deposit", "withdrawal"]
ALLOWED_TRANSACTION_STATUS_LIST = ["pending", "processing", "completed", "failed", "cancelled"]
ALLOWED_AUDIT_LEVEL_LIST = ["INFO", "WARNING", "ERROR", "CRITICAL"]
ALLOWED_RISK_LEVEL_LIST = ["low", "medium", "high"]
DEFAULT_AUDIT_FILE = "audit.log"
DEFAULT_LARGE_AMOUNT_LIMIT = 10000
DEFAULT_FREQUENT_OPERATION_LIMIT = 3


def setup_logger() -> logging.Logger:
    """Configure and return the project logger.

    Returns:
        logging.Logger: Configured logger instance for the project.
    """
    logger = logging.getLogger(__name__)

    if not logger.handlers:
        logger.setLevel(logging.INFO)

        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(message)s"
        )

        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)

        logger.addHandler(console_handler)

    return logger

logger = setup_logger()


def numeric_value_validation(value: float, value_name: str) -> None:
    """Validate a numeric value.

    Args:
        value: any numeric value.

    Raises:
        InvalidOperationError: If value is not numeric or is not positive.
    """
    if not isinstance(value, (int, float)):
        logger.error(f"Invalid {value_name} type: {type(value).__name__}")
        raise InvalidOperationError(f"{value_name} must be a number.")
    
    if value < 0:
        logger.error(f"Non-positive {value_name} attempted: {value}")
        raise InvalidOperationError(f"{value_name} must be equal to or greater than zero.")

def string_value_validation(value: str, allowed_list: dict, value_name: str) -> None:
    """Validate a string status.

    Args:
        value: any string value.

    Raises:
        InvalidOperationError: If value is not in the allowed list.
    """
    if value not in allowed_list:
        logger.error(f"Invalid {value_name}: {value}.")
        raise InvalidOperationError(f"Invalid {value_name}: {value}, allowed_list: {allowed_list}")

def generate_id(id: str | None = None, id_name: str = "") -> str:
    """Generate a short unique identifier.

    Returns:
        str: Short uppercase identifier based on UUID.
    """
    if not id:
        id = uuid4().hex[:8].upper()
        logger.info(f"{id_name} generated: {id}")
    return id