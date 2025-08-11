#!/bin/bash

# Create a global notion-upload wrapper

echo "Creating global notion-upload wrapper..."

# Create a directory for the module
mkdir -p ~/.local/lib/notion_uploader

# Copy the module files
cp -r notion_uploader/* ~/.local/lib/notion_uploader/

# Create the wrapper script
cat > ~/.local/bin/notion-upload << 'EOF'
#!/bin/bash

# Add the module path to Python path
export PYTHONPATH="$HOME/.local/lib:$PYTHONPATH"

# Get the project directory for .env file
PROJECT_DIR="$HOME/code/notion_uploader"

# Source the .env file to get environment variables
if [ -f "$PROJECT_DIR/.env" ]; then
    export $(grep -v '^#' "$PROJECT_DIR/.env" | xargs)
fi

# Run the CLI tool using the virtual environment Python
# The tool will handle .env loading internally
"$HOME/code/notion_uploader/.direnv/python-3.9/bin/python3" -m notion_uploader.cli "$@"
EOF

# Make it executable
chmod +x ~/.local/bin/notion-upload

echo "✅ Global notion-upload wrapper created!"
echo "You can now run 'notion-upload' from anywhere."
echo ""
echo "Make sure your Notion API credentials are set in ~/code/notion_uploader/.env"
