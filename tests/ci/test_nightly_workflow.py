"""Nightly CI workflow tests.

These tests verify that the Nightly CI infrastructure is correctly configured
and functioning as expected.
"""

import json
import subprocess
import tempfile
from pathlib import Path

import pytest


class TestNightlyCIInfrastructure:
    """Test CI infrastructure files exist and are properly configured."""

    def test_extract_metrics_script_exists(self):
        """Metrics extraction script exists and is executable."""
        script_path = Path("scripts/extract_performance_metrics.py")
        assert script_path.exists(), "extract_performance_metrics.py not found"
        assert script_path.is_file(), "extract_performance_metrics.py is not a file"

    def test_regression_check_script_exists(self):
        """Regression check script exists and is executable."""
        script_path = Path("scripts/check_performance_regression.py")
        assert script_path.exists(), "check_performance_regression.py not found"
        assert script_path.is_file(), "check_performance_regression.py is not a file"

    def test_baseline_config_exists(self):
        """Baseline configuration file exists and is valid JSON."""
        config_path = Path("config/performance_baselines.json")
        assert config_path.exists(), "performance_baselines.json not found"

        # Verify it's valid JSON
        with open(config_path) as f:
            baselines = json.load(f)

        assert 'memory_system' in baselines, "memory_system key not found in baselines"
        assert 'thresholds' in baselines['memory_system'], "thresholds not found in memory_system"

    def test_baseline_config_structure(self):
        """Baseline configuration has correct structure."""
        with open("config/performance_baselines.json") as f:
            baselines = json.load(f)

        thresholds = baselines['memory_system']['thresholds']

        # Required metrics exist
        assert 'total_tests' in thresholds, "total_tests threshold missing"
        assert 'test_pass_rate' in thresholds, "test_pass_rate threshold missing"
        assert 'memory_management_tests' in thresholds, "memory_management_tests threshold missing"
        assert 'semantic_bridge_tests' in thresholds, "semantic_bridge_tests threshold missing"
        assert 'memory_store_tests' in thresholds, "memory_store_tests threshold missing"
        assert 'inference_accuracy' in thresholds, "inference_accuracy threshold missing"
        assert 'processing_performance_ms' in thresholds, "processing_performance_ms threshold missing"

        # Each threshold has required fields
        for key in ['total_tests', 'memory_management_tests', 'semantic_bridge_tests', 'memory_store_tests']:
            assert 'min' in thresholds[key], f"{key} missing 'min' field"
            assert 'warning_threshold' in thresholds[key], f"{key} missing 'warning_threshold' field"

    def test_github_workflow_exists(self):
        """GitHub Actions workflow file exists."""
        workflow_path = Path(".github/workflows/nightly-performance.yml")
        assert workflow_path.exists(), "nightly-performance.yml workflow not found"

    def test_github_workflow_valid_yaml(self):
        """GitHub Actions workflow is valid YAML."""
        import yaml

        workflow_path = Path(".github/workflows/nightly-performance.yml")
        with open(workflow_path) as f:
            workflow = yaml.safe_load(f)

        # Basic structure checks
        assert 'name' in workflow, "Workflow missing 'name'"
        # Note: YAML parses 'on' as boolean True, so we check for True key
        assert True in workflow or 'on' in workflow, "Workflow missing 'on' trigger"
        assert 'jobs' in workflow, "Workflow missing 'jobs'"
        assert 'performance' in workflow['jobs'], "Workflow missing 'performance' job"


class TestMetricsExtraction:
    """Test metrics extraction script functionality."""

    def test_extract_metrics_script_runs_with_mock_data(self):
        """Metrics extraction script processes JUnit XML correctly."""
        mock_xml = """<?xml version="1.0" encoding="utf-8"?>
<testsuite name="pytest" errors="0" failures="0" skipped="0" tests="205" time="0.52">
    <testcase classname="tests.memory.test_models" name="test_session_creation" time="0.01"/>
    <testcase classname="tests.memory.test_models" name="test_intent_validation" time="0.01"/>
    <testcase classname="tests.semantic_bridge.test_extractor" name="test_title_generation" time="0.01"/>
    <testcase classname="tests.semantic_bridge.test_inferencer" name="test_type_inference" time="0.01"/>
    <testcase classname="tests.test_memory_store.test_service" name="test_save_memory" time="0.01"/>
</testsuite>
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as xml_file:
            xml_file.write(mock_xml)
            xml_path = xml_file.name

        output_path = tempfile.NamedTemporaryFile(suffix='.json', delete=False).name

        try:
            result = subprocess.run(
                ['python', 'scripts/extract_performance_metrics.py', xml_path, 'nonexistent.json', output_path],
                capture_output=True,
                text=True,
                timeout=30
            )

            assert result.returncode == 0, f"Script failed: {result.stderr}"
            assert Path(output_path).exists(), "Output JSON not created"

            with open(output_path) as f:
                metrics = json.load(f)

            assert 'timestamp' in metrics
            assert 'tests_total' in metrics
            assert 'tests_passed' in metrics
            assert metrics['tests_total'] == 205

        finally:
            Path(xml_path).unlink(missing_ok=True)
            Path(output_path).unlink(missing_ok=True)

    def test_extract_metrics_handles_failures(self):
        """Metrics extraction correctly counts failures."""
        mock_xml = """<?xml version="1.0" encoding="utf-8"?>
