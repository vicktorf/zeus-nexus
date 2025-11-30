#!/bin/bash

# Zeus Nexus GitHub Repository Setup Script

set -e

NAMESPACE="ac-agentic"
GITHUB_REPO="https://github.com/dungpv30/zeus-nexus.git"
PROJECT_NAME="zeus-nexus"

echo "📚 Setting up Zeus Nexus repository on GitHub..."

# Check if git is initialized and committed
if [ ! -d ".git" ]; then
    echo "🔧 Initializing Git repository..."
    git init
    git config user.email "dungpv30@fpt.com"
    git config user.name "dungpv30"
    git branch -m main
    git add .
    git commit -m "Initial Zeus Nexus commit - AI Pantheon as a Service"
fi

echo ""
echo "📋 GitHub Repository Setup Instructions:"
echo "========================================="
echo ""
echo "1. 🌐 Go to: https://github.com/new"
echo "2. 📝 Repository name: zeus-nexus"
echo "3. 📄 Description: Zeus Nexus - AI Pantheon as a Service"
echo "4. 🔓 Make it Public"
echo "5. ❌ Do NOT initialize with README (we have code already)"
echo ""
echo "6. � After creating repo, run these commands:"
echo "   cd /root/zeus-nexus"
echo "   git remote add origin https://github.com/YOUR_USERNAME/zeus-nexus.git"
echo "   git push -u origin main"
echo ""
echo "🏗️ BuildConfig is already configured for GitHub:"
echo "   Repository: $GITHUB_REPO"
echo "   Context Dir: docker/"
echo "   Dockerfile: Dockerfile.zeus-core"
echo ""
echo "🚀 After pushing to GitHub, trigger the build:"
echo "   oc start-build zeus-core -n $NAMESPACE --follow"
echo ""

# Update README with correct GitHub URL
echo "📝 Updating documentation with GitHub URLs..."

echo "✅ Ready to push to GitHub! Follow the instructions above."