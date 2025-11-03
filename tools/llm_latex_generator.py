"""LLM-Based LaTeX Generator that uses Claude for intelligent document generation."""

import os
import json
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import anthropic


@dataclass
class LaTeXGenerationRequest:
    """Request for LaTeX document generation."""
    title: str
    author: str
    content_sections: List[Dict]  # List of {title, content, type}
    tables: List[Dict] = None  # List of {caption, data, format}
    figures: List[Dict] = None  # List of {path, caption, width}
    requirements: List[str] = None  # Special requirements

    def __post_init__(self):
        if self.tables is None:
            self.tables = []
        if self.figures is None:
            self.figures = []
        if self.requirements is None:
            self.requirements = []


@dataclass
class LaTeXGenerationResult:
    """Result of LaTeX generation."""
    success: bool
    latex_content: str
    warnings: List[str]
    improvements_made: List[str]
    error_message: Optional[str] = None


class LLMLaTeXGenerator:
    """
    LLM-based LaTeX generator that uses Claude to intelligently create
    LaTeX documents with proper error handling and edge case management.

    This replaces the deterministic template-based approach with an
    intelligent system that can reason about LaTeX structure and syntax.
    """

    def __init__(self, api_key: Optional[str] = None):
        """Initialize with Anthropic API key."""
        self.api_key = api_key or os.getenv('ANTHROPIC_API_KEY')
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not found")
        self.client = anthropic.Anthropic(api_key=self.api_key)

    def generate_document(self, request: LaTeXGenerationRequest,
                          validate: bool = True) -> LaTeXGenerationResult:
        """
        Generate a complete LaTeX document using LLM reasoning.

        Args:
            request: LaTeX generation request with content and requirements
            validate: Whether to validate and fix LaTeX syntax

        Returns:
            LaTeXGenerationResult with generated LaTeX and metadata
        """
        print("📝 Generating LaTeX document with LLM reasoning...")

        # Step 1: Generate initial LaTeX
        latex_content = self._generate_initial_latex(request)

        if not latex_content:
            return LaTeXGenerationResult(
                success=False,
                latex_content="",
                warnings=[],
                improvements_made=[],
                error_message="Failed to generate initial LaTeX"
            )

        # Step 2: Validate and fix syntax if requested
        warnings = []
        improvements_made = []

        if validate:
            print("🔍 Validating and improving LaTeX syntax...")
            latex_content, validation_warnings, fixes = self._validate_and_fix_latex(
                latex_content, request
            )
            warnings.extend(validation_warnings)
            improvements_made.extend(fixes)

        return LaTeXGenerationResult(
            success=True,
            latex_content=latex_content,
            warnings=warnings,
            improvements_made=improvements_made
        )

    def _generate_initial_latex(self, request: LaTeXGenerationRequest) -> str:
        """Generate initial LaTeX document using Claude."""
        # Build the generation prompt
        prompt = self._build_generation_prompt(request)

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=8000,
                temperature=0.2,  # Lower temperature for more consistent LaTeX
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            # Extract LaTeX from response
            latex_content = self._extract_latex_from_response(response.content[0].text)
            print(f"✅ Generated {len(latex_content)} characters of LaTeX")
            return latex_content

        except Exception as e:
            print(f"❌ Error generating LaTeX: {e}")
            return ""

    def _build_generation_prompt(self, request: LaTeXGenerationRequest) -> str:
        """Build the prompt for LaTeX generation."""
        # Prepare content sections summary
        sections_summary = "\n".join([
            f"- {sec.get('title', 'Untitled')}: {len(sec.get('content', ''))} characters"
            for sec in request.content_sections
        ])

        # Prepare tables summary
        tables_summary = "\n".join([
            f"- {table.get('caption', 'Untitled table')}"
            for table in request.tables
        ]) if request.tables else "No tables"

        # Prepare figures summary
        figures_summary = "\n".join([
            f"- {fig.get('caption', 'Untitled figure')}: {fig.get('path', 'no path')}"
            for fig in request.figures
        ]) if request.figures else "No figures"

        # Build requirements
        requirements_text = "\n".join([
            f"- {req}" for req in request.requirements
        ]) if request.requirements else "Standard research document formatting"

        prompt = f"""You are a LaTeX document generation expert. Generate a complete, professional LaTeX document based on the following specifications.

**CRITICAL REQUIREMENTS:**
1. Generate COMPLETE, VALID LaTeX that compiles without errors
2. Use ONLY packages that are commonly available in TeX Live
3. Escape ALL special LaTeX characters properly (%, $, &, #, _, {{, }}, etc.)
4. Include proper document structure: preamble, \\begin{{document}}, content, \\end{{document}}
5. Use proper spacing and formatting for readability
6. Include table of contents if document has multiple sections
7. Add page numbers and basic header/footer

**Document Specifications:**
Title: {request.title}
Author: {request.author}

**Content Sections:**
{sections_summary}

**Tables:**
{tables_summary}

**Figures:**
{figures_summary}

**Special Requirements:**
{requirements_text}

**Content Details:**
"""

        # Add detailed content for each section
        for i, section in enumerate(request.content_sections, 1):
            prompt += f"\n\n--- Section {i}: {section.get('title', 'Untitled')} ---\n"
            prompt += section.get('content', '')

        # Add table data
        if request.tables:
            prompt += "\n\n**Table Data:**\n"
            for table in request.tables:
                prompt += f"\nTable: {table.get('caption', 'Untitled')}\n"
                prompt += f"Data: {json.dumps(table.get('data', []))}\n"

        # Add figure information
        if request.figures:
            prompt += "\n\n**Figure Information:**\n"
            for fig in request.figures:
                default_width = '0.8\\textwidth'
                prompt += f"\nFigure: {fig.get('caption', 'Untitled')}\n"
                prompt += f"Path: {fig.get('path', 'unknown')}\n"
                prompt += f"Width: {fig.get('width', default_width)}\n"

        prompt += """

**Output Instructions:**
Generate a COMPLETE LaTeX document with the following structure:

1. Preamble with necessary packages (use standard packages only)
2. Document metadata (title, author, date)
3. \\begin{document}
4. Title page with \\maketitle
5. Table of contents (if multiple sections)
6. All content sections with proper formatting
7. All tables with proper booktabs formatting
8. All figures with proper placement
9. \\end{document}

**IMPORTANT:**
- Escape special characters: % → \\%, $ → \\$, & → \\&, # → \\#, _ → \\_, { → \\{, } → \\}
- Use \\section{}, \\subsection{}, etc. for structure
- Use [H] placement for tables/figures to avoid floating issues
- Include \\usepackage{hyperref} for clickable links
- Use \\usepackage{geometry} for proper margins
- Use \\usepackage{fancyhdr} for headers/footers

Return ONLY the complete LaTeX code, no explanations or markdown code blocks.
"""

        return prompt

    def _extract_latex_from_response(self, response_text: str) -> str:
        """Extract LaTeX code from Claude's response."""
        # Remove markdown code blocks if present
        if "```latex" in response_text:
            start = response_text.find("```latex") + 8
            end = response_text.find("```", start)
            return response_text[start:end].strip()
        elif "```" in response_text:
            start = response_text.find("```") + 3
            end = response_text.find("```", start)
            return response_text[start:end].strip()
        else:
            return response_text.strip()

    def _validate_and_fix_latex(self, latex_content: str,
                                request: LaTeXGenerationRequest) -> Tuple[str, List[str], List[str]]:
        """
        Validate LaTeX syntax and fix common issues using LLM reasoning.

        Returns:
            Tuple of (fixed_latex, warnings, improvements_made)
        """
        validation_prompt = f"""You are a LaTeX syntax validator and fixer. Analyze this LaTeX document and fix any issues.

**LaTeX Document to Validate:**
```latex
{latex_content}
```

**Validation Checklist:**
1. Proper document structure (\\documentclass, \\begin{{document}}, \\end{{document}})
2. All special characters properly escaped
3. All environments properly closed
4. Package usage is correct and packages exist
5. No syntax errors
6. Proper use of math mode
7. Figure and table references are valid
8. No orphaned braces or brackets

**Your Task:**
1. Identify any syntax errors or issues
2. Fix all issues while preserving the document's intent
3. List what improvements you made

**Output Format:**
First, list any issues you found as JSON:
{{"issues": ["issue1", "issue2"]}}

Then provide the CORRECTED LaTeX code (complete document).
"""

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=8000,
                temperature=0.1,  # Very low temperature for precise fixes
                messages=[{
                    "role": "user",
                    "content": validation_prompt
                }]
            )

            response_text = response.content[0].text

            # Extract issues
            warnings = []
            if '"issues":' in response_text:
                try:
                    start = response_text.find('{')
                    end = response_text.find('}', start) + 1
                    issues_json = json.loads(response_text[start:end])
                    warnings = issues_json.get('issues', [])
                except:
                    warnings = ["Unable to parse validation issues"]

            # Extract fixed LaTeX
            fixed_latex = self._extract_latex_from_response(response_text)

            # If extraction failed, return original
            if not fixed_latex or len(fixed_latex) < len(latex_content) * 0.5:
                print("⚠️ Validation fix failed, using original LaTeX")
                return latex_content, warnings, []

            improvements = [f"Fixed {len(warnings)} LaTeX issues"] if warnings else []
            print(f"✅ Validated and fixed {len(warnings)} issues")

            return fixed_latex, warnings, improvements

        except Exception as e:
            print(f"⚠️ Validation error: {e}, using original LaTeX")
            return latex_content, [f"Validation failed: {str(e)}"], []

    def apply_visual_qa_fixes(self, latex_content: str,
                             issues: List[str]) -> Tuple[str, bool, List[str]]:
        """
        Apply fixes to LaTeX based on Visual QA feedback using LLM reasoning.

        This is called by the Visual QA agent to improve the document.

        Args:
            latex_content: Current LaTeX document
            issues: List of issues found by Visual QA

        Returns:
            Tuple of (fixed_latex, success, fixes_applied)
        """
        print(f"🔧 Applying {len(issues)} Visual QA fixes to LaTeX...")

        # Build the fix prompt
        issues_text = "\n".join([f"- {issue}" for issue in issues])

        fix_prompt = f"""You are a LaTeX document improvement specialist. You need to fix specific visual quality issues in a LaTeX document.

**Current LaTeX Document:**
```latex
{latex_content}
```

**Issues to Fix:**
{issues_text}

**Your Task:**
1. Analyze each issue carefully
2. Apply MINIMAL, SURGICAL fixes to address each issue
3. Do NOT break existing LaTeX syntax
4. Use ONLY standard LaTeX packages that compile reliably
5. Test that all environments are properly opened and closed
6. Ensure the document structure remains intact

**Common Fixes:**
- Missing page numbers: Ensure \\fancyfoot[C]{{\\thepage}} is set
- Missing table of contents: Add \\tableofcontents after \\maketitle
- Spacing issues: Use \\setlength or \\vspace commands (NOT microtype package)
- Typography issues: Adjust font sizes with \\large, \\Large, etc.
- Header/footer issues: Use fancyhdr package properly
- Line spacing: Use \\linespread{{}} or manual spacing commands

**Critical Rules:**
- Do NOT add \\usepackage after \\begin{{document}}
- Do NOT use packages that don't exist (like longtabu)
- Do NOT use microtype package (causes font expansion errors)
- Do NOT use setspace package if it causes issues
- Preserve ALL existing content
- Only modify formatting/structure
- Use simple, reliable LaTeX commands

**IMPORTANT: This LaTeX will be compiled immediately. Ensure it compiles without errors.**

Return the COMPLETE CORRECTED LaTeX document, no explanations.
"""

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=8000,
                temperature=0.1,
                messages=[{
                    "role": "user",
                    "content": fix_prompt
                }]
            )

            fixed_latex = self._extract_latex_from_response(response.content[0].text)

            # Validate the fix
            if not fixed_latex or len(fixed_latex) < len(latex_content) * 0.5:
                print("❌ Fix generated invalid LaTeX")
                return latex_content, False, []

            # Basic syntax validation
            if fixed_latex.count('\\begin{') != fixed_latex.count('\\end{'):
                print("❌ Fix has unmatched environments")
                return latex_content, False, []

            if '\\begin{document}' not in fixed_latex or '\\end{document}' not in fixed_latex:
                print("❌ Fix is missing document environment")
                return latex_content, False, []

            fixes_applied = [f"Applied fixes for: {', '.join(issues[:3])}"]
            print(f"✅ Successfully applied {len(issues)} Visual QA fixes")

            return fixed_latex, True, fixes_applied

        except Exception as e:
            print(f"❌ Error applying Visual QA fixes: {e}")
            return latex_content, False, []

    def self_correct_compilation_errors(self, latex_content: str,
                                       compilation_error: str,
                                       max_attempts: int = 3) -> Tuple[str, bool, List[str]]:
        """
        Self-correct LaTeX based on compilation errors using LLM reasoning.

        This implements a feedback loop where the LLM:
        1. Receives the LaTeX that failed to compile
        2. Analyzes the compilation error
        3. Generates a corrected version
        4. Returns for re-compilation

        Args:
            latex_content: LaTeX that failed to compile
            compilation_error: Error message from pdflatex
            max_attempts: Maximum self-correction attempts

        Returns:
            Tuple of (corrected_latex, success, corrections_made)
        """
        print(f"🤖 LLM Self-Correction: Analyzing compilation error...")

        corrections_made = []
        current_latex = latex_content

        for attempt in range(1, max_attempts + 1):
            print(f"   Attempt {attempt}/{max_attempts}: Analyzing error...")

            correction_prompt = f"""You are a LaTeX debugging expert. A LaTeX document failed to compile and you need to fix it.

**LaTeX Document (FAILED TO COMPILE):**
```latex
{current_latex}
```

**Compilation Error:**
```
{compilation_error}
```

**Your Task:**
1. **Analyze the error carefully** - understand what went wrong
2. **Identify the root cause** - is it a package issue, syntax error, or incompatibility?
3. **Generate a corrected version** that will compile successfully
4. **Use ONLY reliable, standard LaTeX techniques**

**Common Error Fixes:**
- "auto expansion is only possible with scalable fonts" → REMOVE microtype package or disable expansion
- "File X.sty not found" → REMOVE that package and use alternative approach
- "Missing \\begin{{document}}" → Fix document structure
- "Too many }}" or "Missing }}" → Fix brace matching
- Package conflicts → Remove conflicting packages

**Critical Rules:**
- If a package causes errors, REMOVE it entirely and use manual commands instead
- If microtype fails, remove it and use \\linespread{{}} for spacing
- If setspace fails, use \\setlength{{\\baselineskip}}{{}} instead
- Preserve ALL document content
- Focus on making it COMPILE, not perfection
- Use simple, proven LaTeX commands

**IMPORTANT: The corrected LaTeX MUST compile without errors.**

Return ONLY the COMPLETE CORRECTED LaTeX document, no explanations.
"""

            try:
                response = self.client.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=8000,
                    temperature=0.1,
                    messages=[{
                        "role": "user",
                        "content": correction_prompt
                    }]
                )

                corrected_latex = self._extract_latex_from_response(response.content[0].text)

                # Validate correction
                if not corrected_latex or len(corrected_latex) < len(latex_content) * 0.5:
                    print(f"   ❌ Attempt {attempt} generated invalid LaTeX")
                    continue

                # Check basic structure
                if '\\begin{document}' not in corrected_latex or '\\end{document}' not in corrected_latex:
                    print(f"   ❌ Attempt {attempt} missing document structure")
                    continue

                corrections_made.append(f"Attempt {attempt}: Fixed compilation error")
                print(f"   ✅ Attempt {attempt}: Generated corrected LaTeX")

                return corrected_latex, True, corrections_made

            except Exception as e:
                print(f"   ❌ Attempt {attempt} failed: {e}")
                continue

        # All attempts failed
        print(f"❌ Self-correction failed after {max_attempts} attempts")
        return latex_content, False, corrections_made