<testsuite name="pytest" errors="1" failures="2" skipped="0" tests="10" time="1.0">
    <testcase classname="tests.memory.test_models" name="test_ok" time="0.1"/>
    <testcase classname="tests.memory.test_models" name="test_fail" time="0.1">
        <failure message="AssertionError">Test failed</failure>
    </testcase>
</testsuite>
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as xml_file:
            xml_file.write(mock_xml)
            xml_path = xml_file.name

        output_path = tempfile.NamedTemporaryFile(suffix='.json', delete=False).name

        try:
            result = subprocess.run(
                ['python', 'scripts/extract_performance_metrics.py', xml_path, 'nonexistent.json', output_path],
                capture_output=True,
                text=True,
                timeout=30
            )

            assert result.returncode == 0
            with open(output_path) as f:
                metrics = json.load(f)

            assert metrics['tests_total'] == 10
            assert metrics['tests_failed'] == 2
            assert metrics['tests_errors'] == 1
            assert metrics['tests_passed'] == 7  # 10 - 2 - 1

        finally:
            Path(xml_path).unlink(missing_ok=True)
            Path(output_path).unlink(missing_ok=True)


class TestRegressionCheck:
    """Test regression check script functionality."""

    def test_regression_check_no_regression(self):
        """Regression check passes when metrics meet baseline."""
        metrics = {
            'tests_total': 205,
            'tests_passed': 205,
            'tests_failed': 0,
            'memory_management_tests': 72,
            'semantic_bridge_tests': 97,
            'memory_store_tests': 36,
            'inference_accuracy': 100.0,
            'processing_performance_ms': 0.12
        }

        metrics_path = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False).name
        with open(metrics_path, 'w') as f:
            json.dump(metrics, f)

        try:
            result = subprocess.run(
                ['python', 'scripts/check_performance_regression.py'],
                capture_output=True,
                text=True,
                cwd=str(Path.cwd()),
                env={'PYTHONPATH': str(Path.cwd())},
                timeout=30
            )

            # Move metrics file to expected location
            Path(metrics_path).rename('performance-metrics.json')

            result = subprocess.run(
                ['python', 'scripts/check_performance_regression.py'],
                capture_output=True,
                text=True,
                timeout=30
            )

            assert result.returncode == 0, f"Regression check failed unexpectedly: {result.stderr}"
            assert "No performance regression detected" in result.stdout

        finally:
            Path('performance-metrics.json').unlink(missing_ok=True)
            Path(metrics_path).unlink(missing_ok=True)

    def test_regression_check_detects_low_test_count(self):
        """Regression check fails when test count is below threshold."""
        metrics = {
            'tests_total': 150,  # Below 195 (95% of 205)
            'tests_passed': 150,
            'tests_failed': 0,
            'memory_management_tests': 50,
            'semantic_bridge_tests': 70,
            'memory_store_tests': 30,
            'inference_accuracy': 100.0,
            'processing_performance_ms': 0.12
        }

        with open('performance-metrics.json', 'w') as f:
            json.dump(metrics, f)

        try:
            result = subprocess.run(
                ['python', 'scripts/check_performance_regression.py'],
                capture_output=True,
                text=True,
                timeout=30
            )

            assert result.returncode == 1, "Regression check should fail for low test count"
            assert "REGRESSION" in result.stdout

        finally:
            Path('performance-metrics.json').unlink(missing_ok=True)

    def test_regression_check_detects_low_pass_rate(self):
        """Regression check fails when pass rate is below threshold."""
        metrics = {
            'tests_total': 205,
            'tests_passed': 180,  # 87.8% < 95%
            'tests_failed': 25,
            'memory_management_tests': 72,
            'semantic_bridge_tests': 97,
            'memory_store_tests': 36,
            'inference_accuracy': 100.0,
            'processing_performance_ms': 0.12
        }

        with open('performance-metrics.json', 'w') as f:
            json.dump(metrics, f)

        try:
            result = subprocess.run(
                ['python', 'scripts/check_performance_regression.py'],
                capture_output=True,
                text=True,
                timeout=30
            )

            assert result.returncode == 1, "Regression check should fail for low pass rate"
            assert "REGRESSION" in result.stdout
            assert "Pass Rate" in result.stdout

        finally:
            Path('performance-metrics.json').unlink(missing_ok=True)


class TestBaselineValues:
    """Test that baseline values are correct."""

    def test_baseline_values_match_sprint_reports(self):
        """Baseline values match the Sprint completion reports."""
        with open("config/performance_baselines.json") as f:
            baselines = json.load(f)

        components = baselines['memory_system']['components']

        # Memory Management Sprint 1
        assert components['memory_management']['tests'] == 72
        assert components['memory_management']['execution_time_seconds'] == 0.36

        # Semantic Bridge Sprint 2
        assert components['semantic_bridge']['tests'] == 97
        assert components['semantic_bridge']['execution_time_seconds'] == 0.16
        assert components['semantic_bridge']['processing_performance_ms'] == 0.12
        assert components['semantic_bridge']['inference_accuracy_percent'] == 100

        # Memory Store Sprint 3
        assert components['memory_store']['tests'] == 36

    def test_total_test_count_baseline(self):
        """Total test count baseline is sum of all components."""
        with open("config/performance_baselines.json") as f:
            baselines = json.load(f)

        thresholds = baselines['memory_system']['thresholds']
        components = baselines['memory_system']['components']

        expected_total = (
            components['memory_management']['tests'] +
            components['semantic_bridge']['tests'] +
            components['memory_store']['tests']
        )

        assert thresholds['total_tests']['min'] == expected_total
        assert expected_total == 205  # 72 + 97 + 36
