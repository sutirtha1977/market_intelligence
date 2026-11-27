
#!/bin/bash

# Stop if any command fails
set -e

echo "=================================="
echo " Git Add, Commit and Push"
echo "=================================="

# Add all changes
git add .

# Commit with today's date
git commit -m "Changes done on $(date +'%d %b %Y')"

# Push to remote repository
git push

echo "=================================="
echo " Git push completed successfully!"
echo "=================================="
