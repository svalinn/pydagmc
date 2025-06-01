# Contributing

First off, thank you for considering contributing to PyDAGMC! We welcome contributions from everyone. Your help is essential for keeping it great.

This document provides guidelines for contributing to PyDAGMC. Please read it carefully to ensure a smooth and effective contribution process.

## Ways to Contribute

There are many ways to contribute to PyDAGMC, including:

- **Reporting Bugs:** If you find a bug, please report it by opening an issue.
- **Suggesting Enhancements:** Have an idea for a new feature or an improvement to an existing one? Let us know by opening an issue.
- **Writing Code:** Contribute bug fixes or new features through Pull Requests.
- **Improving Documentation:** Help us make our documentation clearer, more complete, or fix typos.
- **Writing Tutorials or Examples:** Share your knowledge by creating new examples or tutorials.
- **Reviewing Pull Requests:** Help review contributions from others.

## Getting Started

### Prerequisites

Before you begin, ensure you have the following installed:

- **Python:** Version 3.8 or higher.
- **Git:** For version control.
- **PyMOAB:** PyDAGMC is built upon MOAB. Please ensure MOAB is installed and functional in your Python environment. Refer to the [MOAB installation guide](https://ftp.mcs.anl.gov/pub/fathom/moab-docs/building.html).

### Setting up Your Development Environment

1. **Fork the Repository:**
    Click the "Fork" button at the top right of the [PyDAGMC GitHub page](https://github.com/svalinn/pydagmc). This creates your own copy of the repository.

2. **Clone Your Fork:**

    ```bash
    git clone https://github.com/YOUR_USERNAME/pydagmc.git
    cd pydagmc
    ```

3. **Create a Virtual Environment (Recommended):**
    Using a virtual environment helps manage dependencies and avoids conflicts with other projects.

    ```bash
    python -m venv .venv
    source .venv/bin/activate  # On Windows, use: .venv\Scripts\activate
    ```

4. **Install Dependencies:**
    Install PyDAGMC in editable mode along with development dependencies (for testing and documentation).

    ```bash
    pip install -e .[test,docs]
    ```

    This command installs the package from the current directory (`.`) in editable mode (`-e`), and includes the optional dependencies specified for `test` and `docs` in `pyproject.toml`.

5. **Set Upstream Remote:**
    This will help you keep your fork synchronized with the main repository.

    ```bash
    git remote add upstream https://github.com/svalinn/pydagmc.git
    ```

## Making Changes

1. **Create a New Branch:**
    Before making any changes, create a new branch from the `main` branch (or the most up-to-date development branch):

    ```bash
    git checkout main
    git pull upstream main  # Ensure your main branch is up-to-date
    git checkout -b feature/your-feature-name  # For new features
    # or
    git checkout -b bugfix/issue-number-short-description # For bug fixes
    ```

    Use a descriptive branch name (e.g., `feature/add-volume-creation`, `bugfix/fix-group-repr`).

2. **Make Your Changes:**
    Write your code, fix bugs, or improve documentation.

### Coding Style

- Follow [PEP 8 -- Style Guide for Python Code](https://www.python.org/dev/peps/pep-0008/).
- Write clear, readable, and well-commented code where necessary.
- Use type hints for function signatures and variables as much as possible. PyDAGMC uses `sphinx-autodoc-typehints` for documentation.
- (Optional: If you decide to use linters/formatters like Black or Flake8, mention them here and how to run them.)

### Writing Tests

- **All new features and bug fixes should include tests.** PyDAGMC uses `pytest`.
- Place your tests in the `tests/` directory.
- Ensure your tests cover a variety of scenarios, including edge cases.
- Run tests locally before submitting a pull request:

    ```bash
    pytest
    ```

- Aim to maintain or increase code coverage. You can check coverage with:

    ```bash
    pytest --cov=pydagmc --cov-report=html
    # Then open htmlcov/index.html in your browser
    ```

### Updating Documentation

- **Docstrings:** For any new functions, classes, or methods, or changes to existing ones, update the docstrings. We use Google or NumPy style docstrings, which are compatible with Sphinx and Napoleon.
- **User Documentation:** If your changes affect user-facing behavior or add new features, update the relevant sections in the `docs/source/` directory (e.g., `user_guide.md`, `tutorial.md`, API pages).
- Build the documentation locally to ensure your changes render correctly:

    ```bash
    cd docs
    make clean html
    # Then open build/html/index.html
    ```

### Commit Messages

- Write clear and concise commit messages.
- A good commit message summary should be 50 characters or less.
- If more detail is needed, provide it in the commit body after a blank line.
- Reference relevant issue numbers (e.g., `Fixes #123`).

## Submitting Pull Requests

1. **Push Your Changes:**
    Once your changes are ready and tested, push your branch to your fork:

    ```bash
    git push origin feature/your-feature-name
    ```

2. **Open a Pull Request (PR):**
    - Go to the [PyDAGMC GitHub page](https://github.com/svalinn/pydagmc) in your browser.
    - You should see a prompt to create a Pull Request from your recently pushed branch. Click it.
    - Ensure the base repository is `svalinn/pydagmc` and the base branch is `main`.
    - Provide a clear title and a detailed description using the provided [pull request template][pull-request-template] for your PR:
        - Summarize the changes made.
        - Explain the "why" behind your changes.
        - Link to any relevant issues (e.g., "Closes #123" or "Fixes #123").
        - Describe how your changes have been tested.
        - Include any necessary information for reviewers.

3. **Code Review:**
    - Maintainers will review your PR. Be prepared to address feedback and make changes.
    - The CI checks (GitHub Actions) must pass before your PR can be merged.

4. **Merging:**
    Once your PR is approved and all checks pass, a maintainer will merge it into the main codebase. Congratulations, and thank you!

## Reporting Bugs

If you encounter a bug, please help us by reporting it:

1. **Search Existing Issues:** Check if the bug has already been reported on the [GitHub Issues page](https://github.com/svalinn/pydagmc/issues).
2. **Open a New Issue:** If the bug is not already reported:
    - Go to the "Issues" tab and click "New Issue."
    - Choose the [Bug report][bug-report-template] template, or provide the following information:
        - A clear and descriptive title.
        - PyDAGMC version (`pip show pydagmc`).
        - PyMOAB version.
        - Python version.
        - Operating System.
        - A clear description of the bug.
        - Steps to reproduce the bug, including a minimal, reproducible code example.
        - What you expected to happen.
        - What actually happened (include full tracebacks if there's an error).

## Suggesting Enhancements

If you have an idea for a new feature or an improvement:

1. **Search Existing Issues:** Check if the enhancement has already been suggested.
2. **Open a New Issue:**
    - Go to the "Issues" tab and click "New Issue."
    - Choose the [Feature request][feature-request-template] template, or provide:
        - A clear and descriptive title.
        - A detailed description of the proposed enhancement.
        - Explain why this enhancement would be useful.
        - (Optional) Suggest a possible implementation approach.

## Code of Conduct

All contributors are expected to adhere to the [Code of Conduct][code-of-conduct]. Please read it to understand the standards of behavior we expect in our community.

## Questions?

If you have questions about contributing, feel free to:

- Open an issue on GitHub with the "question" label.
- (If you set up GitHub Discussions) Ask on the [Discussions page](https://github.com/svalinn/pydagmc/discussions).

Thank you for contributing to PyDAGMC!

[bug-report-template]: .github/ISSUE_TEMPLATE/bug-report-template.md
[feature-request-template]: .github/ISSUE_TEMPLATE/feature-request-template.md
[pull-request-template]: .github/pull-request-template.md
[code-of-conduct]: CODE_OF_CONDUCT.md
