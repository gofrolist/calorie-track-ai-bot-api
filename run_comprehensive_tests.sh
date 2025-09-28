#!/bin/bash
# Enhanced test runner for comprehensive workflow testing

set -e

echo "🧪 Running Comprehensive Test Suite for Calorie Track AI Bot"
echo "============================================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to run tests and report results
run_test_suite() {
    local test_name="$1"
    local test_command="$2"
    local test_dir="$3"

    echo -e "\n${BLUE}Running $test_name...${NC}"
    echo "Command: $test_command"
    echo "Directory: $test_dir"

    if [ -d "$test_dir" ]; then
        cd "$test_dir"
        if eval "$test_command"; then
            echo -e "${GREEN}✅ $test_name PASSED${NC}"
            return 0
        else
            echo -e "${RED}❌ $test_name FAILED${NC}"
            return 1
        fi
    else
        echo -e "${YELLOW}⚠️  $test_name SKIPPED (directory not found)${NC}"
        return 0
    fi
}

# Track overall results
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Function to update test counts
update_counts() {
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    if [ $? -eq 0 ]; then
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi
}

# Get the script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "Project root: $PROJECT_ROOT"
echo "Script directory: $SCRIPT_DIR"

# 1. Unit Tests (existing)
echo -e "\n${YELLOW}=== UNIT TESTS ===${NC}"
run_test_suite "Backend Unit Tests" "uv run pytest tests/ -v --tb=short" "$PROJECT_ROOT/backend"
update_counts

# 2. Integration Tests (new)
echo -e "\n${YELLOW}=== INTEGRATION TESTS ===${NC}"

# Photo to Meal Workflow Integration Test
run_test_suite "Photo-to-Meal Workflow Integration" "uv run pytest tests/integration/test_photo_to_meal_workflow.py -v --tb=short" "$PROJECT_ROOT/backend"
update_counts

# Bot to Mini-App Workflow Integration Test
run_test_suite "Bot-to-MiniApp Workflow Integration" "uv run pytest tests/integration/test_bot_to_miniapp_workflow.py -v --tb=short" "$PROJECT_ROOT/backend"
update_counts

# API Contract Tests
run_test_suite "API Contract Tests" "uv run pytest tests/integration/test_api_contracts.py -v --tb=short" "$PROJECT_ROOT/backend"
update_counts

# Error Handling Tests
run_test_suite "Error Handling Tests" "uv run pytest tests/integration/test_error_handling.py -v --tb=short" "$PROJECT_ROOT/backend"
update_counts

# 3. Worker Tests (enhanced)
echo -e "\n${YELLOW}=== WORKER TESTS ===${NC}"
run_test_suite "Enhanced Worker Tests" "uv run pytest tests/workers/test_estimate_worker.py -v --tb=short" "$PROJECT_ROOT/backend"
update_counts

# 4. API Tests (existing)
echo -e "\n${YELLOW}=== API TESTS ===${NC}"
run_test_suite "API Endpoint Tests" "uv run pytest tests/api/ -v --tb=short" "$PROJECT_ROOT/backend"
update_counts

# 5. Frontend Tests (if available)
echo -e "\n${YELLOW}=== FRONTEND TESTS ===${NC}"
if [ -d "$PROJECT_ROOT/frontend" ]; then
    run_test_suite "Frontend Unit Tests" "npm test" "$PROJECT_ROOT/frontend"
    update_counts

    run_test_suite "Frontend Integration Tests" "npm run test:integration" "$PROJECT_ROOT/frontend"
    update_counts
else
    echo -e "${YELLOW}⚠️  Frontend tests SKIPPED (frontend directory not found)${NC}"
fi

# 6. Contract Tests (if available)
echo -e "\n${YELLOW}=== CONTRACT TESTS ===${NC}"
if [ -d "$PROJECT_ROOT/frontend/tests/contracts" ]; then
    run_test_suite "Frontend Contract Tests" "npm run test:contracts" "$PROJECT_ROOT/frontend"
    update_counts
else
    echo -e "${YELLOW}⚠️  Contract tests SKIPPED (contracts directory not found)${NC}"
fi

# 7. Performance Tests (if available)
echo -e "\n${YELLOW}=== PERFORMANCE TESTS ===${NC}"
if [ -d "$PROJECT_ROOT/tests/performance" ]; then
    run_test_suite "Performance Tests" "uv run pytest tests/performance/ -v --tb=short" "$PROJECT_ROOT/backend"
    update_counts
else
    echo -e "${YELLOW}⚠️  Performance tests SKIPPED (performance directory not found)${NC}"
fi

# Summary
echo -e "\n${BLUE}============================================================${NC}"
echo -e "${BLUE}TEST SUMMARY${NC}"
echo -e "${BLUE}============================================================${NC}"
echo -e "Total test suites: $TOTAL_TESTS"
echo -e "${GREEN}Passed: $PASSED_TESTS${NC}"
echo -e "${RED}Failed: $FAILED_TESTS${NC}"

if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "\n${GREEN}🎉 ALL TESTS PASSED! 🎉${NC}"
    echo -e "${GREEN}Your workflow is ready for production!${NC}"
    exit 0
else
    echo -e "\n${RED}❌ Some tests failed. Please review the output above.${NC}"
    echo -e "${YELLOW}💡 Tip: Run individual test suites to debug specific issues.${NC}"
    exit 1
fi
