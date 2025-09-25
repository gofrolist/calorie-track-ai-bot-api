# Migration from Alembic to Supabase CLI

This document describes the migration from Alembic to Supabase CLI for database migrations.

## What Changed

### Before (Alembic)
- Database migrations managed with Alembic
- Migration files in `backend/migrations/versions/`
- Python-based migration scripts
- Manual database URL configuration
- Separate migration deployment process

### After (Supabase CLI)
- Database migrations managed with Supabase CLI
- Migration files in `supabase/migrations/`
- SQL-based migration scripts
- Integrated with Supabase project management
- Automated deployment via GitHub Actions

## Migration Steps Completed

1. **Initialized Supabase CLI** in the project root
2. **Converted all Alembic migrations** to a single consolidated SQL migration
3. **Updated GitHub Actions workflows** for Supabase deployment
4. **Updated project configuration files** (pyproject.toml, Dockerfile, Makefiles)
5. **Created new deployment workflow** with proper CI/CD integration

## New File Structure

```
supabase/
├── config.toml          # Supabase configuration
├── migrations/
│   └── 20250925075640_initial_schema.sql  # Consolidated migration
└── seed.sql             # Database seed data

.github/workflows/
└── supabase-migrations.yml  # New Supabase deployment workflow
```

## Environment Variables

The following environment variables are required for Supabase deployment:

### For GitHub Actions (Secrets)
- `SUPABASE_ACCESS_TOKEN` - Your Supabase personal access token
- `PRODUCTION_DB_PASSWORD` - Your production database password
- `PRODUCTION_PROJECT_ID` - Your production project ID

### For Local Development
- `SUPABASE_URL` - Your Supabase project URL
- `SUPABASE_DB_PASSWORD` - Your database password (for direct DB access)

## New Commands

### Local Development
```bash
# Start Supabase local development
make supabase

# Stop Supabase
make supabase-stop

# Reset local database
make supabase-reset

# Generate TypeScript types
make supabase-gen-types
```

### Backend-specific commands
```bash
cd backend

# Start Supabase (from backend directory)
make supabase-start

# Stop Supabase
make supabase-stop

# Reset database
make supabase-reset

# Generate types
make supabase-gen-types
```

## Migration Process

### For New Migrations
1. Create a new migration:
   ```bash
   supabase migration new migration_name
   ```

2. Edit the generated SQL file in `supabase/migrations/`

3. Test locally:
   ```bash
   supabase db reset
   ```

4. Commit and push - GitHub Actions will automatically deploy

### For Schema Changes
1. Make changes through Supabase Studio (localhost:54323) or directly in SQL
2. Generate migration from changes:
   ```bash
   supabase db diff -f migration_name
   ```

## Deployment

Migrations are automatically deployed via GitHub Actions when:
- Code is pushed to `main` branch
- Changes are made to files in `supabase/` directory

The deployment process:
1. **Test Phase**: Validates migrations locally
2. **Deploy Phase**: Links to production and applies migrations
3. **Types Generation**: Generates and commits TypeScript types

## Rollback

Supabase migrations are forward-only. For rollbacks:
1. Create a new migration that reverses the changes
2. Deploy the rollback migration

## Benefits of Migration

1. **Simplified Management**: Single tool for all Supabase operations
2. **Better Integration**: Native integration with Supabase features
3. **Automated Deployment**: CI/CD pipeline handles deployment
4. **Type Safety**: Automatic TypeScript type generation
5. **Local Development**: Full local Supabase environment

## Cleanup

After successful migration, the following files can be removed:
- `backend/alembic.ini`
- `backend/migrations/` (entire directory)
- `backend/run_migration.py`
- `backend/run_local_migration.py`

## Troubleshooting

### Docker Issues
If you encounter Docker-related issues:
1. Ensure Docker Desktop is running
2. Check Docker daemon status: `docker ps`

### Migration Issues
If migrations fail:
1. Check the GitHub Actions logs
2. Verify environment variables are set correctly
3. Ensure Supabase project is accessible

### Local Development Issues
If local Supabase won't start:
1. Stop all containers: `supabase stop`
2. Reset: `supabase db reset`
3. Start fresh: `supabase start`

## Support

For issues related to:
- Supabase CLI: [Supabase CLI Documentation](https://supabase.com/docs/guides/cli)
- Migration process: Check this guide and GitHub Actions logs
- Database schema: Review the consolidated migration file
