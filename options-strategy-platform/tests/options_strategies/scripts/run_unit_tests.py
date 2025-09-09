#!/usr/bin/env python3
"""
Comprehensive Unit Test Runner for Options Strategy Platform

Runs all unit tests for the revolutionary options trading platform,
including new comprehensive tests for:
- Test data creation algorithms
- GSI2 performance optimization 
- Strategy execution components
- Multi-broker allocation logic
- Weekend protection validation

Usage:
    python run_unit_tests.py [--verbose] [--specific-test TEST_NAME] [--coverage]
"""

import sys
import os
import unittest
import argparse
import time
from pathlib import Path
from typing import Dict, Any, List
import json

# Add paths for test discovery
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent.parent
unit_tests_dir = current_dir.parent / "strategy_flow" / "unit"
sys.path.append(str(project_root))
sys.path.append(str(unit_tests_dir))


class UnitTestRunner:
    """Comprehensive unit test runner with reporting and metrics"""
    
    def __init__(self):
        self.test_results = {
            'total_tests': 0,
            'passed': 0,
            'failed': 0,
            'errors': 0,
            'skipped': 0,
            'execution_time': 0,
            'test_modules': {},
            'detailed_failures': []
        }
        self.start_time = None
        
    def discover_unit_tests(self) -> List[str]:
        """Discover all unit test modules"""
        test_modules = []
        
        # Look for test files in unit test directory
        if unit_tests_dir.exists():
            for test_file in unit_tests_dir.glob("test_*.py"):
                module_name = test_file.stem
                test_modules.append(module_name)
        
        return sorted(test_modules)
    
    def run_specific_test(self, test_name: str) -> unittest.TestResult:
        """Run a specific test module"""
        print(f"🧪 Running unit test: {test_name}")
        print("-" * 50)
        
        try:
            # Import the test module
            test_module = __import__(test_name)
            
            # Create test suite
            loader = unittest.TestLoader()
            suite = loader.loadTestsFromModule(test_module)
            
            # Run tests with custom result collector
            runner = unittest.TextTestRunner(
                verbosity=2,
                stream=sys.stdout,
                buffer=True
            )
            
            start_time = time.time()
            result = runner.run(suite)
            execution_time = time.time() - start_time
            
            # Record results
            module_results = {
                'tests_run': result.testsRun,
                'failures': len(result.failures),
                'errors': len(result.errors),
                'skipped': len(result.skipped),
                'execution_time': execution_time,
                'success_rate': ((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100) if result.testsRun > 0 else 0
            }
            
            self.test_results['test_modules'][test_name] = module_results
            
            # Update overall results
            self.test_results['total_tests'] += result.testsRun
            self.test_results['passed'] += result.testsRun - len(result.failures) - len(result.errors)
            self.test_results['failed'] += len(result.failures)
            self.test_results['errors'] += len(result.errors)
            self.test_results['skipped'] += len(result.skipped)
            
            # Record detailed failures
            for test, traceback in result.failures:
                self.test_results['detailed_failures'].append({
                    'test': str(test),
                    'type': 'failure',
                    'traceback': traceback
                })
            
            for test, traceback in result.errors:
                self.test_results['detailed_failures'].append({
                    'test': str(test),
                    'type': 'error',
                    'traceback': traceback
                })
            
            print(f"✅ Module {test_name}: {result.testsRun - len(result.failures) - len(result.errors)}/{result.testsRun} passed")
            
            return result
            
        except ImportError as e:
            print(f"❌ Failed to import test module {test_name}: {e}")
            return None
        except Exception as e:
            print(f"❌ Error running test module {test_name}: {e}")
            return None
    
    def run_all_unit_tests(self, verbose: bool = False) -> bool:
        """Run all discovered unit tests"""
        print("🚀 Options Strategy Platform - Comprehensive Unit Testing")
        print("=" * 65)
        
        self.start_time = time.time()
        
        # Discover all unit test modules
        test_modules = self.discover_unit_tests()
        
        if not test_modules:
            print("❌ No unit test modules found!")
            return False
        
        print(f"📋 Discovered {len(test_modules)} unit test modules:")
        for module in test_modules:
            print(f"   • {module}")
        
        print()
        
        # Run each test module
        all_passed = True
        for module_name in test_modules:
            result = self.run_specific_test(module_name)
            if result is None or len(result.failures) > 0 or len(result.errors) > 0:
                all_passed = False
            print()
        
        # Calculate total execution time
        self.test_results['execution_time'] = time.time() - self.start_time
        
        return all_passed
    
    def generate_comprehensive_report(self):
        """Generate comprehensive unit test report"""
        print("=" * 65)
        print("📊 COMPREHENSIVE UNIT TEST REPORT")
        print("=" * 65)
        
        # Overall summary
        total_tests = self.test_results['total_tests']
        passed_tests = self.test_results['passed']
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"🎯 OVERALL RESULTS:")
        print(f"   Total Tests: {total_tests}")
        print(f"   Passed: {passed_tests}")
        print(f"   Failed: {self.test_results['failed']}")
        print(f"   Errors: {self.test_results['errors']}")
        print(f"   Skipped: {self.test_results['skipped']}")
        print(f"   Success Rate: {success_rate:.1f}%")
        print(f"   Execution Time: {self.test_results['execution_time']:.2f}s")
        
        # Module-specific results
        print(f"\n📋 MODULE-SPECIFIC RESULTS:")
        for module_name, results in self.test_results['test_modules'].items():
            status = "✅" if results['failures'] == 0 and results['errors'] == 0 else "❌"
            print(f"   {status} {module_name}:")
            print(f"      Tests: {results['tests_run']}")
            print(f"      Success Rate: {results['success_rate']:.1f}%")
            print(f"      Time: {results['execution_time']:.3f}s")
        
        # Revolutionary features testing summary
        print(f"\n🚀 REVOLUTIONARY FEATURES TESTED:")
        feature_modules = {
            'test_test_data_creation': 'Multi-Broker Allocation Algorithm',
            'test_gsi2_performance_optimization': 'GSI2 Query Optimization (99.5% reduction)',
            'test_strategy_execution_components': 'End-to-End Testing Components',
            'test_strategy_broker_allocation': 'Revolutionary Broker Allocation',
            'test_weekday_scheduling_logic': 'Weekend Protection Logic',
            'test_indian_market_specialization': 'Indian Market Specialization',
            'test_gsi2_overlap_prevention': 'Execution Overlap Prevention'
        }
        
        for module_name, feature_description in feature_modules.items():
            if module_name in self.test_results['test_modules']:
                module_results = self.test_results['test_modules'][module_name]
                status = "✅" if module_results['failures'] == 0 and module_results['errors'] == 0 else "❌"
                print(f"   {status} {feature_description}")
            else:
                print(f"   ⚠️ {feature_description} (module not found)")
        
        # Performance analysis
        avg_test_time = (self.test_results['execution_time'] / total_tests) if total_tests > 0 else 0
        print(f"\n📈 PERFORMANCE METRICS:")
        print(f"   Average Test Time: {avg_test_time:.3f}s")
        print(f"   Tests per Second: {total_tests / self.test_results['execution_time']:.1f}")
        
        # Failure analysis
        if self.test_results['detailed_failures']:
            print(f"\n❌ FAILURE ANALYSIS:")
            for failure in self.test_results['detailed_failures']:
                print(f"   • {failure['test']} ({failure['type']})")
                print(f"     {failure['traceback'][:200]}...")
        else:
            print(f"\n✅ NO FAILURES DETECTED")
        
        # Save detailed report
        report_path = current_dir.parent.parent / "reports" / "unit_test_report.json"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        
        detailed_report = {
            'timestamp': time.time(),
            'summary': self.test_results,
            'revolutionary_features_coverage': feature_modules
        }
        
        with open(report_path, 'w') as f:
            json.dump(detailed_report, f, indent=2, default=str)
        
        print(f"\n📄 Detailed report saved: {report_path}")
        
        # Next steps
        if success_rate >= 95:
            print(f"\n🎉 EXCELLENT: Unit tests ready for production!")
            print(f"   📋 Next Steps:")
            print(f"   • Run integration tests: python run_e2e_suite.py")
            print(f"   • Performance benchmarking: python run_performance_benchmarks.py")
        elif success_rate >= 80:
            print(f"\n✅ GOOD: Most unit tests passing")
            print(f"   🔧 Review failed tests and fix issues")
        else:
            print(f"\n❌ NEEDS WORK: Low success rate")
            print(f"   🚨 Fix critical test failures before proceeding")
        
        return success_rate >= 95
    
    def run_with_coverage(self):
        """Run tests with coverage analysis (if coverage.py available)"""
        try:
            import coverage
            
            # Start coverage
            cov = coverage.Coverage()
            cov.start()
            
            # Run tests
            success = self.run_all_unit_tests()
            
            # Stop coverage and generate report
            cov.stop()
            cov.save()
            
            print(f"\n📊 COVERAGE ANALYSIS:")
            cov.report(show_missing=True)
            
            # Save coverage report
            coverage_dir = current_dir.parent.parent / "reports" / "coverage"
            coverage_dir.mkdir(parents=True, exist_ok=True)
            cov.html_report(directory=str(coverage_dir))
            
            print(f"📄 HTML coverage report: {coverage_dir}/index.html")
            
            return success
            
        except ImportError:
            print("⚠️ Coverage.py not installed. Running tests without coverage.")
            return self.run_all_unit_tests()


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Comprehensive Unit Test Runner')
    parser.add_argument('--verbose', action='store_true',
                       help='Verbose output')
    parser.add_argument('--specific-test', type=str,
                       help='Run specific test module')
    parser.add_argument('--coverage', action='store_true',
                       help='Run with coverage analysis')
    
    args = parser.parse_args()
    
    # Create test runner
    runner = UnitTestRunner()
    
    try:
        if args.specific_test:
            # Run specific test
            print(f"🎯 Running specific test: {args.specific_test}")
            result = runner.run_specific_test(args.specific_test)
            success = result is not None and len(result.failures) == 0 and len(result.errors) == 0
        elif args.coverage:
            # Run with coverage
            success = runner.run_with_coverage()
        else:
            # Run all tests
            success = runner.run_all_unit_tests(args.verbose)
        
        # Generate comprehensive report
        overall_success = runner.generate_comprehensive_report()
        
        # Exit with appropriate code
        sys.exit(0 if overall_success else 1)
        
    except KeyboardInterrupt:
        print("\n⚠️ Unit testing interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unit testing failed with error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()