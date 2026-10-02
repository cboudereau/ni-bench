"""Reproduces the crash reported from the nightly feed import.

Run: python3 repro.py — prints 'ok' when the import path works.
"""

from inventory import Inventory

# rows exactly as they arrive from the nightly feed file
FEED_ROWS = [("wh-042 ", 10), ("wh-107", 5)]

inv = Inventory()
for sku, quantity in FEED_ROWS:
    inv.restock(sku, quantity)

left = inv.reserve("WH-042", 3)
assert left == 7, f"expected 7 left, got {left}"
assert inv.available("WH-107") == 5
print("ok")
