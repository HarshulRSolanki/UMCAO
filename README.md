# UMCAO (Universal Multi-Language Code Analyzer & Optimizer)

**UMCAO** is a full-stack developer platform designed for static code analysis, algorithmic complexity estimation, anti-pattern detection, and interactive refactoring advisory.

Built with a **modular architecture**, UMCAO currently features real static analysis for **Python** powered by Python's built-in `ast` module, alongside architectural roadmap stubs for **C, C++, Java, and JavaScript**.

---

## 🎨 Design System

- **Background Canvas:** Deep Black (`#09090B` / `#0A0A0A` / `#050505`)
- **Card & Surface Grayscale:** Dark Grey elevated panels (`#121214`, `#18181B`, `#1E1E22`) with subtle charcoal borders (`#27272A`)
- **Typography & Highlighting:** Crisp High-Contrast White (`#FAFAFA` / `#FFFFFF`) and Zinc Muted (`#A1A1AA`, `#71717A`)
- **Dashboard Interface:** Modern, responsive split-pane developer environment featuring a synchronized code editor, live metrics cards, tabbed results panel, and interactive Chart.js performance visualizations.

---

## 🚀 Core Features

1. **Source Code Editor Panel:**
   - Multi-language code editor with line-number gutter and auto-indentation.
   - Character count, line count, copy-to-clipboard, clear, and reset actions.
   - Quick preset selector with real-world inefficiency examples.
   - Keyboard shortcut support (`Ctrl + Enter` / `Cmd + Enter` to trigger analysis).

2. **Language Selector & Modular Roadmap:**
   - Languages: **Python** (Active), **C**, **C++**, **Java**, and **JavaScript** (Phase 2 Roadmap).
   - Clear, honest messaging for languages currently in development with planned engine specifications (e.g., Clang LibTooling, Tree-sitter, Javaparser, Babel).

3. **Real Static Analysis (Python AST Engine):**
   - **Syntax Error Detection:** Identifies exact line and column offsets with visual caret pointers and beginner-friendly remedial hints.
   - **Inefficient Pattern Detection:**
     - Repeated string concatenation in loops (`+=`) causing $O(N^2)$ memory reallocations.
     - Linear list membership checks (`item in my_list`) inside loops creating $O(N \cdot M)$ bottlenecks.
     - Unidiomatic loop indexing (`for i in range(len(x))`) vs `enumerate()`.
     - Un-memoized exponential branching recursion ($O(2^N)$ call trees).
     - Explicit length comparisons (`len(x) == 0`) vs Pythonic truth-value testing.
     - Resource leaks (unclosed files opened without `with` context managers).
     - Bare `except:` clauses swallowing critical system interrupts.
     - Redundant `.keys()` calls during dictionary iterations.
     - Loop accumulation with `.append()` vs list comprehensions.
     - Multiple consecutive print statements causing redundant I/O syscalls vs loop consolidation, single newline unpack, or helper functions.

4. **Complexity & Structural Estimation:**
   - Computes estimated **Time Complexity** ($O(1)$, $O(\log N)$, $O(N)$, $O(N^2)$, $O(2^N)$) and **Space Complexity**.
   - Structural AST breakdown: loop nesting depth, branching count, function/class volume, and total AST nodes.
   - **Explicit Uncertainty Reporting:** Notes runtime factors that cannot be statically determined without profiling (dynamic loop bounds, early breaks, external library routines).

5. **Actionable Optimization Suggestions:**
   - Side-by-side or before/after diff code previews.
   - Algorithmic and memory explanations explaining *why* the recommended change helps.
   - Clear disclaimer that real empirical gains depend on testing and hardware environment.

6. **Interactive Performance Dashboard (Chart.js):**
   - **Theoretical Scaling Model:** Multi-line graph comparing *Current Implementation* vs *Optimized Suggestion* across input sizes $N \in [10, 1000]$.
   - Linear and Logarithmic Y-axis toggle for high-order exponential or polynomial curves.
   - **Issue Breakdown Chart:** Doughnut chart categorizing detected rules.
   - **AST Structural Metrics:** Bar chart showing loop depth, branches, and node counts.

7. **Structured JSON Representation:**
   - Complete machine-readable analysis response in structured JSON with one-click Copy and `.json` file download.

---

## 🔒 Security & Safety Guarantee

- **Zero Server-Side Code Execution:** User code is strictly parsed into an in-memory Abstract Syntax Tree via Python's standard `ast.parse()` library. Code is **never executed, evaluated (`eval`/`exec`), or imported** on the server.
- **No Exposed Secrets:** Zero API keys, database credentials, or private tokens are embedded or exposed in frontend bundles.

---

## 🛠️ Technology Stack

