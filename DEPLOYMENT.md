# Azure App Service Deployment

This repository is configured to automatically deploy to Azure App Service when commits are pushed to the main branch.

## Deployment Workflow

**File**: `.github/workflows/azure-webapps-python.yml`

**Target Environment**: Azure App Service `cs-deploytest`

### Automatic Deployment

The workflow automatically triggers when:
- A commit is pushed to the `main` branch

### Manual Deployment

You can also trigger the deployment manually:
1. Go to the Actions tab in GitHub
2. Select "Build and deploy Python app to Azure Web App"
3. Click "Run workflow"
4. Select the branch to deploy
5. Click "Run workflow"

## Workflow Steps

1. **Build Job**:
   - Checks out the code
   - Sets up Python 3.11
   - Pre-installs all dependencies from `requirements.txt` into `.python_packages/lib/site-packages`
   - Uploads the application and `.python_packages` folder as an artifact

2. **Deploy Job**:
   - Downloads the application artifact
   - Deploys to Azure App Service `cs-deploytest` using the publish profile
   - App Service starts the app from `run:app` (the app entrypoint in `run.py`)

## Required GitHub Secrets

The workflow requires the following GitHub secrets to be configured:
- `AZURE_WEBAPP_PUBLISH_PROFILE` - Publish profile from Azure App Service

## Runtime Notes

- There is no repository `startup.sh` script.
- `run.py` prepends `.python_packages/lib/site-packages` to `sys.path`, so pre-packaged dependencies are available at runtime.
- Ensure the App Service startup command points to the Flask app entrypoint (for example, a Gunicorn command targeting `run:app`) if you are using a custom startup command.

The workflow requires:
- `AZURE_WEBAPP_PUBLISH_PROFILE` - publish profile used by the deployment step

## Enabling the Workflow

If the workflow is disabled, you can enable it:
1. Go to Settings → Actions → General
2. Ensure "Allow all actions and reusable workflows" is selected
3. Go to the Actions tab
4. Find the workflow in the list
5. Click "Enable workflow" if it shows as disabled

## Production Deployment

For production deployments to `cs-document-generator`, use the separate workflow:
- **File**: `.github/workflows/deploy-production.yml`
- **Trigger**: Manual only (workflow_dispatch)
- **Environment**: `cs-document-generator`
