#!/usr/bin/env python3
"""
Options Strategy Testing Suite Runner

Orchestrates the complete testing suite for options strategy platform:
- Unit tests for strategy components
- Integration tests for end-to-end workflows  
- Performance tests for GSI2 optimization
- Weekend logic validation
- Overlap prevention testing

Usage:
    python run_options_strategy_suite.py [--verbose] [--test-type unit|integration|all]
"""

import sys
import os
import argparse
import unittest
import time
from typing import Dict, Any, List
import json
from datetime import datetime

# Add paths for test discovery
current_dir = os.path.dirname(os.path.abspath(__file__))
tests_root = os.path.join(current_dir, '..', '..', '..')
options_tests_dir = os.path.join(tests_root, 'options_strategies')

# CRITICAL: Add project root to Python path for lambda_functions imports
project_root = os.path.abspath(os.path.join(current_dir, '..', '..', '..', '..'))
sys.path.insert(0, project_root)
sys.path.append(tests_root)
sys.path.append(options_tests_dir)


class OptionsStrategyTestRunner:
    """
    Test runner for complete options strategy testing suite.
    Provides comprehensive testing with reporting and performance metrics.
    """
    
    def __init__(self):
        self.test_results = {
            'total_tests': 0,
            'passed': 0,
            'failed': 0,
            'errors': 0,
            'skipped': 0,
            'execution_time': 0,
            'test_categories': {},
            'performance_metrics': {}
        }
        
    def discover_and_run_tests(self, test_type: str = 'all', verbose: bool = False) -> Dict[str, Any]:
        """Discover and run tests based on specified type"""
        
        print(f"🚀 Starting Options Strategy Test Suite - Type: {test_type}")
        print(f"📍 Test Discovery Path: {options_tests_dir}")
        
        start_time = time.time()
        
        # Configure test loader
        loader = unittest.TestLoader()
        suite = unittest.TestSuite()
        
        # Add tests based on type
        if test_type in ['unit', 'all']:
            unit_tests = self.discover_unit_tests(loader)
            suite.addTest(unit_tests)
            
        if test_type in ['integration', 'all']:
            integration_tests = self.discover_integration_tests(loader)
            suite.addTest(integration_tests)
            
        if test_type in ['performance', 'all']:
            performance_tests = self.discover_performance_tests(loader)
            suite.addTest(performance_tests)
            
        # Configure test runner
        verbosity = 2 if verbose else 1
        runner = unittest.TextTestRunner(
            verbosity=verbosity,
            buffer=True,
            resultclass=DetailedTestResult
        )
        
        # Run tests
        print(f"🧪 Running {suite.countTestCases()} tests...")
        result = runner.run(suite)
        
        # Calculate metrics
        execution_time = time.time() - start_time
        self.calculate_test_results(result, execution_time)
        
        # Generate report
        self.generate_test_report()
        
        return self.test_results
        
    def discover_unit_tests(self, loader: unittest.TestLoader) -> unittest.TestSuite:
        """Discover unit tests"""
        unit_test_dir = os.path.join(options_tests_dir, 'strategy_flow', 'unit')
        
        if os.path.exists(unit_test_dir):
            print(f"📋 Discovering unit tests in: {unit_test_dir}")
            return loader.discover(unit_test_dir, pattern='test_*.py')
        else:
            print(f"⚠️  Unit test directory not found: {unit_test_dir}")
            return unittest.TestSuite()
            
    def discover_integration_tests(self, loader: unittest.TestLoader) -> unittest.TestSuite:
        """Discover integration tests"""
        integration_test_dir = os.path.join(options_tests_dir, 'strategy_flow', 'integration')
        
        if os.path.exists(integration_test_dir):
            print(f"🔗 Discovering integration tests in: {integration_test_dir}")
            return loader.discover(integration_test_dir, pattern='test_*.py')
        else:
            print(f"⚠️  Integration test directory not found: {integration_test_dir}")
            return unittest.TestSuite()
            
    def discover_performance_tests(self, loader: unittest.TestLoader) -> unittest.TestSuite:
        """Discover performance tests"""
        performance_test_dir = os.path.join(options_tests_dir, 'strategy_flow', 'performance')
        
        if os.path.exists(performance_test_dir):
            print(f"⚡ Discovering performance tests in: {performance_test_dir}")
            return loader.discover(performance_test_dir, pattern='test_*.py')
        else:
            print(f"⚠️  Performance test directory not found: {performance_test_dir}")
            return unittest.TestSuite()
            
    def calculate_test_results(self, result: unittest.TestResult, execution_time: float):
        """Calculate comprehensive test results"""
        
        self.test_results.update({
            'total_tests': result.testsRun,
            'passed': result.testsRun - len(result.failures) - len(result.errors),
            'failed': len(result.failures),
            'errors': len(result.errors),
            'skipped': len(getattr(result, 'skipped', [])),
            'execution_time': execution_time
        })
        
        # Calculate success rate
        if result.testsRun > 0:
            success_rate = (self.test_results['passed'] / result.testsRun) * 100
            self.test_results['success_rate'] = success_rate
        else:
            self.test_results['success_rate'] = 0
            
        # Store detailed results
        self.test_results['failures'] = [
            {'test': str(test), 'error': error} 
            for test, error in result.failures
        ]
        self.test_results['errors'] = [
            {'test': str(test), 'error': error}
            for test, error in result.errors
        ]
        
    def generate_test_report(self):
        """Generate comprehensive test report"""
        
        print("\n" + "="*80)
        print("🎯 OPTIONS STRATEGY TEST SUITE RESULTS")
        print("="*80)
        
        # Summary statistics
        results = self.test_results
        print(f"📊 Test Execution Summary:")
        print(f"   Total Tests: {results['total_tests']}")
        print(f"   ✅ Passed: {results['passed']}")
        print(f"   ❌ Failed: {results['failed']}")
        print(f"   🚫 Errors: {results['errors']}")
        print(f"   ⏭️  Skipped: {results['skipped']}")
        print(f"   📈 Success Rate: {results['success_rate']:.1f}%")
        print(f"   ⏱️  Execution Time: {results['execution_time']:.2f}s")
        
        # Performance metrics
        if results['execution_time'] > 0:
            tests_per_second = results['total_tests'] / results['execution_time']
            print(f"   ⚡ Tests per Second: {tests_per_second:.1f}")
            
        # Failure details
        if results['failures']:
            print(f"\n❌ FAILURES ({len(results['failures'])}):")
            for i, failure in enumerate(results['failures'][:5], 1):  # Show first 5
                print(f"   {i}. {failure['test']}")
                if len(results['failures']) > 5:
                    print(f"   ... and {len(results['failures']) - 5} more")
                    
        # Error details
        if results['errors']:
            print(f"\n🚫 ERRORS ({len(results['errors'])}):")
            for i, error in enumerate(results['errors'][:5], 1):  # Show first 5
                print(f"   {i}. {error['test']}")
                if len(results['errors']) > 5:
                    print(f"   ... and {len(results['errors']) - 5} more")
                    
        print("\n" + "="*80)
        
        # Determine overall result
        if results['failed'] == 0 and results['errors'] == 0:
            print("🎉 ALL TESTS PASSED! Options strategy platform is ready for deployment.")
            return True
        else:
            print("🚨 SOME TESTS FAILED! Please review failures before deployment.")
            return False
            
    def save_detailed_report(self, output_file: str = None):
        """Save detailed test report to file"""
        
        if output_file is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f"options_strategy_test_results_{timestamp}.json"
            
        report_data = {
            'test_suite': 'Options Strategy Platform',
            'execution_date': datetime.now().isoformat(),
            'results': self.test_results,
            'system_info': {
                'python_version': sys.version,
                'test_framework': 'unittest',
                'test_runner': 'OptionsStrategyTestRunner'
            }
        }
        
        try:
            reports_dir = os.path.join(tests_root, 'reports', 'options_strategies')
            os.makedirs(reports_dir, exist_ok=True)
            
            report_path = os.path.join(reports_dir, output_file)
            
            with open(report_path, 'w') as f:
                json.dump(report_data, f, indent=2, default=str)
                
            print(f"📄 Detailed report saved: {report_path}")
            
        except Exception as e:
            print(f"⚠️  Failed to save detailed report: {e}")


