from rich.console import Console
from rich.panel import Panel
from rich.pretty import Pretty

from src.db.chroma_client import collection_stats, get_collection

console = Console()

if __name__ == "__main__":
    console.print("[bold cyan]Verifying ChromaDB connection...[/bold cyan]")

    try:
        get_collection()
        stats = collection_stats()
        console.print(
            Panel(
                Pretty(stats),
                title="[green]ChromaDB — Ready[/green]",
                border_style="green",
            )
        )
    except Exception as exc:
        console.print(
            Panel(
                f"[red]{exc}[/red]",
                title="[red]ChromaDB — Connection Failed[/red]",
                border_style="red",
            )
        )
        raise SystemExit(1)
