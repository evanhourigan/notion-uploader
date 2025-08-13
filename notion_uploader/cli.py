#!/usr/bin/env python3

import argparse
import sys
import os
from .core import NotionUploader
from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table
from dotenv import load_dotenv

def main():
    # Load environment variables from .env file in project directory
    # This follows the same pattern as deepcast_post and diarized_transcriber
    project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env_path = os.path.join(project_dir, '.env')
    load_dotenv(env_path)
    
    console = Console()
    
    parser = argparse.ArgumentParser(
        description='Upload markdown files to Notion pages',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  notion-upload document.md --title "My Document"
  notion-upload transcript.md --title "Podcast Transcript" --database-id "custom-db-id"
  notion-upload notes.md --verbose
        """
    )
    
    parser.add_argument('file_path', help='Path to the markdown file to upload')
    parser.add_argument('--title', help='Title for the Notion page (optional)')
    parser.add_argument('--database-id', help='Override the default database ID')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose output')
    
    args = parser.parse_args()
    
    try:
        # Validate file exists before proceeding
        if not os.path.exists(args.file_path):
            console.print(Panel(
                f"[bold red]❌ File Not Found[/bold red]\n\n"
                f"[red]The specified file does not exist:[/red]\n"
                f"[bold]{args.file_path}[/bold]",
                title="[bold red]File Error",
                border_style="red"
            ))
            sys.exit(1)
        
        # Check if file is readable
        if not os.access(args.file_path, os.R_OK):
            console.print(Panel(
                f"[bold red]❌ File Not Readable[/bold red]\n\n"
                f"[red]Cannot read the specified file:[/red]\n"
                f"[bold]{args.file_path}[/bold]\n\n"
                f"Check file permissions and try again.",
                title="[bold red]Permission Error",
                border_style="red"
            ))
            sys.exit(1)
        
        # Show upload start
        console.print(Rule("[bold blue]Notion Uploader", style="blue"))
        
        # Initialize uploader with optional database override
        try:
            uploader = NotionUploader(
                verbose=args.verbose,
                database_id=args.database_id
            )
        except ValueError as e:
            if "NOTION_API_TOKEN" in str(e):
                console.print(Panel(
                    f"[bold red]❌ Missing API Token[/bold red]\n\n"
                    f"[red]The NOTION_API_TOKEN environment variable is not set.[/red]\n\n"
                    f"Please set it in your .env file or environment:\n"
                    f"[bold]export NOTION_API_TOKEN=\"your-token-here\"[/bold]",
                    title="[bold red]Configuration Error",
                    border_style="red"
                ))
            elif "NOTION_DATABASE_ID" in str(e):
                console.print(Panel(
                    f"[bold red]❌ Missing Database ID[/bold red]\n\n"
                    f"[red]The NOTION_DATABASE_ID environment variable is not set.[/red]\n\n"
                    f"Please set it in your .env file or environment:\n"
                    f"[bold]export NOTION_DATABASE_ID=\"your-database-id-here\"[/bold]",
                    title="[bold red]Configuration Error",
                    border_style="red"
                ))
            else:
                console.print(Panel(
                    f"[bold red]❌ Configuration Error[/bold red]\n\n"
                    f"[red]{str(e)}[/red]",
                    title="[bold red]Setup Error",
                    border_style="red"
                ))
            sys.exit(1)
        
        # Upload markdown (will automatically split if needed)
        results = uploader.upload_markdown(args.file_path, args.title)
        
        if len(results) == 1:
            # Single page upload
            page = results[0]
            page_title = args.title or os.path.basename(args.file_path).replace('.md', '')
            
            console.print(Panel(
                f"[bold green]✅ Notion Page Created Successfully![/bold green]\n\n"
                f"[bold]Title:[/bold] {page_title}\n"
                f"[bold]Page ID:[/bold] {page.get('id')}\n"
                f"[bold]URL:[/bold] {page.get('url')}\n"
                f"[bold]Database:[/bold] {uploader.database_id}",
                title="[bold blue]Single Page Created",
                border_style="green"
            ))
        else:
            # Multiple pages due to splitting
            table = Table(
                title="[bold blue]Multiple Pages Created", 
                show_header=True, 
                header_style="bold magenta"
            )
            table.add_column("Part", style="cyan", no_wrap=True)
            table.add_column("Title", style="green")
            table.add_column("Page ID", style="blue")
            table.add_column("Page URL", style="yellow")
            
            for i, page in enumerate(results):
                part_title = f"{args.title or 'Untitled'} - Part {i+1}" if len(results) > 1 else (args.title or 'Untitled')
                table.add_row(f"Part {i+1}", part_title, page.get('id'), page.get('url'))
            
            console.print(table)
            
            # Show summary panel
            console.print(Panel(
                f"[bold green]✅ Upload Successful![/bold green]\n\n"
                f"Content was automatically split into [bold cyan]{len(results)} parts[/bold cyan] "
                f"due to size limits.\n\n"
                f"Each part has [bold]≤ 100 blocks[/bold] and will render with "
                f"[bold]perfect rich text formatting[/bold] in Notion.\n\n"
                f"[bold]Original File:[/bold] {args.file_path}\n"
                f"[bold]Database:[/bold] {uploader.database_id}",
                title="[bold blue]Auto-Splitting Summary",
                border_style="blue"
            ))
        
    except FileNotFoundError as e:
        console.print(Panel(
            f"[bold red]❌ File Not Found[/bold red]\n\n"
            f"[red]{str(e)}[/red]",
            title="[bold red]File Error",
            border_style="red"
        ))
        sys.exit(1)
    except ValueError as e:
        console.print(Panel(
            f"[bold red]❌ Validation Error[/bold red]\n\n"
            f"[red]{str(e)}[/red]",
            title="[bold red]Input Error",
            border_style="red"
        ))
        sys.exit(1)
    except Exception as e:
        console.print(Panel(
            f"[bold red]❌ Upload Failed[/bold red]\n\n"
            f"[red]An unexpected error occurred:[/red]\n"
            f"[red]{str(e)}[/red]\n\n"
            f"Please check your configuration and try again.",
            title="[bold red]Unexpected Error",
            border_style="red"
        ))
        sys.exit(1)

if __name__ == "__main__":
    main() 