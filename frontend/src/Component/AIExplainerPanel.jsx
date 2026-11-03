import React, { useState, useRef, useEffect } from 'react';
import {
  Sparkles,
  Play,
  RotateCcw,
  Copy,
  Check,
  Trash2,
  MessageSquare,
  Send,
  HelpCircle,
  FileCode,
  Layers,
  Clock,
  HardDrive,
  Cpu,
  BookOpen,
  ArrowRight,
  Zap,
  CheckCircle2,
  AlertCircle,
  Code2,
  ChevronDown,
  ChevronUp,
  Maximize2,
  Minimize2,
} from 'lucide-react';
import { explainCodeWithAI, sendAIChat } from '../services/api';

const CODE_PRESETS = {
  python: [
    {
      id: 'py-bubble',
      title: 'Python: Bubble Sort Algorithm',
      code: `def bubble_sort(arr):
    n = len(arr)
    for i in range(n):
        swapped = False
        for j in range(0, n - i - 1):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
                swapped = True
        if not swapped:
            break
    return arr

# Test example
numbers = [64, 34, 25, 12, 22, 11, 90]
print("Sorted:", bubble_sort(numbers))`,
    },
    {
      id: 'py-two-sum',
      title: 'Python: Two Sum (Hash Map O(N))',
      code: `def two_sum(nums, target):
    seen = {}
    for index, num in enumerate(nums):
        complement = target - num
        if complement in seen:
            return [seen[complement], index]
        seen[num] = index
    return []

# Test example
print(two_sum([2, 7, 11, 15], 9))  # Output: [0, 1]`,
    },
    {
      id: 'py-fibonacci',
      title: 'Python: Fibonacci with Memoization',
      code: `def fib_memo(n, cache=None):
    if cache is None:
        cache = {}
    if n in cache:
        return cache[n]
    if n <= 1:
        return n
    cache[n] = fib_memo(n - 1, cache) + fib_memo(n - 2, cache)
    return cache[n]

print("Fib(10) =", fib_memo(10))`,
    },
  ],
  c: [
    {
      id: 'c-reverse',
      title: 'C: Array In-Place Reversal',
      code: `#include <stdio.h>

void reverse_array(int arr[], int size) {
    int start = 0;
    int end = size - 1;
    while (start < end) {
        int temp = arr[start];
        arr[start] = arr[end];
        arr[end] = temp;
        start++;
        end--;
    }
}

int main() {
    int data[] = {1, 2, 3, 4, 5};
    int n = sizeof(data) / sizeof(data[0]);
    reverse_array(data, n);
    for (int i = 0; i < n; i++) {
        printf("%d ", data[i]);
    }
    return 0;
}`,
    },
    {
      id: 'c-palindrome',
      title: 'C: String Palindrome Checker',
      code: `#include <stdio.h>
#include <string.h>
#include <stdbool.h>

bool is_palindrome(const char *str) {
    int left = 0;
    int right = strlen(str) - 1;
    while (left < right) {
        if (str[left] != str[right]) {
            return false;
        }
        left++;
        right--;
    }
    return true;
}

int main() {
    const char *word = "radar";
    if (is_palindrome(word)) {
        printf("%s is a palindrome\\n", word);
    }
    return 0;
}`,
    },
  ],
  cpp: [
    {
      id: 'cpp-binary-search',
      title: 'C++: Binary Search Algorithm',
      code: `#include <iostream>
#include <vector>

int binarySearch(const std::vector<int>& arr, int target) {
    int low = 0;
    int high = arr.size() - 1;
    while (low <= high) {
        int mid = low + (high - low) / 2;
        if (arr[mid] == target) return mid;
        if (arr[mid] < target) low = mid + 1;
        else high = mid - 1;
    }
    return -1;
}

int main() {
    std::vector<int> nums = {2, 5, 8, 12, 16, 23, 38, 56, 72, 91};
    int target = 23;
    int index = binarySearch(nums, target);
    std::cout << "Target found at index: " << index << std::endl;
    return 0;
}`,
    },
  ],
  java: [
    {
      id: 'java-twosum',
      title: 'Java: Two Sum with HashMap',
      code: `import java.util.HashMap;
import java.util.Map;

public class TwoSum {
    public static int[] findTwoSum(int[] nums, int target) {
        Map<Integer, Integer> map = new HashMap<>();
        for (int i = 0; i < nums.length; i++) {
            int complement = target - nums[i];
            if (map.containsKey(complement)) {
                return new int[] { map.get(complement), i };
            }
            map.put(nums[i], i);
        }
        return new int[0];
    }

    public static void main(String[] args) {
        int[] result = findTwoSum(new int[]{3, 2, 4}, 6);
        System.out.println("Indices: " + result[0] + ", " + result[1]);
    }
}`,
    },
  ],
  javascript: [
    {
      id: 'js-fetch-retry',
      title: 'JavaScript: Async Fetch with Retry',
      code: `async function fetchWithRetry(url, retries = 3, delayMs = 1000) {
    for (let attempt = 1; attempt <= retries; attempt++) {
        try {
            const response = await fetch(url);
            if (!response.ok) throw new Error(\`HTTP \${response.status}\`);
            return await response.json();
        } catch (error) {
            console.warn(\`Attempt \${attempt} failed: \${error.message}\`);
            if (attempt === retries) throw error;
            await new Promise(res => setTimeout(res, delayMs));
        }
    }
}

// Example invocation
fetchWithRetry('https://api.github.com/zen')
    .then(data => console.log('Success:', data))
    .catch(err => console.error('All retries failed:', err));`,
    },
  ],
};

