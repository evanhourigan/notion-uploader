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
  notion-upload large-file.md --title "Big Document" --dry-run
        """
    )
    
    parser.add_argument('file_path', help='Path to the markdown file to upload')
    parser.add_argument('--title', help='Title for the Notion page (optional)')
    parser.add_argument('--database-id', help='Override the default database ID')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose output')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be uploaded without actually uploading')
    
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
        
        # DRY RUN MODE: Show what would be uploaded without actually uploading
        if args.dry_run:
            console.print(Panel(
                "[bold yellow]🔍 DRY RUN MODE[/bold yellow]\n\n"
                "This will show you exactly what would be uploaded to Notion\n"
                "without making any API calls or creating any pages.",
                title="[bold blue]Dry Run Mode",
                border_style="yellow"
            ))
            
            # Load and parse the markdown file
            try:
                with open(args.file_path, 'r', encoding='utf-8') as f:
                    markdown_content = f.read()
            except Exception as e:
                console.print(Panel(
                    f"[bold red]❌ Failed to read file[/bold red]\n\n"
                    f"[red]Error reading {args.file_path}:[/red]\n"
                    f"[red]{str(e)}[/red]",
                    title="[bold red]File Read Error",
                    border_style="red"
                ))
                sys.exit(1)
            
            # Parse markdown into blocks
            console.print("📖 [bold]Parsing markdown file...[/bold]")
            blocks = uploader.parse_markdown_blocks(markdown_content)
            
            # Show parsing results
            console.print(Panel(
                f"[bold green]✅ Markdown parsed successfully![/bold green]\n\n"
                f"[bold]File:[/bold] {args.file_path}\n"
                f"[bold]Total blocks:[/bold] {len(blocks)}",
                title="[bold blue]Parsing Results",
                border_style="green"
            ))
            
            # Check if splitting would be needed
            if len(blocks) > 100:
                console.print(Panel(
                    f"[bold yellow]⚠️  Content would be auto-split[/bold yellow]\n\n"
                    f"Your content has [bold]{len(blocks)} blocks[/bold], which exceeds "
                    f"Notion's limit of 100 blocks per page.\n\n"
                    f"The tool would automatically split this into "
                    f"[bold]{uploader._split_blocks_for_notion(blocks).__len__()} pages[/bold] "
                    f"to maintain proper formatting and speaker continuity.",
                    title="[bold blue]Auto-Splitting Preview",
                    border_style="yellow"
                ))
            
            # Show sample blocks (first 3 and last 3)
            console.print("📋 [bold]Sample blocks that would be uploaded:[/bold]")
            
            sample_blocks = []
            if len(blocks) <= 6:
                sample_blocks = blocks
            else:
                sample_blocks = blocks[:3] + [{"object": "block", "type": "divider", "divider": {}}] + blocks[-3:]
            
            for i, block in enumerate(sample_blocks):
                if block.get("type") == "divider":
                    console.print("   ... [dim](showing middle blocks)[/dim] ...")
                    continue
                    
                block_type = block.get("type", "unknown")
                if block_type == "heading_1":
                    console.print(f"   [bold blue]# {block[block_type]['rich_text'][0]['text']['content']}[/bold blue]")
                elif block_type == "heading_2":
                    console.print(f"   [bold blue]## {block[block_type]['rich_text'][0]['text']['content']}[/bold blue]")
                elif block_type == "heading_3":
                    console.print(f"   [bold blue]### {block[block_type]['rich_text'][0]['text']['content']}[/bold blue]")
                elif block_type == "bulleted_list_item":
                    content = block[block_type]['rich_text'][0]['text']['content']
                    console.print(f"   [green]• {content}[/green]")
                elif block_type == "numbered_list_item":
                    content = block[block_type]['rich_text'][0]['text']['content']
                    console.print(f"   [green]1. {content}[/green]")
                elif block_type == "paragraph":
                    content = block[block_type]['rich_text'][0]['text']['content']
                    if len(content) > 80:
                        content = content[:80] + "..."
                    console.print(f"   {content}")
                else:
                    console.print(f"   [dim]{block_type}: {str(block)[:60]}...[/dim]")
            
            if len(blocks) > 6:
                console.print(f"\n[dim]... and {len(blocks) - 6} more blocks[/dim]")
            
            # Show final summary
            console.print(Panel(
                f"[bold green]✅ Dry run completed successfully![/bold green]\n\n"
                f"Your markdown file is ready for upload.\n"
                f"Run without [bold]--dry-run[/bold] to actually upload to Notion.",
                title="[bold blue]Dry Run Summary",
                border_style="green"
            ))
            
            return  # Exit early, don't proceed to actual upload
        
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