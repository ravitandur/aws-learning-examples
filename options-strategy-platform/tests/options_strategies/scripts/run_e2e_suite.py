#!/usr/bin/env python3
"""
End-to-End Options Strategy Testing Suite
Orchestrates complete platform validation with proper organization

This script runs the complete end-to-end testing workflow:
1. Environment verification
2. Test data creation
3. Comprehensive strategy execution testing
4. Performance validation
5. Report generation

Usage:
    python run_e2e_suite.py [--clean] [--reports-only]
"""

import sys
import os
import argparse
import subprocess
import json
import time
from datetime import datetime
from pathlib import Path

# Add project root to path
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent.parent
sys.path.append(str(project_root))

class E2ETestSuite:
    """Complete end-to-end testing suite orchestrator"""
    
    def __init__(self, clean_data=False, reports_only=False):
        self.clean_data = clean_data
        self.reports_only = reports_only
        self.project_root = project_root
        self.scripts_dir = current_dir
        self.reports_dir = current_dir.parent.parent / "reports" / "end_to_end"
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        
        # Test results tracking
        self.results = {
            'start_time': datetime.now().isoformat(),
            'environment_verification': {},
            'test_data_creation': {},
            'strategy_execution_testing': {},
            'overall_success': False
        }
    
    def run_script(self, script_name, description):
        """Run a Python script and capture results"""
        print(f"\n🚀 {description}")
        print("=" * 60)
        
        script_path = self.scripts_dir / script_name
        if not script_path.exists():
            script_path = self.scripts_dir.parent / "strategy_flow" / "integration" / script_name
        
        if not script_path.exists():
            print(f"❌ Script not found: {script_name}")
            return False, f"Script not found: {script_name}"
        
        try:
            # Change to project root for proper imports
            original_cwd = os.getcwd()
            os.chdir(self.project_root)
            
            # Run script with virtual environment
            venv_python = self.project_root / "venv" / "bin" / "python"
            if not venv_python.exists():
                print(f"❌ Virtual environment not found at {venv_python}")
                return False, "Virtual environment not found"
            
            start_time = time.time()
            result = subprocess.run(
                [str(venv_python), str(script_path)],
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            execution_time = time.time() - start_time
            
            success = result.returncode == 0
            
            # Print output
            if result.stdout:
                print(result.stdout)
            if result.stderr and not success:
                print("STDERR:", result.stderr)
            
            return success, {
                'returncode': result.returncode,
                'execution_time': execution_time,
                'stdout': result.stdout,
                'stderr': result.stderr
            }
            
        except subprocess.TimeoutExpired:
            print(f"❌ Script timed out: {script_name}")
            return False, "Script execution timed out"
        except Exception as e:
            print(f"❌ Script execution failed: {e}")
            return False, str(e)
        finally:
            os.chdir(original_cwd)
    
    def step_1_environment_verification(self):
        """Step 1: Verify AWS environment and infrastructure"""
        if self.reports_only:
            print("⏭️ Skipping environment verification (reports-only mode)")
            return True
        
        success, result = self.run_script(
            "verify_environment.py",
            "Environment Verification - AWS & Infrastructure Check"
        )
        
        self.results['environment_verification'] = {
            'success': success,
            'result': result
        }
        
        if not success:
            print("❌ Environment verification failed. Please fix infrastructure issues before proceeding.")
            return False
        
        print("✅ Environment verification completed successfully!")
        return True
    
    def step_2_test_data_creation(self):
        """Step 2: Create comprehensive test data"""
        if self.reports_only:
            print("⏭️ Skipping test data creation (reports-only mode)")
            return True
        
        if not self.clean_data:
            print("ℹ️ Using existing test data (use --clean to recreate)")
            return True
        
        success, result = self.run_script(
            "create_test_data_v2.py",
            "Test Data Creation - Comprehensive Strategy & Allocation Data"
        )
        
        self.results['test_data_creation'] = {
            'success': success,
            'result': result
        }
        
        if not success:
            print("❌ Test data creation failed.")
            return False
        
        print("✅ Test data creation completed successfully!")
        return True
    
    def step_3_strategy_execution_testing(self):
        """Step 3: Run comprehensive strategy execution tests"""
        success, result = self.run_script(
            "test_strategy_execution_v2.py",
            "Strategy Execution Testing - End-to-End Platform Validation"
        )
        
        self.results['strategy_execution_testing'] = {
            'success': success,
            'result': result
        }
        
        if not success:
            print("❌ Strategy execution testing failed.")
            return False
        
        print("✅ Strategy execution testing completed successfully!")
        return True
    
    def generate_consolidated_report(self):
        """Generate consolidated test report"""
        print(f"\n📊 Generating Consolidated E2E Test Report")
        print("=" * 60)
        
        # Calculate overall results
        all_steps_passed = all([
            self.results.get('environment_verification', {}).get('success', True),
            self.results.get('test_data_creation', {}).get('success', True),
            self.results.get('strategy_execution_testing', {}).get('success', False)
        ])
        
        self.results['end_time'] = datetime.now().isoformat()
        self.results['overall_success'] = all_steps_passed
        
        # Load individual reports if they exist
        try:
            test_summary_path = self.reports_dir / "test_data_summary_v2.json"
            if test_summary_path.exists():
                with open(test_summary_path) as f:
                    self.results['test_data_summary'] = json.load(f)
        except Exception as e:
            print(f"⚠️ Could not load test data summary: {e}")
        
        try:
            execution_report_path = self.reports_dir / "end_to_end_test_report.json"
            if execution_report_path.exists():
                with open(execution_report_path) as f:
                    self.results['execution_test_report'] = json.load(f)
        except Exception as e:
            print(f"⚠️ Could not load execution test report: {e}")
        
        # Save consolidated report
        consolidated_report_path = self.reports_dir / "consolidated_e2e_report.json"
        with open(consolidated_report_path, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        # Print summary
        print(f"🎯 CONSOLIDATED E2E TEST RESULTS")
        print(f"================================")
        print(f"Overall Success: {'✅ PASS' if all_steps_passed else '❌ FAIL'}")
        print(f"Environment Verification: {'✅' if self.results.get('environment_verification', {}).get('success', True) else '❌'}")
        print(f"Test Data Creation: {'✅' if self.results.get('test_data_creation', {}).get('success', True) else '❌'}")
        print(f"Strategy Execution Testing: {'✅' if self.results.get('strategy_execution_testing', {}).get('success', False) else '❌'}")
        
        # Show key metrics if available
        execution_report = self.results.get('execution_test_report', {})
        if execution_report:
            overall_results = execution_report.get('overall_results', {})
            passed_tests = overall_results.get('passed_tests', 0)
            total_tests = overall_results.get('total_tests', 0)
            success_rate = overall_results.get('success_rate', 0)
            
            print(f"\n📈 EXECUTION TEST METRICS:")
            print(f"   Tests Passed: {passed_tests}/{total_tests}")
            print(f"   Success Rate: {success_rate:.1f}%")
            
            revolutionary_features = execution_report.get('revolutionary_features_validation', {})
            if revolutionary_features:
                print(f"\n🚀 REVOLUTIONARY FEATURES:")
                print(f"   GSI2 Optimization: {revolutionary_features.get('gsi2_optimization', 'N/A')}")
                print(f"   Multi-Broker Allocation: {'✅' if revolutionary_features.get('multi_broker_allocation') else '❌'}")
                print(f"   Weekend Protection: {'✅' if revolutionary_features.get('weekend_protection') else '❌'}")
                print(f"   Lambda Integration: {'✅' if revolutionary_features.get('lambda_integration') else '❌'}")
        
        print(f"\n📄 Reports Location:")
        print(f"   Consolidated Report: {consolidated_report_path}")
        print(f"   Individual Reports: {self.reports_dir}")
        
        return all_steps_passed
    
    def run_complete_suite(self):
        """Run the complete end-to-end testing suite"""
        print("🚀 Options Strategy Platform - Complete E2E Testing Suite")
        print("=" * 70)
        print(f"Started at: {datetime.now()}")
        print(f"Clean data mode: {self.clean_data}")
        print(f"Reports only mode: {self.reports_only}")
        
        try:
            # Step 1: Environment verification
            if not self.step_1_environment_verification():
                return False
            
            # Step 2: Test data creation
            if not self.step_2_test_data_creation():
                return False
            
            # Step 3: Strategy execution testing
            if not self.step_3_strategy_execution_testing():
                return False
            
            # Generate consolidated report
            overall_success = self.generate_consolidated_report()
            
            print(f"\n🎉 E2E Testing Suite {'COMPLETED SUCCESSFULLY' if overall_success else 'COMPLETED WITH ISSUES'}")
            return overall_success
            
        except Exception as e:
            print(f"❌ E2E Testing Suite failed with error: {e}")
            return False

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='End-to-End Options Strategy Testing Suite')
    parser.add_argument('--clean', action='store_true', 
                       help='Clean and recreate all test data')
    parser.add_argument('--reports-only', action='store_true',
                       help='Only generate reports from existing test results')
    
    args = parser.parse_args()
    
    # Run the complete suite
    suite = E2ETestSuite(clean_data=args.clean, reports_only=args.reports_only)
    success = suite.run_complete_suite()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()