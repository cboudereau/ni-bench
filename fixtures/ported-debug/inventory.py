"""In-memory warehouse stock ledger."""


class Inventory:
    def __init__(self):
        self._stock = {}

    def restock(self, sku, quantity):
        """Add received quantity for a SKU (feed rows arrive as raw strings)."""
        if quantity <= 0:
            raise ValueError("quantity must be positive")
        self._stock[sku] = self._stock.get(sku, 0) + quantity

    def reserve(self, sku, quantity):
        """Reserve quantity for an order; returns the remaining stock."""
        key = sku.strip().upper()
        available = self._stock[key]
        if available < quantity:
            raise ValueError(f"insufficient stock for {key}")
        self._stock[key] = available - quantity
        return self._stock[key]

    def available(self, sku):
        """Current stock for a SKU, 0 when unknown."""
        return self._stock.get(sku.strip().upper(), 0)
