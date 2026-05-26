#!/usr/bin/env bash
# Push apix to github.com/allenunrau/apix
# Usage: ./push_to_github.sh [TOKEN]

set -e

TOKEN="${1:-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}"

echo "🚀 Pushing apix to github.com/allenunrau/apix..."

DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

git init -b main
git config user.email "allenunrau@users.noreply.github.com"
git config user.name "Allen Unrau"
git add -A
git commit -m "Initial commit: apix - CLI utility for working with APIs"
git remote add origin "https://allenunrau:${TOKEN}@github.com/allenunrau/apix.git"
git push -u origin main

echo "✅ Done! https://github.com/allenunrau/apix"