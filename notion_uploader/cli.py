#!/usr/bin/env python3

import argparse
import os
import sys
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from notion_uploader.core import NotionUploader

# Load environment variables from .env file in project directory
project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env_path = os.path.join(project_dir, '.env')
load_dotenv(env_path)

console = Console()

def main():
    parser = argparse.ArgumentParser(
        prog="notion-upload",
        description="Upload markdown files to Notion pages",
        epilog="Example: notion-upload document.md --title 'My Document'"
    )
    parser.add_argument("markdown_file", help="Path to the markdown file to upload")
    parser.add_argument("--title", required=True, help="Title for the Notion page")
    parser.add_argument("--database-id", help="Override the default database ID")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    # Validate Notion API credentials
    if not os.getenv("NOTION_API_TOKEN"):
        console.print(Panel(
            "[red]Error: NOTION_API_TOKEN environment variable not set[/red]\n"
            "Please set your Notion API token:\n"
            "export NOTION_API_TOKEN='your-notion-token-here'",
            title="Configuration Error",
            border_style="red"
        ))
        sys.exit(1)
    
    if not os.getenv("NOTION_DATABASE_ID") and not args.database_id:
        console.print(Panel(
            "[red]Error: NOTION_DATABASE_ID environment variable not set[/red]\n"
            "Please set your Notion database ID:\n"
            "export NOTION_DATABASE_ID='your-database-id-here'",
            title="Configuration Error",
            border_style="red"
        ))
        sys.exit(1)
    
    try:
        uploader = NotionUploader(
            database_id=args.database_id,
            verbose=args.verbose
        )
        
        page = uploader.upload_markdown(
            file_path=args.markdown_file,
            title=args.title
        )
        
        # Success message with page URL
        page_url = f"https://notion.so/{page['id'].replace('-', '')}"
        
        success_text = Text()
        success_text.append("✅ ", style="green")
        success_text.append("Notion page created successfully!\n\n", style="green")
        success_text.append("📄 ", style="blue")
        success_text.append(f"Title: {args.title}\n", style="blue")
        success_text.append("🔗 ", style="blue")
        success_text.append(f"URL: {page_url}\n", style="blue")
        success_text.append("📁 ", style="blue")
        success_text.append(f"Database: {uploader.database_id}", style="blue")
        
        console.print(Panel(
            success_text,
            title="Success",
            border_style="green"
        ))
        
    except FileNotFoundError as e:
        console.print(Panel(
            f"[red]Error: {str(e)}[/red]",
            title="File Not Found",
            border_style="red"
        ))
        sys.exit(1)
    except ValueError as e:
        console.print(Panel(
            f"[red]Error: {str(e)}[/red]",
            title="Configuration Error",
            border_style="red"
        ))
        sys.exit(1)
    except Exception as e:
        console.print(Panel(
            f"[red]Error: {str(e)}[/red]",
            title="Upload Failed",
            border_style="red"
        ))
        sys.exit(1)

if __name__ == "__main__":
    main() 