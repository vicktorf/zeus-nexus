#!/bin/bash

# Zeus Nexus GitLab Repository Setup Script

set -e

NAMESPACE="ac-agentic"
GITLAB_URL="https://gitlab-ac-agentic.apps.prod01.fis-cloud.fpt.com"
GITLAB_USER="root"
GITLAB_PASS="zeus123456"
PROJECT_NAME="zeus-nexus"

echo "🦊 Setting up Zeus Nexus repository in GitLab..."

# Wait for GitLab to be fully ready
echo "⏳ Waiting for GitLab to be fully operational..."
sleep 60

# Create project via GitLab API (if available)
echo "📝 Creating Zeus Nexus project in GitLab..."
echo "Manual steps required:"
echo "1. Go to: $GITLAB_URL"
echo "2. Login with: $GITLAB_USER / $GITLAB_PASS"
echo "3. Create new project: $PROJECT_NAME"
echo "4. Copy the repository content from /root/zeus-nexus to GitLab"
echo ""
echo "🔄 To push current code to GitLab after project creation:"
echo "cd /root/zeus-nexus"
echo "git init"
echo "git remote add origin $GITLAB_URL/root/zeus-nexus.git"
echo "git add ."
echo "git commit -m 'Initial Zeus Nexus commit'"
echo "git push -u origin main"
echo ""

# Update BuildConfig to use the local GitLab
echo "🔧 Updating BuildConfig to use local GitLab..."
sed -i "s|https://gitlab.fiscloud.ai/frankenstein/zeus-nexus.git|$GITLAB_URL/root/zeus-nexus.git|g" /root/zeus-nexus/manifests/zeus-core/buildconfig.yaml

echo "✅ GitLab setup instructions provided. Please complete the manual steps."
echo "After pushing code to GitLab, run 'oc start-build zeus-core -n $NAMESPACE' to trigger the build."