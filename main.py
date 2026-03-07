from __future__ import annotations

from pathlib import Path
from typing import Optional
import sys

import typer

from auth import clear_credentials, get_credentials
from config import settings
from exporter import export_subscriptions
from logger import logger
from migrator import migrate_subscriptions
from state import MigrationState


app = typer.Typer(help="YouTube channel subscription migration tool.")


@app.command("auth-source")
def auth_source() -> None:
    """Authenticate the source Google account (used for reading subscriptions)."""
    get_credentials("source")
    logger.info("Source account authentication completed.")


@app.command("auth-target")
def auth_target() -> None:
    """Authenticate the target Google account (used for creating subscriptions)."""
    get_credentials("target")
    logger.info("Target account authentication completed.")


@app.command("clear-auth")
def clear_auth(
    source: bool = typer.Option(
        False, "--source", help="Clear stored credentials for the source account."
    ),
    target: bool = typer.Option(
        False, "--target", help="Clear stored credentials for the target account."
    ),
) -> None:
    """Clear stored OAuth credentials."""
    if not source and not target:
        typer.echo("Specify at least one of --source or --target.")
        raise typer.Exit(code=1)
    if source:
        clear_credentials("source")
    if target:
        clear_credentials("target")


@app.command("export-subscriptions")
def export_subscriptions_cmd(
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Output JSON file path for exported subscriptions.",
    )
) -> None:
    """Export source account subscriptions to a JSON file."""
    path = export_subscriptions(output)
    typer.echo(f"Exported subscriptions to {path}")


@app.command("migrate")
def migrate_cmd(
    input: Path = typer.Option(
        ...,
        "--input",
        "-i",
        exists=True,
        readable=True,
        help="Input JSON file with subscriptions (from export-subscriptions).",
    ),
    delay: float = typer.Option(
        settings.default_delay_seconds,
        "--delay",
        "-d",
        help="Delay in seconds between subscription operations.",
    ),
    resume: bool = typer.Option(
        True,
        "--resume/--no-resume",
        help="Resume from previous migration state file if present.",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Perform all checks but do NOT create any subscriptions.",
    ),
    limit: Optional[int] = typer.Option(
        None,
        "--limit",
        help="Limit the number of subscriptions processed in this run.",
    ),
    retry_failed_only: bool = typer.Option(
        False,
        "--retry-failed-only",
        help="Process only channels that previously failed in migration state.",
    ),
) -> None:
    """Migrate subscriptions from a JSON file to the target account."""
    migrate_subscriptions(
        input_path=input,
        delay_seconds=delay,
        dry_run=dry_run,
        resume=resume,
        limit=limit,
        retry_failed_only=retry_failed_only,
    )
    typer.echo("Migration run completed. Check logs and summary report for details.")


@app.command("status")
def status_cmd() -> None:
    """Show current migration status and summary."""
    if not settings.migration_state_file.exists():
        typer.echo("No migration state file found.")
        raise typer.Exit(code=0)

    state = MigrationState.load(path=settings.migration_state_file)
    typer.echo(f"Input file: {state.input_file}")
    typer.echo(f"Processed: {len(state.processed)}")
    typer.echo(f"Failed: {len(state.failed)}")
    typer.echo(f"Last updated: {state.last_updated}")


def interactive_menu() -> None:
    """Run an interactive text menu for common operations."""
    typer.echo("")
    typer.echo("YouTube Subscription Migrator - Interactive Mode")
    typer.echo("================================================")

    while True:
        typer.echo("")
        typer.echo("Select an option:")
        typer.echo("  1) Authenticate SOURCE account")
        typer.echo("  2) Authenticate TARGET account")
        typer.echo("  3) Export subscriptions from SOURCE account")
        typer.echo("  4) Migrate subscriptions to TARGET account")
        typer.echo("  5) Show migration status")
        typer.echo("  0) Exit")

        choice = typer.prompt("Enter your choice", default="0").strip()

        if choice == "0":
            typer.echo("Exiting interactive mode.")
            break

        if choice == "1":
            try:
                auth_source()
            except Exception as exc:  # noqa: BLE001
                typer.echo(f"Error during source authentication: {exc}")
            continue

        if choice == "2":
            try:
                auth_target()
            except Exception as exc:  # noqa: BLE001
                typer.echo(f"Error during target authentication: {exc}")
            continue

        if choice == "3":
            try:
                default_output = settings.default_export_file
                output_str = typer.prompt(
                    f"Output JSON path for exported subscriptions",
                    default=str(default_output),
                )
                output_path = Path(output_str)
                path = export_subscriptions(output_path)
                typer.echo(f"Exported subscriptions to {path}")
            except Exception as exc:  # noqa: BLE001
                typer.echo(f"Error during export: {exc}")
            continue

        if choice == "4":
            try:
                default_input = settings.default_export_file
                input_str = typer.prompt(
                    "Input JSON path for subscriptions",
                    default=str(default_input),
                )
                input_path = Path(input_str)

                delay = typer.prompt(
                    "Delay between operations in seconds",
                    default=str(settings.default_delay_seconds),
                )
                try:
                    delay_seconds = float(delay)
                except ValueError:
                    typer.echo(
                        f"Invalid delay '{delay}', using default {settings.default_delay_seconds}."
                    )
                    delay_seconds = settings.default_delay_seconds

                resume = typer.confirm(
                    "Resume from previous migration state if present?", default=True
                )
                dry_run = typer.confirm(
                    "Dry run only (no actual subscriptions created)?", default=False
                )
                retry_failed_only = typer.confirm(
                    "Retry only previously failed channels?", default=False
                )

                limit_str = typer.prompt(
                    "Limit number of subscriptions to process (blank for no limit)",
                    default="",
                ).strip()
                limit: Optional[int]
                if limit_str:
                    try:
                        limit = int(limit_str)
                    except ValueError:
                        typer.echo(
                            f"Invalid limit '{limit_str}', ignoring and processing all subscriptions."
                        )
                        limit = None
                else:
                    limit = None

                migrate_subscriptions(
                    input_path=input_path,
                    delay_seconds=delay_seconds,
                    dry_run=dry_run,
                    resume=resume,
                    limit=limit,
                    retry_failed_only=retry_failed_only,
                )
                typer.echo("Migration run completed. Check logs and summary report for details.")
            except Exception as exc:  # noqa: BLE001
                typer.echo(f"Error during migration: {exc}")
            continue

        if choice == "5":
            try:
                status_cmd()
            except Exception as exc:  # noqa: BLE001
                typer.echo(f"Error while reading status: {exc}")
            continue

        typer.echo(f"Unknown choice '{choice}'. Please select a valid option.")


def main() -> None:
    # If no additional CLI arguments are provided, run in interactive mode.
    if len(sys.argv) == 1:
        interactive_menu()
    else:
        app()


if __name__ == "__main__":
    main()

