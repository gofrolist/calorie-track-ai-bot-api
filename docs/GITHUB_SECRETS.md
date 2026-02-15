# GitHub Secrets Configuration

This document explains how to configure GitHub secrets for the CI/CD pipeline.

## Required Secrets

To enable full testing and deployment, you need to add the following secrets to your GitHub repository:

### Go to: Settings → Secrets and variables → Actions → Repository secrets

## OpenAI Configuration

| Secret Name | Description | Example |
|-------------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key for AI estimation | `sk-proj-...` |

## Database Configuration

| Secret Name | Description | Example |
|-------------|-------------|---------|
| `DATABASE_URL` | Neon PostgreSQL connection string | `postgresql://user:pass@ep-xxx.us-east-2.aws.neon.tech/neondb?sslmode=require` |

## Redis Configuration

| Secret Name | Description | Example |
|-------------|-------------|---------|
| `REDIS_URL` | Redis connection URL | `redis://localhost:6379` or `redis://user:pass@host:port` |

## Tigris/S3 Configuration

| Secret Name | Description | Example |
|-------------|-------------|---------|
| `AWS_ENDPOINT_URL_S3` | Tigris endpoint URL | `https://fly.storage.tigris.dev` |
| `AWS_ACCESS_KEY_ID` | Tigris access key | `your-access-key` |
| `AWS_SECRET_ACCESS_KEY` | Tigris secret key | `your-secret-key` |
| `BUCKET_NAME` | Tigris bucket name | `your-bucket-name` |
| `AWS_REGION` | AWS region | `auto` |

## Deployment Secrets

| Secret Name | Description | Example |
|-------------|-------------|---------|
| `FLY_API_TOKEN` | Fly.io API token for deployment | `your-fly-api-token` |

## How to Add Secrets

1. Go to your GitHub repository
2. Click on **Settings** tab
3. In the left sidebar, click **Secrets and variables** → **Actions**
4. Click **New repository secret**
5. Enter the secret name and value
6. Click **Add secret**

## Local Development

For local development, create a `.env` file in the project root with the same variables:

```bash
# Run the setup script to create .env template
make setup

# Edit .env with your actual values
nano .env
```

## CI/CD Pipeline Behavior

### Basic Tests (Always Run)
- Runs on every push and PR
- Uses mock/test environment variables
- Tests: config, health endpoints, auth endpoints
- No real service credentials required

### Full Tests (Main Branch Only)
- Runs only on pushes to main branch
- Uses real service credentials from GitHub secrets
- Tests all modules including external service integrations
- Requires all secrets to be configured

### Deployment (Main Branch Only)
- Runs only on pushes to main branch
- Deploys to Fly.io using the configured image
- Requires `FLY_API_TOKEN` secret

## Security Notes

- Never commit `.env` files to the repository
- GitHub secrets are encrypted and only accessible during CI/CD runs
- Use different credentials for development, staging, and production
- Rotate secrets regularly
- Use least-privilege access for service accounts

## Troubleshooting

### Tests Failing
- Check that all required secrets are set
- Verify secret values are correct
- Check service connectivity (Neon PostgreSQL, Redis, etc.)

### Deployment Failing
- Verify `FLY_API_TOKEN` is set correctly
- Check Fly.io app configuration
- Ensure Docker image builds successfully

### Local Development Issues
- Run `make setup` to create `.env` template
- Fill in actual values in `.env` file
- Run `make dev` to start development server