const MODES = [
  { id: 'simple', label: 'Simple Explanation', desc: 'Easy beginner-friendly explanation without complex jargon.' },
  { id: 'line_by_line', label: 'Line-by-Line', desc: 'Step-by-step breakdown explaining each important statement in order.' },
  { id: 'detailed', label: 'Detailed Explanation', desc: 'Comprehensive dive into logic, variables, functions, and control flow.' },
  { id: 'algorithm', label: 'Algorithm Breakdown', desc: 'Algorithmic strategy, state transitions, and step-by-step trace.' },
  { id: 'interview', label: 'Interview Preparation', desc: 'Technical interview presentation, key talking points, and Q&A.' },
  { id: 'optimization', label: 'Code Optimization', desc: 'Bottleneck diagnosis, edge cases, and algorithmic improvements.' },
];

const EXPLANATION_LANGUAGES = [
  { id: 'english', label: 'English', native: 'English' },
  { id: 'gujarati', label: 'Gujarati', native: 'ગુજરાતી' },
  { id: 'hindi', label: 'Hindi', native: 'हिन्दी' },
];

const CODE_LANGUAGES = [
  { id: 'python', label: 'Python' },
  { id: 'c', label: 'C' },
  { id: 'cpp', label: 'C++' },
  { id: 'java', label: 'Java' },
  { id: 'javascript', label: 'JavaScript' },
];

const SUGGESTED_PROMPTS = [
  'Why is this loop used?',
  'Explain this function in Gujarati',
  'What happens if I change this condition?',
  'Can you explain this code with an example?',
  'Can you make this code easier for beginners?',
  'What questions can an interviewer ask about this program?',
];

