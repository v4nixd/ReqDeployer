from rich.console import Console
from version import __version__ as version

console = Console()
console.show_cursor(False)
console.set_window_title(f"ReqDeployer - {version}")