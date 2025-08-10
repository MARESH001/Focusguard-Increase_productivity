#!/bin/bash

# FocusGuard Deployment Script
echo "🚀 FocusGuard Deployment Script"
echo "================================"

# Check if we're in the right directory
if [ ! -f "Focusguard-Increase_productivity/focusguard-app/main.py" ]; then
    echo "❌ Error: Please run this script from the project root directory"
    exit 1
fi

# Check git status
echo "📋 Checking git status..."
if [ -n "$(git status --porcelain)" ]; then
    echo "✅ Changes detected, proceeding with deployment..."
else
    echo "⚠️  No changes detected. Do you want to continue anyway? (y/n)"
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        echo "❌ Deployment cancelled"
        exit 1
    fi
fi

# Add all changes
echo "📦 Adding files to git..."
git add .

# Get commit message
echo "💬 Enter commit message (or press Enter for default):"
read -r commit_message

if [ -z "$commit_message" ]; then
    commit_message="🚀 Deploy FocusGuard with BERT integration and enhanced features"
fi

# Commit changes
echo "💾 Committing changes..."
git commit -m "$commit_message"

# Push to remote
echo "📤 Pushing to remote repository..."
git push origin main

echo "✅ Deployment script completed!"
echo ""
echo "📋 Next steps:"
echo "1. Check Render dashboard for backend deployment"
echo "2. Check Netlify dashboard for frontend deployment"
echo "3. Update environment variables in both platforms"
echo "4. Test the deployed application"
echo ""
echo "📚 See DEPLOYMENT_GUIDE.md for detailed instructions"
