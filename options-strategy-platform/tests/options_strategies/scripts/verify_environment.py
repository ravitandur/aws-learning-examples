#!/usr/bin/env python3
"""
Environment Verification Script
Validates AWS connection and DynamoDB tables before testing
"""

import boto3
import json
from botocore.exceptions import ClientError

# AWS Configuration
AWS_REGION = 'ap-south-1'
AWS_PROFILE = 'account2'

def verify_aws_connection():
    """Step 1: Verify AWS connection and profile"""
    print("🔍 Step 1: Verifying AWS connection...")
    
    try:
        # Initialize session with profile
        session = boto3.Session(profile_name=AWS_PROFILE)
        sts = session.client('sts', region_name=AWS_REGION)
        
        # Get account info
        identity = sts.get_caller_identity()
        account_id = identity['Account']
        
        print(f"✅ AWS Connection successful")
        print(f"   Account ID: {account_id}")
        print(f"   Profile: {AWS_PROFILE}")
        print(f"   Region: {AWS_REGION}")
        
        return session, True
        
    except Exception as e:
        print(f"❌ AWS Connection failed: {e}")
        print("💡 Fix: Ensure AWS profile 'account2' is configured")
        return None, False

def verify_dynamodb_tables(session):
    """Step 2: Verify DynamoDB tables exist and are accessible"""
    print("\n🔍 Step 2: Verifying DynamoDB tables...")
    
    dynamodb = session.client('dynamodb', region_name=AWS_REGION)
    
    # Expected tables
    expected_tables = [
        'ql-algo-trading-dev-trading-configurations',
        'ql-algo-trading-dev-execution-history'
    ]
    
    table_status = {}
    
    for table_name in expected_tables:
        try:
            response = dynamodb.describe_table(TableName=table_name)
            status = response['Table']['TableStatus']
            item_count = response['Table']['ItemCount']
            
            table_status[table_name] = {
                'status': status,
                'item_count': item_count,
                'available': status == 'ACTIVE'
            }
            
            print(f"✅ {table_name}")
            print(f"   Status: {status}")
            print(f"   Items: {item_count}")
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                print(f"❌ {table_name} - Table not found")
                table_status[table_name] = {'available': False}
            else:
                print(f"❌ {table_name} - Error: {e}")
                table_status[table_name] = {'available': False}
    
    all_available = all(table.get('available', False) for table in table_status.values())
    
    if all_available:
        print("✅ All required tables are available")
    else:
        print("❌ Some tables are missing or not available")
        print("💡 Fix: Ensure CDK stack is deployed successfully")
    
    return table_status, all_available

def verify_lambda_functions(session):
    """Step 3: Verify Lambda functions exist"""
    print("\n🔍 Step 3: Verifying Lambda functions...")
    
    lambda_client = session.client('lambda', region_name=AWS_REGION)
    
    # Expected Lambda functions
    expected_functions = [
        'ql-algo-trading-dev-options-event-emitter',
        'ql-algo-trading-dev-options-schedule-strategy-trigger', 
        'ql-algo-trading-dev-options-strategy-manager',
        'ql-algo-trading-dev-options-strategy-executor'
    ]
    
    function_status = {}
    
    for func_name in expected_functions:
        try:
            response = lambda_client.get_function(FunctionName=func_name)
            state = response['Configuration']['State']
            
            function_status[func_name] = {
                'state': state,
                'available': state == 'Active'
            }
            
            print(f"✅ {func_name}")
            print(f"   State: {state}")
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                print(f"❌ {func_name} - Function not found")
            else:
                print(f"❌ {func_name} - Error: {e}")
            
            function_status[func_name] = {'available': False}
    
    all_available = all(func.get('available', False) for func in function_status.values())
    
    if all_available:
        print("✅ All required Lambda functions are available")
    else:
        print("❌ Some Lambda functions are missing")
        print("💡 Fix: Ensure CDK stack deployment completed successfully")
    
    return function_status, all_available

def verify_step_functions(session):
    """Step 4: Verify Step Functions state machine"""
    print("\n🔍 Step 4: Verifying Step Functions...")
    
    sf_client = session.client('stepfunctions', region_name=AWS_REGION)
    
    # Expected state machine
    state_machine_name = 'ql-algo-trading-dev-master-precision-timer'
    
    try:
        # List state machines to find the ARN
        response = sf_client.list_state_machines()
        
        target_sm = None
        for sm in response['stateMachines']:
            if state_machine_name in sm['name']:
                target_sm = sm
                break
        
        if target_sm:
            print(f"✅ {target_sm['name']}")
            print(f"   ARN: {target_sm['stateMachineArn']}")
            
            return target_sm['stateMachineArn'], True
        else:
            print(f"❌ State machine '{state_machine_name}' not found")
            return None, False
            
    except Exception as e:
        print(f"❌ Step Functions verification failed: {e}")
        return None, False

def main():
    """Main environment verification"""
    print("🚀 Options Strategy Platform - Environment Verification")
    print("=" * 60)
    
    # Step 1: AWS Connection
    session, aws_ok = verify_aws_connection()
    if not aws_ok:
        return False
    
    # Step 2: DynamoDB Tables
    table_status, tables_ok = verify_dynamodb_tables(session)
    
    # Step 3: Lambda Functions
    function_status, functions_ok = verify_lambda_functions(session)
    
    # Step 4: Step Functions
    state_machine_arn, sf_ok = verify_step_functions(session)
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 ENVIRONMENT VERIFICATION SUMMARY")
    print("=" * 60)
    
    checks = [
        ("AWS Connection", aws_ok),
        ("DynamoDB Tables", tables_ok), 
        ("Lambda Functions", functions_ok),
        ("Step Functions", sf_ok)
    ]
    
    passed_checks = sum(1 for _, ok in checks if ok)
    total_checks = len(checks)
    
    for check_name, ok in checks:
        status = "✅ PASS" if ok else "❌ FAIL"
        print(f"{status} {check_name}")
    
    print(f"\nOverall Status: {passed_checks}/{total_checks} checks passed")
    
    if passed_checks == total_checks:
        print("🎉 Environment is ready for end-to-end testing!")
        print("\n📋 Next Steps:")
        print("1. Run: python create_test_data.py")
        print("2. Run: python test_strategy_execution.py")
        return True
    else:
        print("❌ Environment needs fixes before testing")
        print("\n🔧 Required Actions:")
        if not tables_ok:
            print("- Deploy CDK stack: cdk deploy --profile account2")
        if not functions_ok:
            print("- Verify Lambda functions deployment")
        if not sf_ok:
            print("- Verify Step Functions state machine deployment")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)