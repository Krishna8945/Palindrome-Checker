# Palindrome Checker Web App

A modern, high-performance Palindrome Checker web application built with **Python Flask** and **Double-Ended Queue (`collections.deque`)**.

---

## 🚀 Key Features

- **Double-Ended Queue Algorithm**: Uses Python's standard `collections.deque` with $O(1)$ constant time popping from both front (`popleft()`) and rear (`pop()`).
- **Interactive UI & Visualizer**:
  - Live visual depiction of the deque elements with front and rear pointers.
  - Step-by-step trace table showing each two-ended character comparison.
  - Identification of the central pivot element in odd-length palindromes.
- **Configurable Preprocessing**:
  - Case sensitivity toggle (`'A' == 'a'`).
  - Whitespace stripping.
  - Punctuation & special character filtering.
- **Hybrid Support**:
  - Instant real-time checking via dynamic Fetch API (`/api/check`).
  - Full server-side HTML form submission fallback (`POST /`).
- **Quick Preset Samples**: Test classic palindromes ("Racecar", "A man, a plan...", "123454321") and non-palindromes with a single click.

---

## 📂 Project Structure

```
palindrome checker/
├── app.py                  # Flask backend with collections.deque algorithm
├── templates/
│   └── index.html          # Responsive frontend UI & Deque visualizer
├── static/
│   ├── style.css           # Modern styling and responsive CSS
│   └── script.js           # Client-side dynamic interaction script
├── requirements.txt        # Flask dependency specification
└── README.md               # Documentation and execution guide
```

---

## 🛠️ How to Run

1. Open your terminal in the project directory:
   ```powershell
   cd "c:\Users\Admin\Desktop\palindrome checker"
   ```

2. Run the Flask application:
   ```powershell
   py app.py
   # or
   python app.py
   ```

3. Open your browser and navigate to:
   ```
   http://127.0.0.1:5000
   ```

---

## 💡 Why `collections.deque`?

In a standard Python list, `pop(0)` takes $O(n)$ time because all subsequent items in the array must shift to the left. 

`collections.deque` is implemented in C as a doubly linked list of blocks, providing **$O(1)$ amortized complexity** for both `popleft()` and `pop()`. This makes it the mathematically and computationally optimal data structure for two-pointer / two-ended symmetry verification.
