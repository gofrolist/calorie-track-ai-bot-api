# GitHub Secrets Configuration

This document explains how to configure GitHub secrets for the CI/CD pipeline.

## Required Secrets

These are the secrets referenced by the workflows in `.github/workflows/`. Add them to your GitHub repository:

### Go to: Settings → Secrets and variables → Actions → Repository secrets

## Backend Deployment (`backend-deploy.yml`)

| Secret Name | Description | Example |
|-------------|-------------|---------|
| `FLY_API_TOKEN` | Fly.io API token for deployment | `your-fly-api-token` |

## Frontend Deployment (`frontend-deploy.yml`)

| Secret Name | Description | Example |
|-------------|-------------|---------|
| `VERCEL_TOKEN` | Vercel access token used by `vercel --prod` | `your-vercel-token` |
| `VERCEL_ORG_ID` | Vercel team/organization ID | `team_...` |
| `VERCEL_PROJECT_ID` | Vercel project ID | `prj_...` |

## Backend CI (`backend-ci.yml`, optional)

| Secret Name | Description | Example |
|-------------|-------------|---------|
| `OPENAI_API_KEY` | Passed to the pytest step. Optional: tests mock OpenAI and `tests/conftest.py` overrides this variable with a test value | `sk-proj-...` |

`GITHUB_TOKEN` (used by `backend-build.yml` to push the image to GHCR) is provided automatically by GitHub Actions.

## Runtime Configuration (not GitHub secrets)

No workflow reads `DATABASE_URL`, `REDIS_URL`, `AWS_ENDPOINT_URL_S3`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `BUCKET_NAME`, `AWS_REGION` or `TELEGRAM_BOT_TOKEN` from GitHub secrets. Backend CI uses hardcoded test values for these, and `fly.toml` only sets `USE_WEBHOOK`, `WEBHOOK_URL` and `ENABLE_WORKER`, so production values must be configured on the Fly.io app itself (e.g. `fly secrets set DATABASE_URL=...`).

## How to Add Secrets

1. Go to your GitHub repository
2. Click on **Settings** tab
3. In the left sidebar, click **Secrets and variables** → **Actions**
4. Click **New repository secret**
5. Enter the secret name and value
6. Click **Add secret**

## Local Development

For local development, create a `.env` file in `backend/` (loaded by `services/config.py`) with the runtime variables listed above:

```bash
# Create .env from the template
cp backend/.env.example backend/.env

# Edit .env with your actual values
nano backend/.env
```

## CI/CD Pipeline Behavior

### Backend CI
- Runs on pull requests and pushes to `main` that touch `backend/**` (or the workflow file)
- Ruff lint, ruff format check, pyright, and the full pytest suite
- External services are mocked; no real service credentials required

### Backend Build and Deploy (Main Branch / Tags)
- `backend-build.yml` runs after a successful Backend CI run on `main` (or on `v*` tags) and pushes `ghcr.io/<owner>/<repo>:latest`
- `backend-deploy.yml` runs after a successful Backend Build on `main` (or on `v*` tags) and deploys that image to Fly.io
- Requires `FLY_API_TOKEN` secret

### Frontend CI and Deploy
- `frontend-ci.yml` runs on pull requests and pushes to `main` that touch `frontend/**`, plus manual dispatch
- `frontend-deploy.yml` runs after a successful Frontend CI run on `main`, on `v*` tags, or manual dispatch, and deploys to Vercel
- Requires `VERCEL_TOKEN`, `VERCEL_ORG_ID` and `VERCEL_PROJECT_ID` secrets

## Security Notes

- Never commit `.env` files to the repository
- GitHub secrets are encrypted and only accessible during CI/CD runs
- Use different credentials for development, staging, and production
- Rotate secrets regularly
- Use least-privilege access for service accounts

## Troubleshooting

### Tests Failing
- Backend tests do not need real services; reproduce locally with `cd backend && make test`
- Check the ruff, ruff format and pyright steps, which run before pytest

### Deployment Failing
- Verify `FLY_API_TOKEN` (backend) or the `VERCEL_*` secrets (frontend) are set correctly
- Check Fly.io app configuration
- Ensure Docker image builds successfully

### Local Development Issues
- Copy `backend/.env.example` to `backend/.env`
- Fill in actual values in `.env` file
- Run `make dev` (from the repository root or `backend/`) to start the development server
