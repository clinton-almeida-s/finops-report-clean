@echo off
REM GCP Cost Optimizer - Cloud Run Deployment (Batch)

REM Configuration - EDIT THESE VALUES
set PROJECT_ID=gcp-cost-optimizer-clint
set REGION=us-central1
set APP_NAME=gcp-cost-optimizer
set BILLING_ACCOUNT=0136FF-F52314-9FF856

echo =================================================
echo GCP Cost Optimizer - Cloud Run Deployment
echo =================================================
echo.
echo Project: %PROJECT_ID%
echo Region: %REGION%
echo App Name: %APP_NAME%
echo Billing Account: %BILLING_ACCOUNT%
echo.

REM Find gcloud executable
set "GcloudPath=%ProgramFiles%\Google\Cloud SDK\google-cloud-sdk\bin\gcloud.cmd"
if not exist "%GcloudPath%" (
    set "GcloudPath=%ProgramFiles(x86)%\Google\Cloud SDK\google-cloud-sdk\bin\gcloud.cmd"
)
if not exist "%GcloudPath%" (
    set "GcloudPath=%LOCALAPPDATA%\Google\Cloud SDK\google-cloud-sdk\bin\gcloud.cmd"
)

if not exist "%GcloudPath%" (
    echo [ERROR] gcloud not found. Install from: https://dl.google.com/dl/cloudsdk/channels/rapid/GoogleCloudSDKInstaller.exe
    pause
    exit /b 1
)

REM Set project context
"%GcloudPath%" config set project %PROJECT_ID% >nul 2>&1
echo [*] Project set to: %PROJECT_ID%

REM Link billing account (if not already linked)
"%GcloudPath%" alpha billing projects describe %PROJECT_ID% --format="value(billing)" >nul 2>&1
if "%ERRORLEVEL%" NEQ "0" (
    echo [*] Linking billing account %BILLING_ACCOUNT%...
    "%GcloudPath%" alpha billing projects link %PROJECT_ID% --billing-account=%BILLING_ACCOUNT% >nul 2>&1
    if "%ERRORLEVEL%" NEQ "0" (
        echo [!] Failed to link billing account. Check permissions.
        pause
        exit /b 1
    )
    echo [+] Billing linked successfully
)

REM Enable required APIs
for %%A in (run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com containerregistry.googleapis.com) do (
    echo [*] Enabling API: %%A...
    "%GcloudPath%" services enable %%A --project=%PROJECT_ID% >nul 2>&1
    if "%ERRORLEVEL%" NEQ "0" (
        echo [!] Failed to enable %%A
    ) else (
        echo [+] %%A enabled
    )
)

REM Build and deploy to Cloud Run
echo [*] Building Docker image...
"%GcloudPath%" builds submit --tag gcr.io/%PROJECT_ID%/%APP_NAME% . >nul 2>&1
if "%ERRORLEVEL%" NEQ "0" (
    echo [!] Build failed
    pause
    exit /b 1
)

echo [*] Deploying to Cloud Run...
"%GcloudPath%" run deploy %APP_NAME% ^
    --image gcr.io/%PROJECT_ID%/%APP_NAME% ^
    --platform managed ^
    --region %REGION% ^
    --allow-unauthenticated ^
    --memory 512Mi ^
    --cpu 1 ^
    --min-instances 0 ^
    --max-instances 10 >nul 2>&1

if "%ERRORLEVEL%" NEQ "0" (
    echo [!] Deployment failed
    pause
    exit /b 1
)

echo.
echo =================================================
echo [+] Deployment complete!
echo =================================================
echo.
echo Your app is live at:
"%GcloudPath%" run services describe %APP_NAME% --platform managed --region %REGION% --format="value(status.url)" 2>&1
echo.
echo Next steps:
echo 1. Open the URL in your browser
echo 2. Share with beta users (10-15 people)
echo 3. Monitor usage at: https://console.cloud.google.com/run
echo.
echo Estimated monthly cost: $5-10
