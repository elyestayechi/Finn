import hashlib
from functools import lru_cache
from typing import Any

class Utils:
    @staticmethod
    @lru_cache(maxsize=128)
    def generate_cache_key(data: Any) -> str:
        """Generate a consistent cache key for any data structure"""
        if isinstance(data, (str, bytes)):
            content = data if isinstance(data, bytes) else data.encode()
        else:
            content = str(data).encode()
        return hashlib.md5(content).hexdigest()

    @staticmethod
    def format_currency(amount: float, currency: str) -> str:
        """Format currency amounts consistently"""
        if currency == 'TND':
            return f"{amount:,.3f} {currency}"
        return f"{amount:,.2f} {currency}"

    @staticmethod
    def safe_divide(numerator: float, denominator: float) -> float:
        """Safe division with zero handling"""
        try:
            return numerator / denominator
        except ZeroDivisionError:
            return 0.0