| Layer | Technology |
|---|---|
| **Frontend** | React 19 (JSX), Vite 8, Tailwind CSS |
| **Charts** | Chart.js 4 & `react-chartjs-2` |
| **Icons** | Lucide React |
| **Backend** | Python 3.10+ / 3.14, FastAPI, Uvicorn, Pydantic v2 |
| **Analysis Engine** | Python standard library `ast` |
| **Architecture** | Pluggable `BaseAnalyzer` registry |

---

## 📦 Project Structure

```
UMCAO/
├── backend/
│   ├── main.py                     # FastAPI entry point & CORS configuration
│   ├── requirements.txt            # Python dependencies (fastapi, uvicorn, pydantic)
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py               # /api/analyze, /api/languages, /api/samples, /api/health
│   ├── analyzers/
│   │   ├── __init__.py
│   │   ├── base.py                 # Abstract BaseAnalyzer interface
│   │   ├── registry.py             # LanguageAnalyzerRegistry
│   │   ├── python_analyzer.py      # Real static AST analyzer
│   │   ├── c_analyzer.py           # Modular C roadmap stub
│   │   ├── cpp_analyzer.py         # Modular C++ roadmap stub
│   │   ├── java_analyzer.py        # Modular Java roadmap stub
│   │   └── javascript_analyzer.py  # Modular JavaScript roadmap stub
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py              # Pydantic request & response schemas
│   └── tests/
│       ├── __init__.py
│       └── test_analyzer.py        # Unit test suite for AST analysis
│
└── frontend/
    ├── package.json
    ├── vite.config.js              # Vite configuration with Tailwind CSS plugin
    ├── index.html
    └── src/
        ├── App.jsx                 # Main application dashboard
        ├── index.css               # Tailwind CSS & UMCAO color system (#174F4A, #FDFAF5)
        ├── services/
        │   └── api.js              # Fetch client communicating with FastAPI backend
        └── Component/
            ├── Navbar.jsx          # Header navigation, brand logo, status indicators
            ├── CodeEditorPanel.jsx # Monospace code editor with line numbers & presets
            ├── ResultsPanel.jsx    # Metrics cards, optimizations, patterns, and JSON tabs
            ├── PerformanceDashboard.jsx # Chart.js scaling curves, doughnut & bar charts
            ├── UnsupportedLanguageNotice.jsx # Clean roadmap notice for C, C++, Java, JS
            ├── DocsModal.jsx       # Architecture, complexity heuristics & safety docs
            └── Footer.jsx          # Application footer
```

---

## 🏃 Running the Application

### 1. Backend Setup (FastAPI)

1. Open a terminal and navigate to the backend directory:
   ```bash
   cd backend
   ```

2. (Optional) Create and activate a Python virtual environment:
   ```bash
   python -m venv venv
   # Windows:
   venv\Scripts\activate
   # Linux/macOS:
   source venv/bin/activate
   ```

3. Install backend dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run unit tests to verify analyzer correctness:
   ```bash
   python -m unittest tests/test_analyzer.py
   ```

5. Start the FastAPI development server:
   ```bash
   python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
   ```

   The backend will be available at:
   - API Root: `http://127.0.0.1:8000/`
   - Interactive Swagger API Docs: `http://127.0.0.1:8000/docs`
   - Health Check: `http://127.0.0.1:8000/api/health`

---

### 2. Frontend Setup (React + Vite)

1. Open a second terminal and navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the Vite development server:
   ```bash
   npm run dev
   ```

4. Open your browser and navigate to the local URL displayed (e.g. `http://localhost:5173/` or `http://localhost:5174/`).

---

## 🧪 Testing Presets Available in UMCAO

You can instantly test the analyzer using the preset selector dropdown in the code editor:

- **Quadratic Nested Loop ($O(N^2)$):** Flags pairwise search and recommends hash table / dictionary indexing.
- **String Concatenation in Loop (`+=`):** Flags quadratic memory reallocations and suggests `''.join(...)`.
- **Un-memoized Fibonacci ($O(2^N)$):** Flags exponential recursion branching and suggests `@functools.lru_cache`.
- **List Membership in Loop:** Identifies linear $O(M)$ scan inside loop and suggests set conversion.
- **Syntax Error Example:** Demonstrates real-time syntax error diagnosis with line and column highlighting.
- **Multiple Consecutive Print Statements:** Flags repeated print calls and recommends a loop (`for`), single newline separator (`print(*items, sep='\n')`), or helper functions.
- **Clean Python Example:** Demonstrates a clean, idiomatic $O(N)$ implementation.
- **C, C++, Java, JavaScript Samples:** Demonstrates the modular roadmap and unsupported language messaging.
