#!/bin/bash

# Run the HTML to Hugo conversion
python html_to_hugo.py

# Navigate to Hugo site directory
cd hugo_site

# Initialize Hugo modules if needed
hugo mod init github.com/yourusername/screening-tools-hugo

# Start Hugo server
echo "Starting Hugo server..."
hugo server -D
