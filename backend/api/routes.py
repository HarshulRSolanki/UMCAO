"""API router for UMCAO."""

from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, status
from models.schemas import AnalyzeRequest, AnalyzeResponse
from analyzers.registry import analyzer_registry

router = APIRouter(prefix="/api", tags=["Analyzer"])


SAMPLE_CODE_PRESETS = {
    "python": [
        {
            "id": "py-quadratic",
            "title": "Quadratic Nested Loop (O(N²))",
            "description": "Two nested loops comparing items pairwise without indexing.",
            "code": """def find_duplicate_pairs(list_a, list_b):
    # Inefficient pairwise comparison with O(N^2) complexity
    duplicates = []
    for a in list_a:
        for b in list_b:
            if a == b:
                duplicates.append((a, b))
    return duplicates
""",
        },
        {
            "id": "py-str-concat",
            "title": "String Concatenation in Loop (+=)",
            "description": "Repeated in-place string reallocation inside a loop.",
            "code": """def build_csv_report(records):
    # Inefficient string += reallocation inside loop
    header = "ID,Name,Value\\n"
    report = header
    for record in records:
        report += str(record['id']) + "," + record['name'] + "," + str(record['val']) + "\\n"
    return report
""",
        },
        {
            "id": "py-fib-recursion",
            "title": "Un-memoized Fibonacci (O(2^N))",
            "description": "Branching recursive self-calls without dynamic programming or caching.",
            "code": """def fibonacci(n):
    # Exponential recursive branching: O(2^N) time, O(N) call stack
    if n <= 0:
        return 0
    elif n == 1:
        return 1
    return fibonacci(n - 1) + fibonacci(n - 2)
""",
        },
        {
            "id": "py-list-membership",
            "title": "List Membership in Loop (O(N*M))",
            "description": "Linear lookup in list instead of constant-time set lookup.",
            "code": """def filter_banned_users(users, banned_list):
    # Linear list search inside loop yields quadratic behavior
    active = []
    for user in users:
        if user not in banned_list:
            active.append(user)
    return active
""",
        },
        {
            "id": "py-idiomatic-issues",
            "title": "Unidiomatic Iteration & Length Checks",
            "description": "Demonstrates range(len()) anti-pattern and explicit len() == 0 checks.",
            "code": """def process_items(items):
    # Unidiomatic range(len(items)) and explicit len == 0
    if len(items) == 0:
        return []

    results = []
    for i in range(len(items)):
        val = items[i]
        results.append(val * 2)

    return results
""",
        },
        {
            "id": "py-multiple-prints",
            "title": "Multiple Consecutive Print Statements",
            "description": "Repeated print calls that can be optimized using a loop or helper function.",
            "code": """def display_user_dashboard(user_name, score, rank, status):
    # Repeated consecutive print calls (I/O & DRY anti-pattern)
    print("=== User Dashboard ===")
    print("Name: " + str(user_name))
    print("Score: " + str(score))
    print("Rank: " + str(rank))
    print("Status: " + str(status))
    print("======================")
""",
        },
        {
            "id": "py-syntax-error",
            "title": "Syntax Error Example",
            "description": "Shows real-time syntax error diagnosis with line and column highlighting.",
            "code": """def calculate_total(prices, tax_rate)
    # Notice the missing colon on the function header above!
    total = 0
    for price in prices:
        total += price * (1 + tax_rate)
    return total
""",
        },
        {
            "id": "py-clean",
            "title": "Clean, Optimized Python Code",
            "description": "Idiomatic, linear O(N) Python code using list comprehensions and sets.",
            "code": """def get_unique_transactions(transactions, valid_ids):
    # Optimized: O(M) set conversion + O(N) single-pass comprehension
    valid_id_set = set(valid_ids)
    return [tx for tx in transactions if tx.id in valid_id_set]
""",
        },
    ],
    "c": [
        {
            "id": "c-sample",
            "title": "C Pointer & Buffer Example",
            "description": "Sample C code to demonstrate unsupported language roadmap notification.",
            "code": """#include <stdio.h>
#include <stdlib.h>
#include <string.h>

void process_data(const char* input) {
    char buffer[64];
    // Potential unsafe copy and dynamic allocation
    strcpy(buffer, input);
    printf("Processed: %s\\n", buffer);
}

int main() {
    process_data("UMCAO C Static Analysis Demo");
    return 0;
}
""",
        }
    ],
    "cpp": [
        {
            "id": "cpp-sample",
            "title": "C++ Vector Copy Example",
            "description": "Sample C++ code illustrating heavy pass-by-value opportunities.",
            "code": """#include <iostream>
#include <vector>
#include <string>

// Pass-by-value induces deep copy of large vector
void analyzeItems(std::vector<std::string> items) {
    for (const auto& item : items) {
        std::cout << item << std::endl;
    }
}

int main() {
    std::vector<std::string> data = {"alpha", "beta", "gamma"};
    analyzeItems(data);
    return 0;
}
""",
        }
    ],
    "java": [
        {
            "id": "java-sample",
            "title": "Java String Concatenation Loop",
            "description": "Sample Java code with loop concatenation and boxing.",
            "code": """public class OrderProcessor {
    public static String buildReceipt(String[] items, double[] prices) {
        String receipt = "Order Summary:\\n";
        for (int i = 0; i < items.length; i++) {
            // Inefficient string concatenation in loop; StringBuilder preferred
            receipt += items[i] + ": $" + prices[i] + "\\n";
        }
        return receipt;
    }
}
""",
        }
    ],
    "javascript": [
        {
            "id": "js-sample",
            "title": "JavaScript Async Loop & Closure",
            "description": "Sample JS code demonstrating sequential await and chained iterations.",
            "code": """async function fetchUserReports(userIds) {
    const results = [];
    // Sequential await inside for-loop creates unnecessary latency bottleneck
    for (const id of userIds) {
        const res = await fetch(`/api/users/${id}`);
        const data = await res.json();
        results.push(data);
    }
    return results;
}
""",
        }
    ],
}


@router.post("/analyze", response_model=AnalyzeResponse)
def analyze_code(request: AnalyzeRequest):
    """Analyze source code statically. Never executes user code on the server."""
    analyzer = analyzer_registry.get_analyzer(request.language)
    if not analyzer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Language '{request.language}' is not recognized. Supported/recognized languages: Python, C, C++, Java, JavaScript.",
        )

    return analyzer.analyze(request.code, request.options)


@router.get("/languages")
def get_languages():
    """List recognized languages, their support state, and planned analysis engines."""
    return {
        "status": "success",
        "languages": analyzer_registry.list_languages(),
    }


@router.get("/samples")
def get_sample_presets(language: str = "python"):
    """Get curated preset code samples for demonstration and testing."""
    norm_lang = language.strip().lower()
    samples = SAMPLE_CODE_PRESETS.get(norm_lang, [])
    return {
        "language": norm_lang,
        "samples": samples,
    }


@router.get("/health")
def health_check():
    """Health status and metadata."""
    return {
        "status": "healthy",
        "service": "UMCAO Backend Analysis Engine",
        "version": "1.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "safety": "Static AST parsing only; user code execution is strictly prohibited.",
    }
