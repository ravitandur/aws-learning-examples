/**
 * Custom Test Runner
 * 
 * Industry-standard test execution with reporting and coverage
 * Supports running specific test suites and generating detailed reports
 */

const { exec } = require('child_process');
const path = require('path');
const fs = require('fs');

// Test suite configurations
const TEST_SUITES = {
  utils: {
    name: 'Utility Functions',
    pattern: 'src/test/suites/utils/**/*.test.ts',
    description: 'Tests for utility functions and parsing logic',
  },
  services: {
    name: 'Service Layer',
    pattern: 'src/test/suites/services/**/*.test.ts',
    description: 'Tests for API services and business logic',
  },
  components: {
    name: 'React Components',
    pattern: 'src/test/suites/components/**/*.test.tsx',
    description: 'Tests for UI components and user interactions',
  },
  integration: {
    name: 'Integration Tests',
    pattern: 'src/test/suites/integration/**/*.test.ts',
    description: 'End-to-end workflow tests',
  },
  all: {
    name: 'All Tests',
    pattern: 'src/test/suites/**/*.test.{ts,tsx}',
    description: 'Complete test suite execution',
  },
};

// Command line argument parsing
const args = process.argv.slice(2);
const suite = args[0] || 'all';
const options = {
  watch: args.includes('--watch'),
  coverage: args.includes('--coverage'),
  verbose: args.includes('--verbose'),
  silent: args.includes('--silent'),
  updateSnapshots: args.includes('--updateSnapshots'),
};

// Validate suite selection
if (!TEST_SUITES[suite]) {
  console.error(`❌ Unknown test suite: ${suite}`);
  console.log('Available suites:');
  Object.entries(TEST_SUITES).forEach(([key, config]) => {
    console.log(`  ${key.padEnd(12)} - ${config.description}`);
  });
  process.exit(1);
}

// Build Jest command
function buildJestCommand() {
  const selectedSuite = TEST_SUITES[suite];
  let command = 'npx react-scripts test';
  
  // Add test pattern
  if (suite !== 'all') {
    command += ` --testPathPattern="${selectedSuite.pattern}"`;
  }
  
  // Add options
  if (options.coverage) {
    command += ' --coverage --coverageReporters=text --coverageReporters=lcov --coverageReporters=html';
  }
  
  if (options.verbose) {
    command += ' --verbose';
  }
  
  if (options.updateSnapshots) {
    command += ' --updateSnapshot';
  }
  
  if (!options.watch) {
    command += ' --watchAll=false';
  }
  
  // Set environment variables
  command = `CI=${!options.watch} ${command}`;
  
  return command;
}

// Execute test suite
function runTests() {
  const selectedSuite = TEST_SUITES[suite];
  
  console.log('🧪 Quantleap Options Trading Platform - Test Runner');
  console.log('=' .repeat(60));
  console.log(`📋 Suite: ${selectedSuite.name}`);
  console.log(`📝 Pattern: ${selectedSuite.pattern}`);
  console.log(`🔍 Coverage: ${options.coverage ? 'Enabled' : 'Disabled'}`);
  console.log(`👁️  Watch Mode: ${options.watch ? 'Enabled' : 'Disabled'}`);
  console.log('=' .repeat(60));
  
  const command = buildJestCommand();
  
  if (!options.silent) {
    console.log(`Executing: ${command}\n`);
  }
  
  const child = exec(command, {
    cwd: process.cwd(),
    env: { ...process.env, NODE_ENV: 'test' },
  });
  
  child.stdout.on('data', (data) => {
    process.stdout.write(data);
  });
  
  child.stderr.on('data', (data) => {
    process.stderr.write(data);
  });
  
  child.on('close', (code) => {
    console.log(`\n${'='.repeat(60)}`);
    if (code === 0) {
      console.log('✅ All tests passed successfully!');
      
      if (options.coverage) {
        console.log('📊 Coverage report generated in coverage/ directory');
        console.log('🌐 Open coverage/lcov-report/index.html to view detailed report');
      }
    } else {
      console.log('❌ Some tests failed. Check the output above for details.');
      process.exit(code);
    }
  });
}

// Generate test report
function generateTestReport() {
  const reportPath = path.join(process.cwd(), 'test-results');
  
  if (!fs.existsSync(reportPath)) {
    fs.mkdirSync(reportPath, { recursive: true });
  }
  
  const report = {
    timestamp: new Date().toISOString(),
    suite: suite,
    options: options,
    command: buildJestCommand(),
  };
  
  fs.writeFileSync(
    path.join(reportPath, `test-run-${Date.now()}.json`),
    JSON.stringify(report, null, 2)
  );
}

// Main execution
if (require.main === module) {
  generateTestReport();
  runTests();
}

module.exports = {
  TEST_SUITES,
  buildJestCommand,
  runTests,
};