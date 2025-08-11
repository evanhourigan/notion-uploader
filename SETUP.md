# Setup Guide

This guide will help you set up the Notion Uploader tool.

## Prerequisites

- Python 3.9 or higher
- Poetry (recommended) or pip
- A Notion account with API access

## Installation

### 1. Install Dependencies

Using Poetry (recommended):

```bash
poetry install
```

Using pip:

```bash
pip install -r requirements.txt
```

### 2. Set Up Notion API

1. Go to [Notion Developers](https://developers.notion.com/)
2. Click "New integration"
3. Give your integration a name (e.g., "Markdown Uploader")
4. Select the workspace where you want to use it
5. Copy the "Internal Integration Token"

### 3. Create a Database

1. In your Notion workspace, create a new database
2. Share the database with your integration:
   - Click the "Share" button in the top right
   - Click "Invite" and search for your integration name
   - Select it and click "Invite"

### 4. Get Database ID

1. Open your database in Notion
2. Copy the database ID from the URL:
   - URL format: `https://notion.so/workspace/DATABASE_ID?v=...`
   - The database ID is the long string after the workspace name

### 5. Configure Environment Variables

Create a `.env` file in the project root:

```bash
cp env.example .env
```

Edit `.env` with your credentials:

```bash
NOTION_API_TOKEN=your-notion-token-here
NOTION_DATABASE_ID=your-database-id-here
```

## Testing

Test the installation with the sample document:

```bash
poetry run notion-upload sample-document.md --title "Test Document" --verbose
```

## Troubleshooting

### Common Issues

1. **"NOTION_API_TOKEN not set"**

   - Make sure you've created the `.env` file
   - Verify the token is correct

2. **"NOTION_DATABASE_ID not set"**

   - Check that you've copied the database ID correctly
   - Ensure the database is shared with your integration

3. **"Error creating Notion page"**
   - Verify your integration has access to the database
   - Check that the database ID is correct

### Getting Help

- Check the [Notion API documentation](https://developers.notion.com/)
- Review the [README.md](README.md) for usage examples
- Run `notion-upload --help` for command options
