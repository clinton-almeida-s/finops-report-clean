# GCP Cost Optimizer - Cloud Run Deployment (PowerShell)

# Configuration - EDIT THESE VALUES
$ProjectID = "gcp-cost-optimizer-clint"
$Region = "us-central1"
$AppName = "gcp-cost-optimizer"
$BillingAccount = "0136FF-F52314-9FF856"

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "GCP Cost Optimizer - Cloud Run Deployment" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Project: $ProjectID" -ForegroundColor Yellow
Write-Host "Region: $Region" -ForegroundColor Yellow
Write-Host "App Name: $AppName" -ForegroundColor Yellow
Write-Host "Billing Account: $BillingAccount" -ForegroundColor Yellow
Write-Host ""

# Find gcloud executable
$GcloudPath = "${env:ProgramFiles}\Google\Cloud SDK\google-cloud-sdk\bin\gcloud.cmd"
if (-not (Test-Path $GcloudPath)) {
    $GcloudPath = "${env:ProgramFiles(x86)}\Google\Cloud SDK\google-cloud-sdk\bin\gcloud.cmd"
}
if (-not (Test-Path $GcloudPath)) {
    $GcloudPath = "${env:LOCALAPPDATA}\Google\Cloud SDK\google-cloud-sdk\bin\gcloud.cmd"
}

if (-not (Test-Path $GcloudPath)) {
    Write-Host "[ERROR] gcloud not found. Install from: https://dl.google.com/dl/cloudsdk/channels/rapid/GoogleCloudSDKInstaller.exe" -ForegroundColor Red
    exit 1
}

# Set project context
&$GcloudPath config set project $ProjectID 2>$null
Write-Host "[*] Project set to: $ProjectID" -ForegroundColor Green

# Link billing account (if not already linked)
$BillingStatus = &$GcloudPath alpha billing projects describe $ProjectID --format="value(billing)" 2>$null
if ($LASTEXITCODE -ne 0 -or $BillingStatus -ne $BillingAccount) {
    Write-Host "[*] Linking billing account $BillingAccount..." -ForegroundColor Yellow
    &$GcloudPath alpha billing projects link $ProjectID --billing-account=$BillingAccount 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[!] Failed to link billing account. Check permissions." -ForegroundColor Red
        exit 1
    }
    Write-Host "[+] Billing linked successfully" -ForegroundColor Green
}

# Enable required APIs
$Apis = @("run.googleapis.com", "cloudbuild.googleapis.com", "artifactregistry.googleapis.com", "containerregistry.googleapis.com")
foreach ($Api in $Apis) {
    Write-Host "[*] Enabling API: $Api..." -ForegroundColor Yellow
    &$GcloudPath services enable $Api --project=$ProjectID 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[!] Failed to enable $Api" -ForegroundColor Red
    } else {
        Write-Host "[+] $Api enabled" -ForegroundColor Green
    }
}

# Build and deploy to Cloud Run
Write-Host "[*] Building Docker image..." -ForegroundColor Yellow
&$GcloudPath builds submit --tag gcr.io/$ProjectID/$AppName . 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "[!] Build failed" -ForegroundColor Red
    exit 1
}

Write-Host "[*] Deploying to Cloud Run..." -ForegroundColor Yellow
&$GcloudPath run deploy $AppName `n    --image gcr.io/$ProjectID/$AppName `n    --platform managed `n    --region $Region `n    --allow-unauthenticated `n    --memory 512Mi `n    --cpu 1 `n    --min-instances 0 `n    --max-instances 10 2>$null

if ($LASTEXITCODE -ne 0) {
    Write-Host "[!] Deployment failed" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "[+] Deployment complete!" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Your app is live at:" -ForegroundColor Yellow
&$GcloudPath run services describe $AppName --platform managed --region $Region --format="value(status.url)" 2>$null
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Open the URL in your browser" -ForegroundColor White
Write-Host "2. Share with beta users (10-15 people)" -ForegroundColor White
Write-Host "3. Monitor usage at: https://console.cloud.google.com/run" -ForegroundColor White
Write-Host ""
Write-Host "Estimated monthly cost: $5-10" -ForegroundColor Yellow