export default function AIExplainerPanel() {
  const [code, setCode] = useState(CODE_PRESETS.python[0].code);
  const [language, setLanguage] = useState('python');
  const [mode, setMode] = useState('detailed');
  const [explanationLanguage, setExplanationLanguage] = useState('english');

  const [isLoading, setIsLoading] = useState(false);
  const [explanationResult, setExplanationResult] = useState(null);
  const [errorMessage, setErrorMessage] = useState(null);
  const [copiedAll, setCopiedAll] = useState(false);
  const [copiedSection, setCopiedSection] = useState(null);
  const [viewRawMarkdown, setViewRawMarkdown] = useState(false);

  // Chat State
  const [chatMessages, setChatMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isChatSending, setIsChatSending] = useState(false);
  const [chatError, setChatError] = useState(null);

  const textareaRef = useRef(null);
  const lineNumbersRef = useRef(null);
  const chatBottomRef = useRef(null);

  // Sync scroll
  const handleScroll = () => {
    if (textareaRef.current && lineNumbersRef.current) {
      lineNumbersRef.current.scrollTop = textareaRef.current.scrollTop;
    }
  };

  // Scroll chat to bottom on new messages
  useEffect(() => {
    chatBottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatMessages, isChatSending]);

  // Tab key indent
  const handleKeyDown = (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      e.preventDefault();
      handleExplain();
      return;
    }

    if (e.key === 'Tab') {
      e.preventDefault();
      const start = e.target.selectionStart;
      const end = e.target.selectionEnd;
      const newCode = code.substring(0, start) + '    ' + code.substring(end);
      setCode(newCode);
      setTimeout(() => {
        if (textareaRef.current) {
          textareaRef.current.selectionStart = textareaRef.current.selectionEnd = start + 4;
        }
      }, 0);
    }
  };

  const handleLanguageChange = (newLang) => {
    setLanguage(newLang);
    const presets = CODE_PRESETS[newLang];
    if (presets && presets.length > 0) {
      setCode(presets[0].code);
    }
    setErrorMessage(null);
  };

  const handleExplain = async () => {
    if (!code.trim()) {
      setErrorMessage('Please enter or select code to explain.');
      return;
    }

    setIsLoading(true);
    setErrorMessage(null);

    try {
      const data = await explainCodeWithAI({
        code,
        language,
        mode,
        explanationLanguage,
      });

      if (data.success) {
        setExplanationResult(data);
      } else {
        setErrorMessage(data.error || 'Failed to explain code.');
      }
    } catch (err) {
      setErrorMessage(err.message || 'Gemini API explanation request failed.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleCopyAll = () => {
    if (!explanationResult) return;
    const textToCopy = explanationResult.markdown;
    navigator.clipboard.writeText(textToCopy);
    setCopiedAll(true);
    setTimeout(() => setCopiedAll(false), 2000);
  };

  const handleCopySection = (sectionKey, text) => {
    navigator.clipboard.writeText(text);
    setCopiedSection(sectionKey);
    setTimeout(() => setCopiedSection(null), 2000);
  };

  const handleClear = () => {
    setCode('');
    setExplanationResult(null);
    setErrorMessage(null);
  };

  // Follow-up Chat Handlers
  const handleSendMessage = async (msgToSend = null) => {
    const text = (msgToSend || inputMessage).trim();
    if (!text || isChatSending) return;

    const newHistory = [...chatMessages, { role: 'user', content: text }];
    setChatMessages(newHistory);
    setInputMessage('');
    setIsChatSending(true);
    setChatError(null);

    try {
      const res = await sendAIChat({
        code,
        message: text,
        language,
        explanationLanguage,
        history: chatMessages,
      });

      if (res.success) {
        setChatMessages([...newHistory, { role: 'model', content: res.reply }]);
      } else {
        setChatError(res.error || 'Chat response failed.');
      }
    } catch (err) {
      setChatError(err.message || 'Failed to communicate with Gemini assistant.');
    } finally {
      setIsChatSending(false);
    }
  };

  const handleResetChat = () => {
    setChatMessages([]);
    setChatError(null);
  };

  const lineCount = Math.max(code.split('\n').length, 1);
  const linesArray = Array.from({ length: lineCount }, (_, i) => i + 1);

  const sections = explanationResult?.sections;

  // Simple Markdown renderer for sections
  const renderFormattedMarkdown = (rawText) => {
    if (!rawText) return <p className="text-zinc-500 italic text-xs">Not specified or not applicable.</p>;

    // Split paragraphs
    const paragraphs = rawText.split('\n\n');
    return (
      <div className="space-y-2 text-sm text-zinc-800 leading-relaxed font-sans">
        {paragraphs.map((p, idx) => {
          // If bullet points
          if (p.trim().startsWith('- ') || p.trim().startsWith('* ')) {
            const items = p.split('\n').filter((item) => item.trim());
            return (
              <ul key={idx} className="list-disc list-inside space-y-1 pl-1">
                {items.map((item, iIdx) => (
                  <li key={iIdx} className="text-zinc-800">
                    {item.replace(/^[-*]\s+/, '')}
                  </li>
                ))}
              </ul>
            );
          }
          // If numbered list
          if (/^\d+\.\s+/.test(p.trim())) {
            const items = p.split('\n').filter((item) => item.trim());
            return (
              <ol key={idx} className="list-decimal list-inside space-y-1 pl-1">
                {items.map((item, iIdx) => (
                  <li key={iIdx} className="text-zinc-800">
                    {item.replace(/^\d+\.\s+/, '')}
                  </li>
                ))}
              </ol>
            );
          }
          // If code block
          if (p.trim().startsWith('```')) {
            const codeBlock = p.replace(/^```[a-z]*\n?|```$/gi, '');
            return (
              <pre key={idx} className="p-3 bg-[#174F4A]/5 border border-[#174F4A]/20 rounded-lg text-xs font-mono overflow-x-auto text-[#174F4A]">
                {codeBlock}
              </pre>
            );
          }
          return <p key={idx}>{p}</p>;
        })}
      </div>
    );
  };

  return (
    <div className="space-y-6">
      {/* Top Banner & Title */}
      <div className="bg-white rounded-2xl p-6 shadow-xs border border-[#E5E9E5] flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2.5">
            <span className="p-2 rounded-xl bg-[#174F4A]/10 text-[#174F4A]">
              <Sparkles className="w-5 h-5 text-[#174F4A]" />
            </span>
            <h1 className="text-xl font-bold tracking-tight text-[#202824]">Gemini AI Code Explainer</h1>
            <span className="text-[11px] font-mono px-2.5 py-0.5 rounded-full bg-[#F0FDF4] text-[#21865A] border border-[#BBF7D0] font-semibold">
              gemini-3.5-flash-lite
            </span>
          </div>
          <p className="text-xs text-[#68736D] mt-1 max-w-2xl leading-relaxed">
            Submit code in Python, C, C++, Java, or JavaScript and receive comprehensive, step-by-step explanations in English,
            Gujarati, or Hindi across 6 specialized learning modes.
          </p>
        </div>

        {/* Quick Language Pills */}
        <div className="flex flex-wrap items-center gap-2">
          {EXPLANATION_LANGUAGES.map((lang) => (
            <button
              key={lang.id}
              onClick={() => setExplanationLanguage(lang.id)}
              className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition-all cursor-pointer ${
                explanationLanguage === lang.id
                  ? 'bg-[#174F4A] text-white shadow-xs font-bold'
                  : 'bg-[#F3F5F2] hover:bg-[#E5E9E5] text-[#202824] border border-[#E5E9E5]'
              }`}
            >
              <span>{lang.native}</span>
              <span className="text-[10px] ml-1 opacity-70">({lang.label})</span>
            </button>
          ))}
        </div>
      </div>

      {/* Control Navigation Bar */}
      <div className="bg-white rounded-2xl p-4 shadow-xs border border-[#E5E9E5] flex flex-wrap items-center justify-between gap-4 text-[#202824]">
        {/* Left: Code Language & Mode Selection */}
        <div className="flex flex-wrap items-center gap-3">
          {/* Source Code Language */}
          <div className="flex items-center space-x-2">
            <label className="text-xs font-bold text-[#68736D] uppercase tracking-wider">Source:</label>
            <select
              value={language}
              onChange={(e) => handleLanguageChange(e.target.value)}
              className="text-xs font-semibold bg-[#F3F5F2] border border-[#E5E9E5] text-[#202824] rounded-lg px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-[#174F4A] transition-all cursor-pointer shadow-xs"
            >
              {CODE_LANGUAGES.map((lang) => (
                <option key={lang.id} value={lang.id}>
                  {lang.label}
                </option>
              ))}
            </select>
          </div>

          {/* Explanation Mode */}
          <div className="flex items-center space-x-2">
            <label className="text-xs font-bold text-[#68736D] uppercase tracking-wider">Mode:</label>
            <select
              value={mode}
              onChange={(e) => setMode(e.target.value)}
              className="text-xs font-semibold bg-[#F3F5F2] border border-[#E5E9E5] text-[#202824] rounded-lg px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-[#174F4A] transition-all cursor-pointer shadow-xs"
            >
              {MODES.map((m) => (
                <option key={m.id} value={m.id}>
                  {m.label}
                </option>
              ))}
            </select>
          </div>

          {/* Presets */}
          {CODE_PRESETS[language] && (
            <div className="flex items-center space-x-2">
              <select
                onChange={(e) => {
                  const found = CODE_PRESETS[language].find((p) => p.id === e.target.value);
                  if (found) {
                    setCode(found.code);
                    setExplanationResult(null);
                    setErrorMessage(null);
                  }
                  e.target.value = '';
                }}
                defaultValue=""
                className="text-xs bg-[#F3F5F2] border border-[#E5E9E5] text-[#202824] hover:bg-white rounded-lg px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-[#174F4A] transition-all cursor-pointer font-medium shadow-xs"
              >
                <option value="" disabled className="text-[#68736D]">
                  ⚡ Preset Samples...
                </option>
                {CODE_PRESETS[language].map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.title}
                  </option>
                ))}
              </select>
            </div>
          )}
        </div>

        {/* Right: Actions */}
        <div className="flex items-center space-x-2">
          <button
            onClick={handleClear}
            className="p-1.5 px-3 text-xs text-[#68736D] hover:text-[#D64545] hover:bg-[#FEF2F2] rounded-lg border border-[#E5E9E5] hover:border-[#FECACA] transition-all flex items-center space-x-1 cursor-pointer bg-white"
            title="Clear Editor and Explanation"
          >
            <Trash2 className="w-3.5 h-3.5" />
            <span>Clear</span>
          </button>
        </div>
      </div>

      {/* Main Two-Column Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Column: Code Editor (6 cols) */}
        <div className="lg:col-span-6 flex flex-col h-full bg-white rounded-2xl shadow-xs border border-[#E5E9E5] overflow-hidden">
          {/* Editor Header */}
          <div className="bg-[#F3F5F2] px-4 py-2.5 border-b border-[#E5E9E5] flex items-center justify-between text-xs text-[#202824]">
            <div className="flex items-center space-x-2">
              <Code2 className="w-4 h-4 text-[#174F4A]" />
              <span className="font-bold uppercase tracking-wider text-[#202824]">{language} Code</span>
              <span className="text-[#8E9993]">•</span>
              <span className="text-[#68736D]">{lineCount} lines</span>
            </div>
            <button
              onClick={() => {
                navigator.clipboard.writeText(code);
                setCopiedAll(true);
                setTimeout(() => setCopiedAll(false), 2000);
              }}
              className="text-[#68736D] hover:text-[#202824] flex items-center space-x-1 cursor-pointer"
            >
              {copiedAll ? <Check className="w-3.5 h-3.5 text-[#21865A]" /> : <Copy className="w-3.5 h-3.5" />}
              <span className="text-[11px]">{copiedAll ? 'Copied' : 'Copy'}</span>
            </button>
          </div>

          {/* Textarea with Gutter */}
          <div className="relative flex-1 min-h-[380px] lg:min-h-[500px] bg-white flex text-[#202824] font-mono text-[13px] leading-relaxed">
            <div
              ref={lineNumbersRef}
              className="w-12 py-3 bg-[#F3F5F2] text-[#68736D] text-right pr-3 select-none overflow-hidden border-r border-[#E5E9E5] shrink-0 font-mono text-[12px]"
            >
              {linesArray.map((num) => (
                <div key={num} className="leading-relaxed">
                  {num}
                </div>
              ))}
            </div>

            <textarea
              ref={textareaRef}
              value={code}
              onChange={(e) => setCode(e.target.value)}
              onScroll={handleScroll}
              onKeyDown={handleKeyDown}
              placeholder="Paste or write your code here..."
              spellCheck="false"
              className="flex-1 w-full h-full p-3 bg-white text-[#202824] selection:bg-[#174F4A]/15 selection:text-[#174F4A] resize-none outline-none font-mono leading-relaxed overflow-auto focus:ring-0 focus:outline-none placeholder:text-[#8E9993]"
            />
          </div>

          {/* Action Bar */}
          <div className="bg-[#F3F5F2] px-4 py-3 border-t border-[#E5E9E5] flex items-center justify-between">
            <span className="text-[11px] text-[#68736D] font-mono hidden sm:inline">Ctrl + Enter</span>
            <button
              onClick={handleExplain}
              disabled={isLoading}
              className={`w-full sm:w-auto flex items-center justify-center space-x-2 px-6 py-2.5 rounded-xl text-xs font-bold shadow-xs transition-all ${
                isLoading
                  ? 'bg-zinc-200 text-zinc-500 cursor-not-allowed border border-zinc-300'
                  : 'bg-[#174F4A] hover:bg-[#123E3A] text-white active:scale-98 cursor-pointer'
              }`}
            >
              {isLoading ? (
                <>
                  <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-emerald-300" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path>
                  </svg>
                  <span>Explaining with Gemini...</span>
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4 text-amber-300" />
                  <span>Explain with Gemini AI</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* Right Column: AI Explanation (6 cols) */}
        <div className="lg:col-span-6 space-y-6">
          {/* Error Notice */}
          {errorMessage && (
            <div className="p-4 rounded-xl bg-[#FEF2F2] border border-[#FECACA] text-[#D64545] flex items-start space-x-3">
              <AlertCircle className="w-5 h-5 text-[#D64545] shrink-0 mt-0.5" />
              <div className="text-xs">
                <span className="font-bold text-[#D64545]">Explanation Error: </span>
                <span>{errorMessage}</span>
              </div>
            </div>
          )}

          {/* Loading Animation Card */}
          {isLoading && (
            <div className="bg-white rounded-2xl shadow-xs border border-[#E5E9E5] p-10 flex flex-col items-center justify-center min-h-[460px] text-center">
              <div className="relative mb-6">
                <div className="w-16 h-16 rounded-2xl bg-[#174F4A] text-white flex items-center justify-center shadow-lg animate-bounce">
                  <Sparkles className="w-8 h-8 text-amber-300 animate-spin" />
                </div>
                <span className="absolute -bottom-2 -right-2 flex h-5 w-5">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-5 w-5 bg-emerald-500"></span>
                </span>
              </div>
              <h3 className="text-xl font-bold text-[#202824]">Gemini AI is analyzing your code...</h3>
              <p className="text-xs text-[#68736D] mt-2 max-w-md leading-relaxed">
                Synthesizing step-by-step logic, inspecting variable flows, calculating theoretical Big-O complexity, and formatting
                explanations in <strong>{explanationLanguage.toUpperCase()}</strong>.
              </p>
              <div className="mt-6 flex flex-wrap gap-2 justify-center text-xs text-[#68736D]">
                <span className="px-3 py-1 bg-[#F3F5F2] rounded-full border border-[#E5E9E5] shadow-xs">Analyzing flow</span>
                <span className="px-3 py-1 bg-[#F3F5F2] rounded-full border border-[#E5E9E5] shadow-xs">Formulating 11 sections</span>
                <span className="px-3 py-1 bg-[#F3F5F2] rounded-full border border-[#E5E9E5] shadow-xs">Ensuring token accuracy</span>
              </div>
            </div>
          )}

          {/* Empty State Card */}
          {!isLoading && !explanationResult && (
            <div className="bg-white rounded-2xl shadow-xs border border-[#E5E9E5] p-10 flex flex-col items-center justify-center min-h-[460px] text-center">
              <div className="w-16 h-16 rounded-2xl bg-[#174F4A]/10 text-[#174F4A] flex items-center justify-center mb-4 border border-[#174F4A]/20 shadow-xs">
                <Sparkles className="w-8 h-8 text-[#174F4A]" />
              </div>
              <h3 className="text-xl font-bold text-[#202824]">Ready to Explain Your Code</h3>
              <p className="text-xs text-[#68736D] mt-2 max-w-md leading-relaxed">
                Select your desired programming language, explanation style, and output language, then click{' '}
                <strong className="text-[#174F4A]">"Explain with Gemini AI"</strong> to receive an 11-section structured breakdown.
              </p>

              <div className="mt-6 grid grid-cols-2 sm:grid-cols-3 gap-3 w-full max-w-lg text-left">
                {MODES.map((m) => (
                  <div key={m.id} className="p-3 bg-[#F3F5F2] rounded-xl border border-[#E5E9E5] shadow-xs">
                    <span className="text-xs font-bold text-[#174F4A] block">{m.label}</span>
                    <span className="text-[11px] text-[#68736D] leading-tight block mt-0.5 line-clamp-2">{m.desc}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Structured 11-Section Explanation Output */}
          {!isLoading && explanationResult && (
            <div className="space-y-4">
              {/* Output Top Bar */}
              <div className="bg-white rounded-xl p-4 shadow-xs border border-[#E5E9E5] flex flex-wrap items-center justify-between gap-3 text-xs">
                <div className="flex items-center space-x-2">
                  <span className="px-2.5 py-1 rounded-md bg-[#174F4A] text-white font-bold uppercase tracking-wider text-[11px]">
                    {explanationResult.mode.replace('_', ' ')}
                  </span>
                  <span className="px-2.5 py-1 rounded-md bg-[#F3F5F2] border border-[#E5E9E5] text-[#202824] font-semibold uppercase text-[11px]">
                    {explanationResult.explanation_language}
                  </span>
                  <span className="text-[#68736D] font-mono text-[11px] hidden sm:inline">
                    model: {explanationResult.model_used}
                  </span>
                </div>

                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => setViewRawMarkdown(!viewRawMarkdown)}
                    className="px-2.5 py-1 rounded-lg text-xs font-medium bg-[#F3F5F2] hover:bg-[#E5E9E5] border border-[#E5E9E5] text-[#202824] transition-all cursor-pointer"
                  >
                    {viewRawMarkdown ? 'Structured View' : 'Raw Markdown'}
                  </button>
                  <button
                    onClick={handleCopyAll}
                    className="px-3 py-1 rounded-lg text-xs font-semibold bg-[#174F4A] hover:bg-[#123E3A] text-white shadow-xs transition-all flex items-center space-x-1 cursor-pointer"
                  >
                    {copiedAll ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
                    <span>{copiedAll ? 'Copied All' : 'Copy All'}</span>
                  </button>
                </div>
              </div>

              {/* Raw Markdown View */}
              {viewRawMarkdown ? (
                <div className="bg-white rounded-xl p-6 shadow-xs border border-[#E5E9E5] text-[#202824] font-mono text-xs whitespace-pre-wrap leading-relaxed overflow-x-auto">
                  {explanationResult.markdown}
                </div>
              ) : (
                /* 11 Structured Cards */
                <div className="space-y-4">
                  {/* 1. Code Overview */}
                  <SectionCard
                    number="1"
                    title="Code Overview"
                    icon={<FileCode className="w-4 h-4 text-[#174F4A]" />}
                    content={renderFormattedMarkdown(sections?.code_overview)}
                    rawContent={sections?.code_overview}
                    copiedSection={copiedSection}
                    onCopy={handleCopySection}
                    sectionKey="overview"
                  />

                  {/* 2. Purpose */}
                  <SectionCard
                    number="2"
                    title="Purpose"
                    icon={<Zap className="w-4 h-4 text-[#174F4A]" />}
                    content={renderFormattedMarkdown(sections?.purpose)}
                    rawContent={sections?.purpose}
                    copiedSection={copiedSection}
                    onCopy={handleCopySection}
                    sectionKey="purpose"
                  />

                  {/* 3. Line-by-Line Explanation */}
                  <SectionCard
                    number="3"
                    title="Line-by-Line Explanation"
                    icon={<Code2 className="w-4 h-4 text-[#174F4A]" />}
                    content={renderFormattedMarkdown(sections?.line_by_line)}
                    rawContent={sections?.line_by_line}
                    copiedSection={copiedSection}
                    onCopy={handleCopySection}
                    sectionKey="line_by_line"
                  />

                  {/* 4. Variables and Functions */}
                  <SectionCard
                    number="4"
                    title="Variables and Functions"
                    icon={<Layers className="w-4 h-4 text-[#174F4A]" />}
                    content={renderFormattedMarkdown(sections?.variables_and_functions)}
                    rawContent={sections?.variables_and_functions}
                    copiedSection={copiedSection}
                    onCopy={handleCopySection}
                    sectionKey="vars_funcs"
                  />

                  {/* 5. Logic and Workflow */}
                  <SectionCard
                    number="5"
                    title="Logic and Workflow"
                    icon={<ArrowRight className="w-4 h-4 text-[#174F4A]" />}
                    content={renderFormattedMarkdown(sections?.logic_and_workflow)}
                    rawContent={sections?.logic_and_workflow}
                    copiedSection={copiedSection}
                    onCopy={handleCopySection}
                    sectionKey="logic_workflow"
                  />

                  {/* 6. Algorithm */}
                  <SectionCard
                    number="6"
                    title="Algorithm"
                    icon={<Cpu className="w-4 h-4 text-[#174F4A]" />}
                    content={renderFormattedMarkdown(sections?.algorithm)}
                    rawContent={sections?.algorithm}
                    copiedSection={copiedSection}
                    onCopy={handleCopySection}
                    sectionKey="algorithm"
                  />

                  {/* 7. Example Input and Output */}
                  <SectionCard
                    number="7"
                    title="Example Input and Output"
                    icon={<CheckCircle2 className="w-4 h-4 text-[#174F4A]" />}
                    content={renderFormattedMarkdown(sections?.example_input_output)}
                    rawContent={sections?.example_input_output}
                    copiedSection={copiedSection}
                    onCopy={handleCopySection}
                    sectionKey="io_example"
                  />

                  {/* Complexity Row: 8. Time & 9. Space */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <SectionCard
                      number="8"
                      title="Time Complexity"
                      icon={<Clock className="w-4 h-4 text-emerald-700" />}
                      content={renderFormattedMarkdown(sections?.time_complexity)}
                      rawContent={sections?.time_complexity}
                      copiedSection={copiedSection}
                      onCopy={handleCopySection}
                      sectionKey="time_comp"
                      badge="Big-O"
                    />

                    <SectionCard
                      number="9"
                      title="Space Complexity"
                      icon={<HardDrive className="w-4 h-4 text-emerald-700" />}
                      content={renderFormattedMarkdown(sections?.space_complexity)}
                      rawContent={sections?.space_complexity}
                      copiedSection={copiedSection}
                      onCopy={handleCopySection}
                      sectionKey="space_comp"
                      badge="Big-O"
                    />
                  </div>

                  {/* 10. Possible Improvements */}
                  <SectionCard
                    number="10"
                    title="Possible Improvements"
                    icon={<Sparkles className="w-4 h-4 text-amber-600" />}
                    content={renderFormattedMarkdown(sections?.possible_improvements)}
                    rawContent={sections?.possible_improvements}
                    copiedSection={copiedSection}
                    onCopy={handleCopySection}
                    sectionKey="improvements"
                  />

                  {/* 11. Learning Summary */}
                  <SectionCard
                    number="11"
                    title="Learning Summary"
                    icon={<BookOpen className="w-4 h-4 text-[#174F4A]" />}
                    content={renderFormattedMarkdown(sections?.learning_summary)}
                    rawContent={sections?.learning_summary}
                    copiedSection={copiedSection}
                    onCopy={handleCopySection}
                    sectionKey="learning_summary"
                  />
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Interactive Follow-Up Chat Section */}
      <div className="bg-white rounded-2xl shadow-xs border border-[#E5E9E5] overflow-hidden">
        {/* Chat Header */}
        <div className="bg-[#174F4A] px-6 py-4 text-white flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center space-x-3">
            <span className="p-2 rounded-xl bg-white/10 backdrop-blur-xs">
              <MessageSquare className="w-5 h-5 text-emerald-200" />
            </span>
            <div>
              <h3 className="text-base font-bold">Ask Follow-Up Questions to Gemini AI</h3>
              <p className="text-xs text-emerald-100/80">
                Ask specific questions about logic, loop mechanics, condition edge cases, or request explanations in Gujarati/Hindi.
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            {chatMessages.length > 0 && (
              <button
                onClick={handleResetChat}
                className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-white/10 hover:bg-white/20 text-white border border-white/20 transition-all flex items-center space-x-1 cursor-pointer"
                title="Reset Conversation"
              >
                <RotateCcw className="w-3.5 h-3.5" />
                <span>Reset Chat</span>
              </button>
            )}
          </div>
        </div>

        {/* Suggested Quick Prompt Chips */}
        <div className="bg-[#F3F5F2] px-6 py-3 border-b border-[#E5E9E5] flex flex-wrap items-center gap-2">
          <span className="text-xs font-bold text-[#68736D] uppercase tracking-wider mr-1">Suggestions:</span>
          {SUGGESTED_PROMPTS.map((prompt, idx) => (
            <button
              key={idx}
              onClick={() => handleSendMessage(prompt)}
              disabled={isChatSending}
              className="text-xs px-3 py-1 rounded-full bg-white hover:bg-[#174F4A] text-[#202824] hover:text-white border border-[#E5E9E5] transition-all cursor-pointer font-medium shadow-xs"
            >
              💬 {prompt}
            </button>
          ))}
        </div>

        {/* Chat History Messages */}
        <div className="p-6 max-h-[420px] overflow-y-auto space-y-4 bg-white">
          {chatMessages.length === 0 ? (
            <div className="text-center py-8 text-[#8E9993]">
              <MessageSquare className="w-10 h-10 mx-auto text-[#D0D7D0] mb-2" />
              <p className="text-sm font-semibold text-[#202824]">No follow-up questions yet</p>
              <p className="text-xs text-[#68736D] mt-1 max-w-sm mx-auto">
                Type your question below or click one of the suggested prompts above to interact with Gemini AI about your submitted code.
              </p>
            </div>
          ) : (
            chatMessages.map((msg, idx) => (
              <div
                key={idx}
                className={`flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start'}`}
              >
                <div className="flex items-center space-x-2 mb-1">
                  <span className="text-[11px] font-semibold text-[#68736D] uppercase">
                    {msg.role === 'user' ? 'You' : 'Gemini AI'}
                  </span>
                </div>
                <div
                  className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm leading-relaxed shadow-xs ${
                    msg.role === 'user'
                      ? 'bg-[#174F4A] text-white rounded-tr-xs'
                      : 'bg-[#F3F5F2] text-[#202824] border border-[#E5E9E5] rounded-tl-xs'
                  }`}
                >
                  <p className="whitespace-pre-wrap">{msg.content}</p>
                </div>
              </div>
            ))
          )}

          {isChatSending && (
            <div className="flex flex-col items-start">
              <span className="text-[11px] font-semibold text-[#68736D] uppercase mb-1">Gemini AI</span>
              <div className="bg-[#F3F5F2] border border-[#E5E9E5] rounded-2xl rounded-tl-xs px-4 py-3 text-sm text-[#202824] flex items-center space-x-2 shadow-xs">
                <div className="w-2 h-2 rounded-full bg-[#174F4A] animate-ping" />
                <span className="text-xs font-medium">Gemini is drafting an answer...</span>
              </div>
            </div>
          )}

          {chatError && (
            <div className="p-3 bg-[#FEF2F2] border border-[#FECACA] rounded-xl text-xs text-[#D64545] flex items-center space-x-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{chatError}</span>
            </div>
          )}

          <div ref={chatBottomRef} />
        </div>

        {/* Chat Input Bar */}
        <div className="bg-white p-4 border-t border-[#E5E9E5] flex items-center space-x-3">
          <input
            type="text"
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSendMessage();
              }
            }}
            placeholder={`Ask a follow-up question about this ${language.toUpperCase()} code in ${explanationLanguage.toUpperCase()}...`}
            className="flex-1 text-xs bg-[#F3F5F2] border border-[#E5E9E5] rounded-xl px-4 py-3 text-[#202824] focus:outline-none focus:ring-2 focus:ring-[#174F4A] transition-all placeholder:text-[#8E9993]"
            disabled={isChatSending}
          />

          <button
            onClick={() => handleSendMessage()}
            disabled={!inputMessage.trim() || isChatSending}
            className={`px-5 py-3 rounded-xl text-xs font-bold shadow-xs transition-all flex items-center space-x-2 ${
              !inputMessage.trim() || isChatSending
                ? 'bg-zinc-200 text-zinc-400 cursor-not-allowed'
                : 'bg-[#174F4A] hover:bg-[#123E3A] text-white active:scale-98 cursor-pointer'
            }`}
          >
            <span>Send</span>
            <Send className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    </div>
  );
}

// Reusable Section Card Component
function SectionCard({
  number,
  title,
  icon,
  content,
  rawContent,
  copiedSection,
  onCopy,
  sectionKey,
  badge = null,
}) {
  const [isExpanded, setIsExpanded] = useState(true);

  return (
    <div className="bg-white rounded-2xl border border-[#E5E9E5] shadow-xs overflow-hidden transition-all hover:border-[#174F4A]/30">
      {/* Header */}
      <div className="bg-[#F3F5F2] px-4 py-3 border-b border-[#E5E9E5] flex items-center justify-between">
        <div className="flex items-center space-x-2.5">
          <span className="flex items-center justify-center w-6 h-6 rounded-full bg-[#174F4A]/10 text-[#174F4A] font-bold text-xs">
            {number}
          </span>
          <div className="flex items-center space-x-1.5">
            {icon}
            <h4 className="text-xs font-bold text-[#202824] uppercase tracking-wider">{title}</h4>
          </div>
          {badge && (
            <span className="px-2 py-0.5 rounded-full bg-[#F0FDF4] text-[#21865A] border border-[#BBF7D0] text-[10px] font-bold">
              {badge}
            </span>
          )}
        </div>

        <div className="flex items-center space-x-2">
          {rawContent && (
            <button
              onClick={() => onCopy(sectionKey, rawContent)}
              className="text-[#68736D] hover:text-[#174F4A] transition-all p-1 cursor-pointer"
              title="Copy Section"
            >
              {copiedSection === sectionKey ? (
                <Check className="w-3.5 h-3.5 text-[#21865A]" />
              ) : (
                <Copy className="w-3.5 h-3.5" />
              )}
            </button>
          )}
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="text-[#68736D] hover:text-[#202824] p-1 cursor-pointer"
          >
            {isExpanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
          </button>
        </div>
      </div>

      {/* Content */}
      {isExpanded && <div className="p-5 bg-white text-[#202824]">{content}</div>}
    </div>
  );
}

