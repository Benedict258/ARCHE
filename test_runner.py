#!/usr/bin/env python3
"""
Comprehensive test runner with coverage reporting and performance analysis.
Usage: python test_runner.py [command]

Commands:
  all        - Run all test suites (unit + integration + performance)
  unit       - Run unit tests only
  integration - Run integration tests only
  performance - Run performance benchmarks
  coverage   - Run tests with coverage report
  quick      - Quick smoke tests for CI/CD
"""

import sys
import subprocess
import json
from pathlib import Path
from typing import List, Dict
import time


class TestRunner:
    """Orchestrates test execution and reporting."""
    
    def __init__(self):
        self.workspace = Path.cwd()
        self.results = {
            "timestamp": time.time(),
            "test_results": {},
            "coverage_report": None,
            "performance_report": None,
        }
    
    def run_command(self, cmd: List[str], description: str, capture_output: bool = False) -> bool:
        """Run shell command and report status."""
        print(f"\n{'='*60}")
        print(f"▶ {description}")
        print(f"{'='*60}")
        print(f"$ {' '.join(cmd)}")
        print()
        
        try:
            result = subprocess.run(
                cmd,
                cwd=self.workspace,
                capture_output=capture_output,
                timeout=300,
            )
            
            if result.returncode == 0:
                print(f"✅ {description} PASSED")
                return True
            else:
                print(f"❌ {description} FAILED (exit code: {result.returncode})")
                if result.stdout:
                    print(result.stdout.decode())
                if result.stderr:
                    print(result.stderr.decode())
                return False
        
        except subprocess.TimeoutExpired:
            print(f"⏱️  {description} TIMEOUT (exceeded 5 minutes)")
            return False
        except Exception as e:
            print(f"❌ {description} ERROR: {e}")
            return False
    
    def run_unit_tests(self) -> bool:
        """Run unit tests."""
        return self.run_command(
            ["python", "-m", "pytest", "tests/test_ingest.py", "tests/test_simulate.py", "-v", "--tb=short"],
            "Unit Tests",
        )
    
    def run_integration_tests(self) -> bool:
        """Run integration tests."""
        return self.run_command(
            ["python", "-m", "pytest", "tests/test_integration.py", "-v", "--tb=short"],
            "Integration Tests",
        )
    
    def run_performance_tests(self) -> bool:
        """Run performance benchmarks."""
        return self.run_command(
            ["python", "-m", "pytest", "tests/test_performance.py", "-v", "--tb=short", "-s"],
            "Performance Benchmarks",
        )
    
    def run_coverage_report(self) -> bool:
        """Run tests with coverage reporting."""
        cmd = [
            "python", "-m", "pytest",
            "tests/",
            "--cov=api", "--cov=memory", "--cov=orchestrator", "--cov=sdk",
            "--cov-report=term-missing",
            "--cov-report=html",
            "--cov-report=json",
            "-v", "--tb=short",
        ]
        
        success = self.run_command(cmd, "Coverage Report")
        
        # Parse coverage JSON if it exists
        coverage_json = Path(".coverage.json") if Path(".coverage.json").exists() else None
        if coverage_json and coverage_json.exists():
            try:
                with open(coverage_json) as f:
                    self.results["coverage_report"] = json.load(f)
            except Exception as e:
                print(f"⚠️  Could not parse coverage report: {e}")
        
        return success
    
    def run_quick_smoke_tests(self) -> bool:
        """Run quick smoke tests."""
        return self.run_command(
            ["python", "-m", "pytest", "tests/", "-v", "-x", "--tb=short", "-k", "not performance"],
            "Quick Smoke Tests (unit + integration)",
        )
    
    def run_all_tests(self) -> bool:
        """Run all test suites."""
        print("\n" + "="*60)
        print("🧪 ARCHE COMPREHENSIVE TEST SUITE")
        print("="*60)
        
        results = {}
        
        # Unit tests
        results["unit"] = self.run_unit_tests()
        
        # Integration tests
        results["integration"] = self.run_integration_tests()
        
        # Performance tests
        results["performance"] = self.run_performance_tests()
        
        # Coverage
        results["coverage"] = self.run_coverage_report()
        
        # Summary
        self.print_summary(results)
        
        return all(results.values())
    
    def print_summary(self, results: Dict[str, bool]):
        """Print test summary."""
        print("\n" + "="*60)
        print("📊 TEST SUMMARY")
        print("="*60)
        
        for test_type, passed in results.items():
            status = "✅ PASSED" if passed else "❌ FAILED"
            print(f"{test_type.upper():20} {status}")
        
        total = len(results)
        passed = sum(1 for v in results.values() if v)
        
        print(f"\n{passed}/{total} test suites passed")
        
        if passed == total:
            print("\n🎉 All tests passed!")
        else:
            print(f"\n⚠️  {total - passed} test suite(s) failed")
    
    def generate_report(self):
        """Generate test report."""
        report_file = self.workspace / "test_report.json"
        with open(report_file, "w") as f:
            json.dump(self.results, f, indent=2)
        print(f"\n📄 Test report saved to {report_file}")


def main():
    """Main entry point."""
    command = sys.argv[1].lower() if len(sys.argv) > 1 else "all"
    
    runner = TestRunner()
    
    try:
        if command == "all":
            success = runner.run_all_tests()
        elif command == "unit":
            success = runner.run_unit_tests()
        elif command == "integration":
            success = runner.run_integration_tests()
        elif command == "performance":
            success = runner.run_performance_tests()
        elif command == "coverage":
            success = runner.run_coverage_report()
        elif command == "quick":
            success = runner.run_quick_smoke_tests()
        else:
            print(f"Unknown command: {command}")
            print(__doc__)
            return 1
        
        runner.generate_report()
        return 0 if success else 1
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
        return 130
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
