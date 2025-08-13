#!/usr/bin/env python3

import os
import re
import requests
from typing import List, Dict, Any
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.panel import Panel

class NotionUploader:
    def __init__(self, verbose: bool = False, database_id: str = None):
        """Initialize the Notion uploader."""
        self.notion_token = os.getenv('NOTION_API_TOKEN')
        self.database_id = database_id or os.getenv('NOTION_DATABASE_ID')
        self.verbose = verbose
        self.console = Console()
        
        if not self.notion_token:
            raise ValueError("NOTION_API_TOKEN environment variable is required")
        if not self.database_id:
            raise ValueError("NOTION_DATABASE_ID environment variable is required")
    
    def load_markdown(self, file_path: str) -> str:
        """Load markdown content from file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return content
        except FileNotFoundError:
            raise FileNotFoundError(f"Markdown file not found: {file_path}")
        except Exception as e:
            raise Exception(f"Error reading file {file_path}: {str(e)}")
    
    def _parse_inline_formatting(self, text: str) -> List[Dict[str, Any]]:
        """Parse inline markdown formatting (bold, italic, code) into Notion rich text objects."""
        rich_text = []
        i = 0
        
        while i < len(text):
            # Handle bold text: **text**
            if text[i:i+2] == '**' and i + 2 < len(text):
                end_bold = text.find('**', i + 2)
                if end_bold != -1:
                    rich_text.append({
                        "type": "text",
                        "text": {"content": text[i+2:end_bold]},
                        "annotations": {"bold": True}
                    })
                    i = end_bold + 2
                    continue
            
            # Handle italic text: *text*
            elif text[i] == '*' and i + 1 < len(text):
                end_italic = text.find('*', i + 1)
                if end_italic != -1:
                    rich_text.append({
                        "type": "text",
                        "text": {"content": text[i+1:end_italic]},
                        "annotations": {"italic": True}
                    })
                    i = end_italic + 1
                    continue
            
            # Handle code: `text`
            elif text[i] == '`' and i + 1 < len(text):
                end_code = text.find('`', i + 1)
                if end_code != -1:
                    rich_text.append({
                        "type": "text",
                        "text": {"content": text[i+1:end_code]},
                        "annotations": {"code": True}
                    })
                    i = end_code + 1
                    continue
            
            # Regular text
            else:
                # Find the next special character
                next_special = len(text)
                for special in ['**', '*', '`']:
                    pos = text.find(special, i)
                    if pos != -1 and pos < next_special:
                        next_special = pos
                
                if next_special == len(text):
                    # No more special characters, add remaining text
                    if text[i:].strip():
                        rich_text.append({
                            "type": "text",
                            "text": {"content": text[i:]}
                        })
                    break
                else:
                    # Add text up to next special character
                    if text[i:next_special].strip():
                        rich_text.append({
                            "type": "text",
                            "text": {"content": text[i:next_special]}
                        })
                    i = next_special
        
        return rich_text if rich_text else [{"type": "text", "text": {"content": text}}]
    
    def _split_long_text_at_sentences(self, text: str, max_chars: int = 1800) -> List[str]:
        """Split long text at sentence boundaries to stay under character limits."""
        if len(text) <= max_chars:
            return [text]
        
        # Look for sentence endings
        sentence_endings = ['. ', '! ', '? ', '.\n', '!\n', '?\n']
        sentences = []
        current_pos = 0
        
        for i in range(len(text)):
            if i < len(text) - 1:  # Not the last character
                # Check if this position starts a sentence ending
                for ending in sentence_endings:
                    if text[i:i+len(ending)] == ending:
                        # Found sentence ending
                        sentence = text[current_pos:i+1].strip()
                        if sentence:
                            sentences.append(sentence)
                        current_pos = i + len(ending)
                        break
        
        # Add the last sentence (if any)
        if current_pos < len(text):
            last_sentence = text[current_pos:].strip()
            if last_sentence:
                sentences.append(last_sentence)
        
        # If no sentences were found, split by length as fallback
        if not sentences:
            sentences = [text]
        
        # Now combine sentences into chunks that fit within limits
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk) + len(sentence) + 1 > max_chars:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = sentence
                else:
                    # Single sentence is too long, just add it
                    chunks.append(sentence)
            else:
                if current_chunk:
                    current_chunk += " " + sentence
                else:
                    current_chunk = sentence
        
        # Add the last chunk if there's content
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def parse_markdown_blocks(self, markdown_content: str) -> List[Dict[str, Any]]:
        """Parse markdown content into Notion blocks."""
        blocks = []
        lines = markdown_content.split('\n')
        
        # Show progress for large markdown files
        if len(lines) > 100 and not self.verbose:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                console=self.console
            ) as progress:
                task = progress.add_task("Parsing markdown blocks...", total=len(lines))
                
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                    
                    # Parse the line into blocks
                    self._parse_line_to_blocks(line, blocks)
                    progress.advance(task)
        else:
            # For smaller files or verbose mode, parse without progress bar
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Parse the line into blocks
                self._parse_line_to_blocks(line, blocks)
        
        return blocks
    
    def _split_blocks_for_notion(self, blocks: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
        """Split blocks into chunks that respect speaker boundaries and stay under 100 blocks."""
        chunks = []
        current_chunk = []
        
        # Show progress for large block lists
        if len(blocks) > 200 and not self.verbose:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                console=self.console
            ) as progress:
                task = progress.add_task("Splitting blocks for optimal page size...", total=len(blocks))
                
                for i, block in enumerate(blocks):
                    current_chunk.append(block)
                    
                    # Check if we need to split
                    if len(current_chunk) >= 100:
                        # Find optimal split point
                        optimal_split = self._find_optimal_split_point(blocks, 0, 100)
                        
                        # Split at the optimal point
                        if optimal_split < len(current_chunk):
                            # Create chunk up to optimal split point
                            chunk = current_chunk[:optimal_split]
                            chunks.append(chunk)
                            
                            # Start new chunk from optimal split point
                            current_chunk = current_chunk[optimal_split:]
                        else:
                            # No good split point found, use current chunk
                            chunks.append(current_chunk)
                            current_chunk = []
                    
                    progress.advance(task)
                
                # Add any remaining blocks
                if current_chunk:
                    chunks.append(current_chunk)
        else:
            # For smaller block lists or verbose mode, split without progress bar
            for i, block in enumerate(blocks):
                current_chunk.append(block)
                
                # Check if we need to split
                if len(current_chunk) >= 100:
                    # Find optimal split point
                    optimal_split = self._find_optimal_split_point(blocks, 0, 100)
                    
                    # Split at the optimal point
                    if optimal_split < len(current_chunk):
                        # Create chunk up to optimal split point
                        chunk = current_chunk[:optimal_split]
                        chunks.append(chunk)
                        
                        # Start new chunk from optimal split point
                        current_chunk = current_chunk[optimal_split:]
                    else:
                        # No good split point found, use current chunk
                        chunks.append(current_chunk)
                        current_chunk = []
            
            # Add any remaining blocks
            if current_chunk:
                chunks.append(current_chunk)
        
        return chunks
    
    def _is_optimal_split_point(self, blocks: List[Dict[str, Any]], pos: int) -> bool:
        """
        Check if a position is an optimal split point.
        Returns True if splitting here keeps speaker turns together.
        """
        if pos >= len(blocks):
            return False
        
        current_block = blocks[pos]
        
        # If this is a heading, it's a great split point
        if current_block.get('type', '').startswith('heading'):
            return True
        
        # If this is a paragraph, analyze the content
        if current_block.get('type') == 'paragraph':
            content = current_block['paragraph']['rich_text'][0]['text']['content']
            
            # Check if this looks like a speaker label
            is_speaker_label = 'SPEAKER' in content and ':' in content
            
            if is_speaker_label:
                # Speaker labels are BAD split points!
                # We want to keep the speaker label with their content
                return False
            
            # If this is content (not a speaker label), check what comes next
            if pos + 1 < len(blocks):
                next_block = blocks[pos + 1]
                if next_block.get('type') == 'paragraph':
                    next_content = next_block['paragraph']['rich_text'][0]['text']['content']
                    
                    # If next block is a speaker label, this is a PERFECT split point
                    # because we're ending content before a new speaker begins
                    if 'SPEAKER' in next_content and ':' in next_content:
                        return True
            
            # If this is the last block, it's always a good split point
            if pos == len(blocks) - 1:
                return True
        
        return False
    
    def _find_optimal_split_point(self, blocks: List[Dict[str, Any]], start_pos: int, target_end: int) -> int:
        """
        Find the optimal split point that keeps speaker turns together.
        Returns the best position to split without breaking speaker continuity.
        """
        # Start from the target end and work backwards to find the best split
        best_split_pos = target_end
        
        # Look within a reasonable range around the target
        # Look back further to find better split points
        search_start = max(start_pos, target_end - 50)  # Look back up to 50 blocks
        search_end = min(len(blocks), target_end + 10)  # Look forward up to 10 blocks
        
        # Instead of taking the first good split point, find the one closest to target_end
        # that still respects speaker boundaries
        for pos in range(search_start, search_end):
            if pos <= start_pos:
                continue
                
            # Check if this is a good split point
            if self._is_optimal_split_point(blocks, pos):
                # Update best_split_pos only if this position is closer to target_end
                # This ensures we maximize page utilization
                if abs(pos - target_end) < abs(best_split_pos - target_end):
                    best_split_pos = pos
        
        # CRITICAL FIX: If we're splitting at content that precedes a speaker label,
        # we need to split BEFORE that content, not at it
        if best_split_pos < len(blocks):
            current_block = blocks[best_split_pos]
            if current_block.get('type') == 'paragraph':
                content = current_block['paragraph']['rich_text'][0]['text']['content']
                
                # If this is content (not a speaker label), check what comes next
                if 'SPEAKER' not in content or ':' not in content:
                    if best_split_pos + 1 < len(blocks):
                        next_block = blocks[best_split_pos + 1]
                        if next_block.get('type') == 'paragraph':
                            next_content = next_block['paragraph']['rich_text'][0]['text']['content']
                            
                            # If next block is a speaker label, we should split BEFORE this content
                            if 'SPEAKER' in next_content and ':' in next_content:
                                # Split at the previous block instead
                                best_split_pos = max(start_pos, best_split_pos - 1)
        
        return best_split_pos
    
    def _parse_line_to_blocks(self, line: str, blocks: List[Dict[str, Any]]) -> None:
        """Parse a single line into Notion blocks and add them to the blocks list."""
        # Handle headings
        if line.startswith('#'):
            level = len(line) - len(line.lstrip('#'))
            if level > 3:
                level = 3  # Notion only supports h1, h2, h3
            
            heading_text = line.lstrip('#').strip()
            rich_text = self._parse_inline_formatting(heading_text)
            
            blocks.append({
                "object": "block",
                "type": f"heading_{level}",
                f"heading_{level}": {
                    "rich_text": rich_text
                }
            })
        
        # Handle bulleted lists
        elif line.startswith('- ') or line.startswith('* '):
            list_text = line[2:].strip()
            rich_text = self._parse_inline_formatting(list_text)
            
            blocks.append({
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": rich_text
                }
            })
        
        # Handle nested bulleted lists (indented with spaces)
        elif re.match(r'^\s+[-*]\s', line):
            # Remove leading spaces and bullet marker
            list_text = re.sub(r'^\s+[-*]\s+', '', line)
            rich_text = self._parse_inline_formatting(list_text)
            
            blocks.append({
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": rich_text
                }
            })
        
        # Handle numbered lists
        elif re.match(r'^\d+\.\s', line):
            list_text = re.sub(r'^\d+\.\s', '', line)
            rich_text = self._parse_inline_formatting(list_text)
            
            blocks.append({
                "object": "block",
                "type": "numbered_list_item",
                "numbered_list_item": {
                    "rich_text": rich_text
                }
            })
        
        # Handle paragraphs (everything else)
        else:
            # Check if this text is too long and needs splitting
            if len(line) > 1800:  # Leave buffer under Notion's 2000 limit
                if self.verbose:
                    print(f"📏 Splitting long paragraph ({len(line)} chars) at sentence boundaries...")
                
                # Split the long text
                text_chunks = self._split_long_text_at_sentences(line)
                
                # Create a block for each chunk
                for chunk in text_chunks:
                    rich_text = self._parse_inline_formatting(chunk)
                    blocks.append({
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": rich_text
                        }
                    })
            else:
                # Text fits in one block
                rich_text = self._parse_inline_formatting(line)
                blocks.append({
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": rich_text
                    }
                })
    
    def create_notion_page(self, title: str, blocks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create a Notion page with the given blocks."""
        if self.verbose:
            self.console.print(f"📝 [bold green]Creating Notion page...[/bold green]")
        
        # Show progress for large blocks
        if len(blocks) > 50 and not self.verbose:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                console=self.console
            ) as progress:
                task = progress.add_task("Creating Notion page...", total=len(blocks))
                
                # Create the page structure
                page_data = {
                    "parent": {"database_id": self.database_id},
                    "properties": {
                        "title": {
                            "title": [
                                {
                                    "text": {
                                        "content": title
                                    }
                                }
                            ]
                        }
                    },
                    "children": blocks
                }
                
                # Make the API call
                response = requests.post(
                    'https://api.notion.com/v1/pages',
                    headers={
                        'Authorization': f'Bearer {self.notion_token}',
                        'Notion-Version': '2022-06-28',
                        'Content-Type': 'application/json'
                    },
                    json=page_data
                )
                
                progress.advance(task)
                
                if response.status_code != 200:
                    raise Exception(f"Failed to create Notion page: {response.text}")
                
                return response.json()
        else:
            # For smaller blocks or verbose mode, create without progress bar
            page_data = {
                "parent": {"database_id": self.database_id},
                "properties": {
                    "title": {
                        "title": [
                            {
                                "text": {
                                    "content": title
                                }
                            }
                        ]
                    }
                },
                "children": blocks
            }
            
            # Make the API call
            response = requests.post(
                'https://api.notion.com/v1/pages',
                headers={
                    'Authorization': f'Bearer {self.notion_token}',
                    'Notion-Version': '2022-06-28',
                    'Content-Type': 'application/json'
                },
                json=page_data
            )
            
            if response.status_code != 200:
                raise Exception(f"Failed to create Notion page: {response.text}")
            
            if self.verbose:
                self.console.print(Panel(
                    f"[bold green]✅ Notion Page Created Successfully![/bold green]\n\n"
                    f"[bold]Title:[/bold] {title}\n"
                    f"[bold]Blocks:[/bold] {len(blocks)}\n"
                    f"[bold]Database:[/bold] {self.database_id}\n"
                    f"[bold]Status:[/bold] Ready for content",
                    title="[bold blue]Page Creation Complete",
                    border_style="green"
                ))
            
            return response.json()
    
    def upload_markdown(self, file_path: str, title: str = None) -> List[Dict[str, Any]]:
        """Upload markdown file to Notion, automatically splitting if needed."""
        if self.verbose:
            self.console.print(f"📖 [bold blue]Loading markdown from:[/bold blue] {file_path}")
        
        # Load markdown content
        markdown_content = self.load_markdown(file_path)
        
        if self.verbose:
            self.console.print("🔄 [bold yellow]Converting markdown to Notion blocks...[/bold yellow]")
        
        # Parse markdown into blocks
        blocks = self.parse_markdown_blocks(markdown_content)
        
        if self.verbose:
            self.console.print(Panel(
                f"[bold green]📊 Created {len(blocks)} blocks[/bold green]",
                title="[bold blue]Parsing Complete",
                border_style="green"
            ))
        
        # Check if we need to split due to block limits
        if len(blocks) > 100:
            if self.verbose:
                self.console.print(Panel(
                    f"[bold yellow]📄 Content needs splitting[/bold yellow]\n\n"
                    f"Current: [bold red]{len(blocks)} blocks[/bold red]\n"
                    f"Limit: [bold green]100 blocks[/bold green]",
                    title="[bold blue]Size Check",
                    border_style="yellow"
                ))
            
            # Split blocks into chunks
            chunks = self._split_blocks_for_notion(blocks)
            
            if self.verbose:
                chunk_info = "\n".join([f"   [cyan]Chunk {i+1}:[/cyan] {len(chunk)} blocks" for i, chunk in enumerate(chunks)])
                self.console.print(Panel(
                    f"[bold blue]📄 Split {len(blocks)} blocks into {len(chunks)} chunks[/bold blue]\n\n{chunk_info}",
                    title="[bold blue]Splitting Complete",
                    border_style="blue"
                ))
            
            # Upload each chunk
            results = []
            for i, chunk in enumerate(chunks):
                if self.verbose:
                    self.console.print(f"📤 [bold green]Uploading Part {i+1}[/bold green] ([cyan]{len(chunk)} blocks[/cyan])...")
                
                # Create title for this part
                part_title = f"{title or 'Untitled'} - Part {i+1}" if len(chunks) > 1 else (title or 'Untitled')
                
                # Upload the chunk
                page = self.create_notion_page(part_title, chunk)
                results.append(page)
            
            return results
        else:
            # Single page upload
            if self.verbose:
                self.console.print("📝 [bold green]Creating Notion page...[/bold green]")
            
            page = self.create_notion_page(title or 'Untitled', blocks)
            return [page] 