# Quick Deployment Guide - GCP Cloud Run

## Prerequisites
- Google Cloud account with billing enabled
- gcloud CLI installed: `gcloud --version`
- Docker installed (for local building)

## Step 1: Create a GCP Project

```bash
gcloud projects create your-project-name --name="GCP Cost Optimizer"
gcloud config set project your-project-name
```

## Step 2: Enable Required APIs

```bash
gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com
```

## Step 3: Deploy to Cloud Run

### Option A: One-Click Deploy (Recommended)
```bash
# Windows PowerShell
.\deploy.ps1

# Or batch file (requires gcloud in PATH)
deploy.bat
```

### Option B: Manual Deploy
```bash
# Build image
gcloud builds submit --tag gcr.io/PROJECT_ID/gcp-cost-optimizer .

# Deploy
gcloud run deploy gcp-cost-optimizer \
  --image gcr.io/PROJECT_ID/gcp-cost-optimizer \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 512Mi \
  --cpu 1
```

## Step 4: Get Your Live URL

```bash
gcloud run services describe gcp-cost-optimizer \
  --platform managed \
  --region us-central1 \
  --format="value(status.url)"
```

## Step 5: Share With Beta Users

1. Copy the URL from Step 4
2. Send to 5-10 potential users
3. Collect feedback on:
   - UI clarity
   - Recommendation accuracy
   - Missing features

## Estimated Costs

| Service | Cost |
|---------|------|
| Cloud Run (512MB, 1 CPU) | ~$5-10/month (first 2M invocations free) |
| Cloud Build | ~$0.05 per build |
| Artifact Registry | ~$0.10/month |
| **Total** | **~$6-11/month** |

> Free tier includes 2M invocations/month and 180,000 vCPU-seconds - plenty for beta testing.

## Troubleshooting

**Issue**: Build fails with "Docker not found"
```bash
# Install Docker Desktop or use Google Cloud Build instead
gcloud builds submit
```

**Issue**: Permission denied
```bash
# Grant Cloud Build service account permission
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:PROJECT_ID@cloudbuild.gserviceaccount.com" \
  --role="roles/cloudbuild.builds.builder"
```

**Issue**: App times out
```bash
# Increase timeout (default is 5 min, Streamlit needs more)
gcloud run deploy gcp-cost-optimizer \
  --timeout 300 \
  --memory 1Gi \
  --cpu 2
```

## Next Steps After Deployment

1. Test the live URL
2. Take screenshots for your portfolio
3. Write blog post about the tool
4. Post on Reddit r/gcp, r/devops, LinkedIn
5. Collect beta user feedback