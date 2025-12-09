# Frontend Infrastructure - CLAUDE.md

This file provides **module-specific guidance** for the Frontend Hosting Infrastructure stack.

**Shared Context**: Root `/CLAUDE.md` contains shared AWS configuration, deployment patterns, and enterprise standards

## Project Overview

**Module**: Frontend Infrastructure (S3 + CloudFront)
**Purpose**: Deploy React frontend application with global CDN distribution
**Stack Name**: `ql-algo-trading-{env}-frontend-hosting-stack`
**Dependencies**: Backend stacks (auth-broker, options-trading) for API endpoints

## Architecture

```
React Build → S3 Bucket (Private) → CloudFront (CDN) → Users
                    ↑
              Origin Access Identity (OAI)
```

### Key Components

1. **S3 Bucket**: Private static asset storage
   - `BlockPublicAccess.BLOCK_ALL` - No direct public access
   - OAI (Origin Access Identity) for CloudFront access only
   - Versioning enabled for staging/production

2. **CloudFront Distribution**: Global CDN
   - HTTPS enforced with TLS 1.2+
   - SPA routing (403/404 → index.html)
   - Compression enabled (gzip + brotli)
   - Environment-specific price classes

3. **Cache Strategy**:
   - `index.html`: No cache (TTL=0) - always fresh for deployments
   - Static assets (`*.js`, `*.css`, `static/*`): 1 year cache (content-hashed)

## Project Structure

```
frontend-infrastructure/
├── app.py                    # CDK entry point
├── cdk.json                  # CDK configuration
├── requirements.txt          # Python dependencies
├── deploy.sh                 # Symlink to shared script
├── CLAUDE.md                 # This file
└── cdk_stack/
    ├── __init__.py
    └── frontend_hosting_stack.py  # Main CDK stack
```

## Deployment

### Prerequisites
- Backend stacks deployed (for API endpoints)
- AWS profile configured (`account2`)
- Node.js installed for frontend build

### Step 1: Deploy Infrastructure

```bash
cd frontend-infrastructure
./deploy.sh -p frontend-infrastructure -e dev -a account2
```

This creates:
- S3 bucket for static assets
- CloudFront distribution
- Cache policies
- OAI for secure access

### Step 2: Deploy Frontend Code

```bash
./shared_scripts/deploy-frontend.sh -e dev -a account2
```

This:
- Builds React app (`npm run build`)
- Syncs assets to S3 with proper cache headers
- Invalidates CloudFront cache

## Stack Outputs

| Output | Description | Usage |
|--------|-------------|-------|
| `FrontendBucketName` | S3 bucket name | Deploy script |
| `CloudFrontDistributionId` | Distribution ID | Cache invalidation |
| `CloudFrontDomainName` | CloudFront domain | Access URL |
| `FrontendUrl` | Full HTTPS URL | User access |

## Environment Configuration

| Environment | Price Class | Versioning | Cache Invalidation |
|-------------|-------------|------------|-------------------|
| dev | PRICE_CLASS_100 (NA, EU) | Disabled | Immediate |
| staging | PRICE_CLASS_100 (NA, EU) | Enabled | Immediate |
| production | PRICE_CLASS_ALL (Global) | Enabled | Immediate |

## Security

- **S3**: Completely private, no public access
- **CloudFront OAI**: Only entity with S3 read access
- **HTTPS**: Enforced with redirect
- **TLS 1.2+**: Minimum protocol version
- **Compression**: Reduces data transfer

## Cost Optimization

- **S3 Storage**: ~$0.023/GB/month
- **CloudFront Transfer**: ~$0.085/GB (first 10TB)
- **CloudFront Requests**: ~$0.0075/10K requests
- **Estimated Monthly**: ~$1-5 for dev environment

### Cost Tips
- PRICE_CLASS_100 for dev/staging (NA + EU only)
- Long cache TTLs reduce origin requests
- Compression reduces data transfer

## Troubleshooting

### Build Fails
```bash
cd frontend
npm ci
npm run build
```

### Cache Not Updating
```bash
# Manual invalidation
aws cloudfront create-invalidation \
  --distribution-id DISTRIBUTION_ID \
  --paths "/*" \
  --profile account2
```

### 403 Errors
- Check OAI permissions on S3 bucket
- Verify CloudFront origin settings

## Integration with Backend

The frontend connects to backend APIs via environment variables:
- `REACT_APP_API_URL_DEV` - Auth/Broker API
- `REACT_APP_OPTIONS_API_URL_DEV` - Options Trading API

These are set in `/frontend/.env` and injected at build time.

## Future Enhancements

1. **Custom Domain**: Add Route 53 + ACM certificate
2. **WAF**: Web Application Firewall for production
3. **Lambda@Edge**: Security headers at edge
4. **Multiple Origins**: API proxy through CloudFront
