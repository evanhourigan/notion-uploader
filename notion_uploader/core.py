import os
import re
from typing import List, Dict, Any, Optional
from notion_client import Client
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

class NotionUploader:
    """Uploads markdown files to Notion pages with proper block conversion."""
    
    def __init__(self, api_token: Optional[str] = None, database_id: Optional[str] = None, verbose: bool = False):
        self.console = Console()
        self.verbose = verbose
        
        # Load configuration from environment variables with defaults
        self.api_token = api_token or os.getenv("NOTION_API_TOKEN")
        self.database_id = database_id or os.getenv("NOTION_DATABASE_ID")
        
        if not self.api_token:
            raise ValueError("NOTION_API_TOKEN environment variable not set")
        if not self.database_id:
            raise ValueError("NOTION_DATABASE_ID environment variable not set")
        
        # Initialize Notion client
        self.client = Client(auth=self.api_token)
    
    def load_markdown(self, file_path: str) -> str:
        """Load markdown content from file."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            raise FileNotFoundError(f"Markdown file not found: {file_path}")
        except Exception as e:
            raise Exception(f"Error reading markdown file: {str(e)}")
    
    def parse_markdown_blocks(self, markdown_content: str) -> List[Dict[str, Any]]:
        """Parse markdown content into Notion blocks."""
        blocks = []
        lines = markdown_content.split('\n')
        i = 0
        
        while i < len(lines):
            line = lines[i].strip()
            
            if not line:
                i += 1
                continue
            
            # Handle headers
            if line.startswith('#'):
                level = len(line) - len(line.lstrip('#'))
                if level > 3:
                    level = 3  # Notion supports up to 3 heading levels
                
                text = line.lstrip('#').strip()
                blocks.append({
                    "object": "block",
                    "type": f"heading_{level}",
                    f"heading_{level}": {
                        "rich_text": [{"type": "text", "text": {"content": text}}]
                    }
                })
            
            # Handle code blocks
            elif line.startswith('```'):
                code_lines = []
                i += 1
                while i < len(lines) and not lines[i].strip().startswith('```'):
                    code_lines.append(lines[i])
                    i += 1
                
                if code_lines:
                    code_content = '\n'.join(code_lines)
                    blocks.append({
                        "object": "block",
                        "type": "code",
                        "code": {
                            "rich_text": [{"type": "text", "text": {"content": code_content}}],
                            "language": "plain text"
                        }
                    })
            
            # Handle bullet lists
            elif line.startswith('- ') or line.startswith('* '):
                list_items = []
                while i < len(lines) and (lines[i].strip().startswith('- ') or lines[i].strip().startswith('* ')):
                    item_text = lines[i].strip()[2:].strip()
                    list_items.append(item_text)
                    i += 1
                i -= 1  # Go back one line since we'll increment at the end
                
                for item in list_items:
                    blocks.append({
                        "object": "block",
                        "type": "bulleted_list_item",
                        "bulleted_list_item": {
                            "rich_text": [{"type": "text", "text": {"content": item}}]
                        }
                    })
            
            # Handle numbered lists
            elif re.match(r'^\d+\.\s', line):
                list_items = []
                while i < len(lines) and re.match(r'^\d+\.\s', lines[i].strip()):
                    item_text = re.sub(r'^\d+\.\s', '', lines[i].strip())
                    list_items.append(item_text)
                    i += 1
                i -= 1  # Go back one line since we'll increment at the end
                
                for item in list_items:
                    blocks.append({
                        "object": "block",
                        "type": "numbered_list_item",
                        "numbered_list_item": {
                            "rich_text": [{"type": "text", "text": {"content": item}}]
                        }
                    })
            
            # Handle paragraphs (default)
            else:
                # Collect consecutive non-empty lines as a paragraph
                paragraph_lines = []
                while i < len(lines) and lines[i].strip() and not lines[i].strip().startswith(('#', '- ', '* ', '```')) and not re.match(r'^\d+\.\s', lines[i].strip()):
                    paragraph_lines.append(lines[i].strip())
                    i += 1
                i -= 1  # Go back one line since we'll increment at the end
                
                if paragraph_lines:
                    paragraph_text = ' '.join(paragraph_lines)
                    blocks.append({
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [{"type": "text", "text": {"content": paragraph_text}}]
                        }
                    })
            
            i += 1
        
        return blocks
    
    def create_notion_page(self, title: str, blocks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create a new Notion page with the given title and blocks."""
        try:
            page = self.client.pages.create(
                parent={"database_id": self.database_id},
                properties={
                    "Name": {"title": [{"type": "text", "text": {"content": title}}]}
                },
                children=blocks
            )
            return page
        except Exception as e:
            raise Exception(f"Error creating Notion page: {str(e)}")
    
    def upload_markdown(self, file_path: str, title: str) -> Dict[str, Any]:
        """Upload markdown file to Notion as a new page."""
        # Load markdown content
        if self.verbose:
            self.console.print(f"📖 Loading markdown from: {file_path}")
        markdown_content = self.load_markdown(file_path)
        
        # Parse markdown into blocks
        if self.verbose:
            self.console.print(f"🔄 Converting markdown to Notion blocks...")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
            transient=True
        ) as progress:
            task = progress.add_task("Converting markdown...", total=None)
            blocks = self.parse_markdown_blocks(markdown_content)
        
        # Create Notion page
        if self.verbose:
            self.console.print(f"📝 Creating Notion page...")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
            transient=True
        ) as progress:
            task = progress.add_task("Creating page...", total=None)
            page = self.create_notion_page(title, blocks)
        
        return page 