#!/bin/bash
# GCP Cost Optimizer - Cloud Run Deploy Script
# Run this to deploy your app to Google Cloud Run

set -e

# Configuration - EDIT THESE VALUES
PROJECT_ID="${PROJECT_ID:-your-gcp-project-id}"
REGION="${REGION:-us-central1}"
APP_NAME="gcp-cost-optimizer"

echo "================================================"
echo "GCP Cost Optimizer - Cloud Run Deployment"
echo "================================================"
echo ""
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo "App Name: $APP_NAME"
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "[ERROR] gcloud CLI not found. Install it from:"
    echo "https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Check if authenticated
echo "[*] Checking authentication..."
gcloud auth list --filter=status:ACTIVE --format="value(account)" > /dev/null 2>&1 || {
    echo "[!] No active authentication found."
    echo "Run: gcloud auth login"
    exit 1
}

# Check if Cloud Run API is enabled
echo "[*] Checking Cloud Run API..."
gcloud services enable run.googleapis.com --project="$PROJECT_ID" 2>/dev/null || true

# Build and deploy to Cloud Run
echo "[*] Building Docker image..."
gcloud builds submit --tag gcr.io/"$PROJECT_ID"/"$APP_NAME" .

echo "[*] Deploying to Cloud Run..."
gcloud run deploy "$APP_NAME" \
    --image gcr.io/"$PROJECT_ID"/"$APP_NAME" \
    --platform managed \
    --region "$REGION" \
    --allow-unauthenticated \
    --memory 512Mi \
    --cpu 1 \
    --min-instances 0 \
    --max-instances 10

echo ""
echo "================================================"
echo "[+] Deployment complete!"
echo "================================================"
echo ""
echo "Your app is live at:"
gcloud run services describe "$APP_NAME" --platform managed --region "$REGION" --format="value(status.url)"
echo ""
echo "Next steps:"
echo "1. Open the URL in your browser"
echo "2. Share with beta users"
echo "3. Monitor usage at: https://console.cloud.google.com/run"
echo ""
