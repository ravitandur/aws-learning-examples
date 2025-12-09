"""
Frontend Hosting CDK Stack

Deploys React frontend to AWS using S3 static hosting with CloudFront CDN.
Follows existing project patterns for naming, configuration, and deployment.

Architecture:
    React Build → S3 Bucket (Private) → CloudFront (CDN) → Users
                        ↑
                  Origin Access Identity (OAI)
"""

from aws_cdk import (
    Stack,
    Duration,
    RemovalPolicy,
    CfnOutput,
    aws_s3 as s3,
    aws_cloudfront as cloudfront,
    aws_cloudfront_origins as origins,
)
from constructs import Construct
from typing import Dict, Any


class FrontendHostingStack(Stack):
    """
    CDK Stack for React Frontend Hosting with S3 and CloudFront.

    Features:
    - Private S3 bucket with CloudFront OAI access
    - HTTPS enforced with TLS 1.2+
    - SPA routing (403/404 → index.html)
    - Smart caching (index.html=no-cache, static assets=1 year)
    - Environment-specific configurations
    """

    def __init__(self, scope: Construct, construct_id: str,
                 deploy_env: str, config: Dict[str, Any], **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.deploy_env = deploy_env
        self.config = config
        self.company_prefix = config['company']['short_name']
        self.project_name = config['project']
        self.env_config = config['environments'][deploy_env]

        # Create resources
        self._create_s3_bucket()
        self._create_cloudfront_distribution()
        self._create_outputs()

    def get_resource_name(self, resource_type: str) -> str:
        """Generate environment-specific resource names with company prefix."""
        return f"{self.company_prefix}-{self.project_name}-{self.deploy_env}-{resource_type}"

    def get_removal_policy(self) -> RemovalPolicy:
        """Get environment-specific removal policy."""
        policy = self.env_config['removal_policy']
        return RemovalPolicy.DESTROY if policy == "DESTROY" else RemovalPolicy.RETAIN

    def _create_s3_bucket(self):
        """Create private S3 bucket for frontend static assets."""

        self.frontend_bucket = s3.Bucket(
            self, f"FrontendBucket{self.deploy_env.title()}",
            bucket_name=self.get_resource_name("frontend-assets"),
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            encryption=s3.BucketEncryption.S3_MANAGED,
            versioned=True if self.deploy_env != 'dev' else False,
            removal_policy=self.get_removal_policy(),
            auto_delete_objects=True if self.env_config['removal_policy'] == 'DESTROY' else False,
            cors=[
                s3.CorsRule(
                    allowed_methods=[s3.HttpMethods.GET, s3.HttpMethods.HEAD],
                    allowed_origins=self.env_config['cors_origins'],
                    allowed_headers=["*"],
                    max_age=3000
                )
            ]
        )

    def _create_cloudfront_distribution(self):
        """Create CloudFront distribution with SPA routing and smart caching."""

        # Origin Access Identity for secure S3 access
        oai = cloudfront.OriginAccessIdentity(
            self, f"FrontendOAI{self.deploy_env.title()}",
            comment=f"OAI for {self.get_resource_name('frontend')}"
        )

        # Grant OAI read access to S3 bucket
        self.frontend_bucket.grant_read(oai)

        # Price class based on environment (cost optimization)
        price_class_map = {
            'dev': cloudfront.PriceClass.PRICE_CLASS_100,
            'staging': cloudfront.PriceClass.PRICE_CLASS_100,
            'production': cloudfront.PriceClass.PRICE_CLASS_ALL
        }

        # Cache policy for static assets (js, css, images): 1 year cache
        static_assets_policy = cloudfront.CachePolicy(
            self, f"StaticAssetsCachePolicy{self.deploy_env.title()}",
            cache_policy_name=self.get_resource_name("static-assets-cache"),
            default_ttl=Duration.days(365),
            max_ttl=Duration.days(365),
            min_ttl=Duration.days(1),
            enable_accept_encoding_gzip=True,
            enable_accept_encoding_brotli=True,
            header_behavior=cloudfront.CacheHeaderBehavior.none(),
            query_string_behavior=cloudfront.CacheQueryStringBehavior.none()
        )

        # Cache policy for index.html: no cache (always fresh for deployments)
        index_cache_policy = cloudfront.CachePolicy(
            self, f"IndexCachePolicy{self.deploy_env.title()}",
            cache_policy_name=self.get_resource_name("index-no-cache"),
            default_ttl=Duration.seconds(0),
            max_ttl=Duration.seconds(1),
            min_ttl=Duration.seconds(0),
            header_behavior=cloudfront.CacheHeaderBehavior.none(),
            query_string_behavior=cloudfront.CacheQueryStringBehavior.none()
        )

        # S3 Origin
        s3_origin = origins.S3Origin(
            self.frontend_bucket,
            origin_access_identity=oai
        )

        # CloudFront distribution
        self.distribution = cloudfront.Distribution(
            self, f"FrontendDistribution{self.deploy_env.title()}",
            comment=f"Quantleap Frontend - {self.deploy_env} environment",
            default_behavior=cloudfront.BehaviorOptions(
                origin=s3_origin,
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                cache_policy=index_cache_policy,
                compress=True,
                allowed_methods=cloudfront.AllowedMethods.ALLOW_GET_HEAD_OPTIONS,
                cached_methods=cloudfront.CachedMethods.CACHE_GET_HEAD_OPTIONS
            ),
            additional_behaviors={
                "static/*": cloudfront.BehaviorOptions(
                    origin=s3_origin,
                    viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                    cache_policy=static_assets_policy,
                    compress=True
                ),
                "*.js": cloudfront.BehaviorOptions(
                    origin=s3_origin,
                    viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                    cache_policy=static_assets_policy,
                    compress=True
                ),
                "*.css": cloudfront.BehaviorOptions(
                    origin=s3_origin,
                    viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                    cache_policy=static_assets_policy,
                    compress=True
                ),
                "*.png": cloudfront.BehaviorOptions(
                    origin=s3_origin,
                    viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                    cache_policy=static_assets_policy,
                    compress=True
                ),
                "*.jpg": cloudfront.BehaviorOptions(
                    origin=s3_origin,
                    viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                    cache_policy=static_assets_policy,
                    compress=True
                ),
                "*.svg": cloudfront.BehaviorOptions(
                    origin=s3_origin,
                    viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                    cache_policy=static_assets_policy,
                    compress=True
                ),
                "*.woff2": cloudfront.BehaviorOptions(
                    origin=s3_origin,
                    viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                    cache_policy=static_assets_policy,
                    compress=True
                )
            },
            default_root_object="index.html",
            error_responses=[
                # SPA routing: redirect 404 to index.html
                cloudfront.ErrorResponse(
                    http_status=404,
                    response_http_status=200,
                    response_page_path="/index.html",
                    ttl=Duration.seconds(10)
                ),
                # SPA routing: redirect 403 (access denied) to index.html
                cloudfront.ErrorResponse(
                    http_status=403,
                    response_http_status=200,
                    response_page_path="/index.html",
                    ttl=Duration.seconds(10)
                )
            ],
            price_class=price_class_map.get(self.deploy_env, cloudfront.PriceClass.PRICE_CLASS_100),
            enabled=True,
            http_version=cloudfront.HttpVersion.HTTP2,
            minimum_protocol_version=cloudfront.SecurityPolicyProtocol.TLS_V1_2_2021
        )

    def _create_outputs(self):
        """Create CloudFormation outputs for cross-stack references and deployment scripts."""

        CfnOutput(
            self, "FrontendBucketName",
            value=self.frontend_bucket.bucket_name,
            description="Frontend S3 Bucket Name",
            export_name=f"{self.stack_name}-FrontendBucket"
        )

        CfnOutput(
            self, "FrontendBucketArn",
            value=self.frontend_bucket.bucket_arn,
            description="Frontend S3 Bucket ARN",
            export_name=f"{self.stack_name}-FrontendBucketArn"
        )

        CfnOutput(
            self, "CloudFrontDistributionId",
            value=self.distribution.distribution_id,
            description="CloudFront Distribution ID (for cache invalidation)",
            export_name=f"{self.stack_name}-DistributionId"
        )

        CfnOutput(
            self, "CloudFrontDomainName",
            value=self.distribution.distribution_domain_name,
            description="CloudFront Distribution Domain Name",
            export_name=f"{self.stack_name}-CloudFrontDomain"
        )

        CfnOutput(
            self, "FrontendUrl",
            value=f"https://{self.distribution.distribution_domain_name}",
            description="Frontend Application URL",
            export_name=f"{self.stack_name}-FrontendUrl"
        )
