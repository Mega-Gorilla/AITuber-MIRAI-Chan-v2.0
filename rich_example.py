from rich.table import Table
from rich import print

table = Table()

table.add_column("Name", style="cyan")
table.add_column("Age", style="magenta")
table.add_column("City", style="green")

table.add_row("Alice", "24", "New York")
table.add_row("Bob", "22", "Boston")
table.add_row("Charlie", "27", "Chicago")

print(table)

from rich.progress import track
import time

for step in track(range(10), description="Processing..."):
    time.sleep(0.1)

print("```python")
print("def hello_world():")
print("    print('Hello, world!')")
print("```")