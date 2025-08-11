#!/bin/bash

# Install notion-uploader CLI tool

echo "Installing notion-uploader CLI tool..."

# Check if Poetry is installed
if ! command -v poetry &> /dev/null; then
    echo "Poetry not found. Installing Poetry..."
    curl -sSL https://install.python-poetry.org | python3 -
fi

# Install dependencies using Poetry
echo "Installing dependencies..."
poetry install

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    if [ -f env.example ]; then
        echo "Creating .env file from example..."
        cp env.example .env
        echo "✅ Created .env file"
        echo "⚠️  Please edit .env and add your Notion API credentials"
    else
        echo "Creating .env file..."
        echo "NOTION_API_TOKEN=your-notion-token-here" > .env
        echo "NOTION_DATABASE_ID=your-database-id-here" >> .env
        echo "✅ Created .env file"
        echo "⚠️  Please edit .env and add your Notion API credentials"
    fi
else
    echo "✅ .env file already exists"
fi

# Create a simple wrapper script
cat > notion-upload << 'EOF'
#!/bin/bash
# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$SCRIPT_DIR"

# Run the CLI tool directly with Python
cd "$PROJECT_DIR" && python3 -m notion_uploader.cli "$@"
EOF

# Make the script executable
chmod +x notion-upload

# Move to a directory in PATH (if possible)
if [ -d "$HOME/.local/bin" ]; then
    mv notion-upload "$HOME/.local/bin/"
    echo "✅ CLI tool installed to $HOME/.local/bin/notion-upload"
    echo "You can now run: notion-upload --help"
elif [ -d "/usr/local/bin" ] && [ -w "/usr/local/bin" ]; then
    sudo mv notion-upload /usr/local/bin/
    echo "✅ CLI tool installed to /usr/local/bin/notion-upload"
    echo "You can now run: notion-upload --help"
else
    echo "✅ CLI script created in current directory"
    echo "You can run: ./notion-upload --help"
    echo "Or add current directory to PATH to use 'notion-upload' command"
fi

echo ""
echo "Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env and add your Notion API credentials"
echo "2. Run: notion-upload --help"
echo ""
echo "If you're using direnv, the environment will be automatically loaded."
echo "Otherwise, run: poetry shell"