class DetailedTestResult(unittest.TestResult):
    """Enhanced test result class with detailed metrics"""
    
    def __init__(self, stream=None, descriptions=None, verbosity=None):
        super().__init__(stream, descriptions, verbosity)
        self.test_start_times = {}
        
    def startTest(self, test):
        super().startTest(test)
        self.test_start_times[test] = time.time()
        
    def stopTest(self, test):
        super().stopTest(test)
        if test in self.test_start_times:
            execution_time = time.time() - self.test_start_times[test]
            # Store execution time for performance analysis
            if not hasattr(self, 'execution_times'):
                self.execution_times = {}
            self.execution_times[str(test)] = execution_time


def validate_test_environment() -> bool:
    """Validate test environment setup"""
    
    print("🔍 Validating test environment...")
    
    # Check required directories
    required_dirs = [
        os.path.join(options_tests_dir, 'strategy_flow'),
        os.path.join(options_tests_dir, 'test_data'),
        os.path.join(tests_root, 'shared', 'fixtures')
    ]
    
    for directory in required_dirs:
        if not os.path.exists(directory):
            print(f"❌ Missing required directory: {directory}")
            return False
        else:
            print(f"✅ Found directory: {directory}")
            
    # Check for required test files
    required_files = [
        os.path.join(tests_root, 'shared', 'fixtures', 'BaseStrategyTestCase.py'),
        os.path.join(options_tests_dir, 'strategy_flow', 'fixtures', 'OptionsStrategyTestBase.py')
    ]
    
    for file_path in required_files:
        if not os.path.exists(file_path):
            print(f"❌ Missing required file: {file_path}")
            return False
        else:
            print(f"✅ Found file: {os.path.basename(file_path)}")
            
    print("✅ Test environment validation passed")
    return True


def main():
    """Main entry point"""
    
    parser = argparse.ArgumentParser(
        description='Options Strategy Testing Suite Runner',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_options_strategy_suite.py                    # Run all tests
  python run_options_strategy_suite.py --test-type unit   # Run only unit tests
  python run_options_strategy_suite.py --verbose          # Run with verbose output
  python run_options_strategy_suite.py --test-type integration --verbose
        """
    )
    
    parser.add_argument(
        '--test-type',
        choices=['unit', 'integration', 'performance', 'all'],
        default='all',
        help='Type of tests to run (default: all)'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )
    
    parser.add_argument(
        '--save-report',
        action='store_true',
        help='Save detailed test report to file'
    )
    
    args = parser.parse_args()
    
    # Validate environment
    if not validate_test_environment():
        print("❌ Test environment validation failed. Please check setup.")
        sys.exit(1)
        
    # Run tests
    runner = OptionsStrategyTestRunner()
    
    try:
        results = runner.discover_and_run_tests(
            test_type=args.test_type,
            verbose=args.verbose
        )
        
        # Save detailed report if requested
        if args.save_report:
            runner.save_detailed_report()
            
        # Exit with appropriate code
        if results['failed'] == 0 and results['errors'] == 0:
            print("\n🎉 Test suite completed successfully!")
            sys.exit(0)
        else:
            print(f"\n🚨 Test suite completed with {results['failed']} failures and {results['errors']} errors")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Test suite execution failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()