# Azure App Service Deployment

This repository is configured to automatically deploy to Azure App Service when commits are pushed to the main branch.

## Deployment Workflow

**File**: `.github/workflows/main_cs-document-generator.yml`

**Target Environment**: Azure App Service `cs-deploytest`

### Automatic Deployment

The workflow automatically triggers when:
- A commit is pushed to the `main` branch

### Manual Deployment

You can also trigger the deployment manually:
1. Go to the Actions tab in GitHub
2. Select "Build and deploy Python app - deploy to cs-deploytest"
3. Click "Run workflow"
4. Select the branch to deploy
5. Click "Run workflow"

## Workflow Steps

1. **Build Job**:
   - Checks out the code
   - Sets up Python 3.11
   - Creates a virtual environment
   - Installs dependencies from `requirements.txt`
   - Uploads the application as an artifact

2. **Deploy Job**:
   - Downloads the application artifact
   - Authenticates with Azure using OpenID Connect (OIDC)
   - Enables App Service remote build (`SCM_DO_BUILD_DURING_DEPLOYMENT`, `ENABLE_ORYX_BUILD`)
   - Deploys to Azure App Service `cs-deploytest`
   - App Service installs Python dependencies from `requirements.txt` during deployment

## Required Secrets

The workflow requires the following GitHub secrets to be configured:
- `AZURE_CLIENT_ID` - Azure service principal client ID
- `AZURE_TENANT_ID` - Azure tenant ID  
- `AZURE_SUBSCRIPTION_ID` - Azure subscription ID

These secrets are used for federated credential authentication with Azure.

The workflow also requires:
- `AZURE_WEBAPP_PUBLISH_PROFILE` - publish profile used by the final deployment step

## Enabling the Workflow

If the workflow is disabled, you can enable it:
1. Go to Settings → Actions → General
2. Ensure "Allow all actions and reusable workflows" is selected
3. Go to the Actions tab
4. Find the workflow in the list
5. Click "Enable workflow" if it shows as disabled

## Production Deployment

For production deployments to `cs-document-generator`, use the separate workflow:
- **File**: `.github/workflows/promote-to-production.yml`
- **Trigger**: Manual only (workflow_dispatch)
- **Environment**: Production (requires approval)
