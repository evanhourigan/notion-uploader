import pytest
from notion_uploader.core import NotionUploader


class TestNotionUploader:
    """Test cases for NotionUploader class."""
    
    def test_parse_markdown_blocks_headers(self):
        """Test parsing markdown headers."""
        uploader = NotionUploader(api_token="test", database_id="test")
        
        markdown = "# Header 1\n## Header 2\n### Header 3"
        blocks = uploader.parse_markdown_blocks(markdown)
        
        assert len(blocks) == 3
        assert blocks[0]["type"] == "heading_1"
        assert blocks[1]["type"] == "heading_2"
        assert blocks[2]["type"] == "heading_3"
    
    def test_parse_markdown_blocks_paragraphs(self):
        """Test parsing markdown paragraphs."""
        uploader = NotionUploader(api_token="test", database_id="test")
        
        markdown = "This is a paragraph.\n\nThis is another paragraph."
        blocks = uploader.parse_markdown_blocks(markdown)
        
        assert len(blocks) == 2
        assert blocks[0]["type"] == "paragraph"
        assert blocks[1]["type"] == "paragraph"
    
    def test_parse_markdown_blocks_lists(self):
        """Test parsing markdown lists."""
        uploader = NotionUploader(api_token="test", database_id="test")
        
        markdown = "- Item 1\n- Item 2\n1. Numbered 1\n2. Numbered 2"
        blocks = uploader.parse_markdown_blocks(markdown)
        
        assert len(blocks) == 4
        assert blocks[0]["type"] == "bulleted_list_item"
        assert blocks[1]["type"] == "bulleted_list_item"
        assert blocks[2]["type"] == "numbered_list_item"
        assert blocks[3]["type"] == "numbered_list_item"
    
    def test_parse_markdown_blocks_code(self):
        """Test parsing markdown code blocks."""
        uploader = NotionUploader(api_token="test", database_id="test")
        
        markdown = "```python\ndef test():\n    return True\n```"
        blocks = uploader.parse_markdown_blocks(markdown)
        
        assert len(blocks) == 1
        assert blocks[0]["type"] == "code"
        assert "def test():" in blocks[0]["code"]["rich_text"][0]["text"]["content"] 