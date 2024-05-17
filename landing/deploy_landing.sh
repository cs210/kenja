#!/bin/bash

# Define the source files
FILES=("favicon.ico" "index.html" "style.css")

# Define the destination directory
DEST_DIR="/usr/share/nginx/landing"

# Check if the destination directory exists
if [ ! -d "$DEST_DIR" ]; then
    echo "Destination directory $DEST_DIR does not exist. Creating it now."
    sudo mkdir -p "$DEST_DIR"
fi

# Copy each file to the destination directory
for FILE in "${FILES[@]}"; do
    if [ -f "$FILE" ]; then
        echo "Copying $FILE to $DEST_DIR"
        sudo cp "$FILE" "$DEST_DIR"
    else
        echo "File $FILE does not exist. Skipping."
    fi
done

echo "All specified files have been copied."