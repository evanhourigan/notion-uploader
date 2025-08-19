# Notion Uploader

A CLI tool for uploading markdown files to Notion pages using the Notion API.

## Overview

This tool takes markdown files and uploads them as structured pages to a Notion database. It supports:

- Converting markdown to Notion blocks
- Preserving formatting and structure
- Setting custom page titles
- Rich console output with progress indicators
- Error handling and validation

## Installation

### Using Poetry (Recommended)

```bash
# Install dependencies
poetry install

# Install the CLI tool
poetry install
```

### Using pip

```bash
pip install -r requirements.txt
```

## Setup

### Environment Variables

1. **Using direnv (Recommended)**:

   ```bash
   # Install direnv if you haven't already
   brew install direnv  # macOS
   # or: sudo apt-get install direnv  # Ubuntu/Debian

   # Copy the example environment file
   cp env.example .env

   # Edit .env with your Notion API credentials
   nano .env
   ```

2. **Using environment variables directly**:

   ```bash
   export NOTION_API_TOKEN="your-notion-token-here"
   export NOTION_DATABASE_ID="your-database-id-here"
   ```

3. **Using a .env file manually**:
   ```bash
   # Create .env file
   echo "NOTION_API_TOKEN=your-notion-token-here" > .env
   echo "NOTION_DATABASE_ID=your-database-id-here" >> .env
   ```

### Getting Notion API Credentials

1. Go to [Notion Developers](https://developers.notion.com/)
2. Create a new integration
3. Copy the "Internal Integration Token"
4. Share your database with the integration
5. Copy the database ID from the database URL

### Virtual Environment

The project uses Poetry for dependency management and direnv for environment management:

```bash
# Install Poetry if you haven't already
curl -sSL https://install.python-poetry.org | python3 -

# Install dependencies and activate virtual environment
poetry install

# Or if you prefer pip:
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Usage

### Basic Usage

```bash
# Upload a markdown file to Notion
notion-upload path/to/file.md --title "My Page Title"
```

The tool will:

1. Load the specified markdown file
2. Convert markdown to Notion blocks
3. Create a new page in your Notion database
4. Display the page URL

### Command Line Options

```bash
notion-upload --help
```

Available options:

- `markdown_file`: Path to the markdown file to upload
- `--title`: Title for the Notion page (required)
- `--database-id`: Override the default database ID
- `--verbose`: Enable verbose output

### Examples

```bash
# Upload a blog post
notion-upload blog-post.md --title "My Blog Post"

# Upload with custom database
notion-upload notes.md --title "Meeting Notes" --database-id "custom-db-id"

# Verbose output
notion-upload document.md --title "Document" --verbose
```

## Workflow Integration

This tool is designed to work as part of a larger content management workflow:

1. **Create Content**: Write markdown files locally
2. **Upload to Notion**: Use this tool to upload to your Notion workspace
3. **Collaborate**: Share and collaborate on the uploaded content

Example workflow:

```bash
# Step 1: Create markdown content
echo "# My Notes\n\nSome content here" > notes.md

# Step 2: Upload to Notion
notion-upload notes.md --title "My Notes"

# Step 3: Share the page URL with your team
```

## Supported Markdown Features

The tool converts the following markdown elements to Notion blocks:

| Markdown Syntax | Notion Block Type    | Features             | Limitations                  |
| --------------- | -------------------- | -------------------- | ---------------------------- |
| `# Heading`     | `heading_1`          | Rich text formatting | Max 3 levels (h1, h2, h3)    |
| `## Heading`    | `heading_2`          | Rich text formatting | Notion caps at h3            |
| `### Heading`   | `heading_3`          | Rich text formatting | Deeper levels become h3      |
| `**text**`      | `paragraph`          | Bold formatting      | Inline within any text block |
| `*text*`        | `paragraph`          | Italic formatting    | Inline within any text block |
| `` `code` ``    | `paragraph`          | Code formatting      | Inline within any text block |
| `- Item`        | `bulleted_list_item` | Rich text formatting | Nested lists supported       |
| `1. Item`       | `numbered_list_item` | Rich text formatting | Nested lists supported       |
| Regular text    | `paragraph`          | Rich text formatting | Auto-split if >1800 chars    |
| Code blocks     | `code`               | Language detection   | Preserves formatting         |

### Rich Text Formatting

All text blocks support inline formatting:

- **Bold**: `**text**` → Bold text
- **Italic**: `*text*` → Italic text
- **Code**: `` `code` `` → Inline code
- **Mixed**: ` **Bold** and *italic* with ``  `code` `` → Mixed formatting

## Error Handling & Exit Codes

The tool provides comprehensive error handling with specific exit codes:

| Error Type          | Exit Code | Description                        | Common Causes             |
| ------------------- | --------- | ---------------------------------- | ------------------------- |
| **File Errors**     | `1`       | File not found or unreadable       | Invalid path, permissions |
| **Configuration**   | `1`       | Missing API token or database ID   | `.env` not set up         |
| **Authentication**  | `1`       | Invalid or expired API token       | Token revoked, expired    |
| **Database Access** | `1`       | Database not found or inaccessible | Wrong ID, no permissions  |
| **API Rate Limits** | `1`       | Too many requests                  | Hit Notion API limits     |
| **Content Limits**  | `1`       | Content too large                  | >100 blocks, >2000 chars  |
| **Network Issues**  | `1`       | Connection failures                | Internet, Notion API down |
| **Validation**      | `1`       | Invalid content structure          | Malformed markdown        |

### Automatic Content Splitting

When content exceeds Notion's limits, the tool automatically splits it:

- **Block Limit**: >100 blocks → Multiple pages (≤100 blocks each)
- **Character Limit**: >2000 chars → Multiple blocks (≤1800 chars each)
- **Speaker Continuity**: Preserves speaker labels with their content
- **Smart Splitting**: Splits at optimal boundaries (end of content, before new speakers)

## Configuration

The tool uses the following default settings:

- **API Endpoint**: Notion API v1
- **Block Types**: Automatically detected from markdown
- **Error Handling**: Graceful failure with helpful error messages

## Development

```bash
# Install development dependencies
poetry install

# Run tests (when implemented)
poetry run pytest

# Build the package
poetry build

# Format code
poetry run black notion_uploader/
poetry run isort notion_uploader/

# Lint code
poetry run flake8 notion_uploader/
```

## License

MIT License
