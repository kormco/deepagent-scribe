"""
LLM-Enhanced Research Report Generator - Milestone 3

Uses Claude with pattern learning to generate intelligent LaTeX documents.
Applies learned patterns from historical document generation.
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Optional
import csv

# Add tools to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tools.llm_latex_generator import (
    LLMLaTeXGenerator, LaTeXGenerationRequest, LaTeXGenerationResult
)
from tools.pattern_injector import PatternInjector
from tools.pdf_compiler import PDFCompiler


class LLMResearchReportGenerator:
    """
    LLM-powered LaTeX report generator with pattern learning integration.

    Features:
    - Uses Claude to generate intelligent LaTeX
    - Applies learned patterns from historical documents
    - Self-correcting LaTeX generation
    - Context-aware optimization
    """

    def __init__(self, output_dir: str = "artifacts/output"):
        """
        Initialize the LLM report generator.

        Args:
            output_dir: Directory to save generated files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.artifacts_dir = Path("artifacts")
        self.content_dir = self.artifacts_dir / "sample_content"
        self.data_dir = self.content_dir / "data"
        self.images_dir = self.content_dir / "images"

        # Initialize LLM generator and pattern injector
        self.llm_generator = LLMLaTeXGenerator()
        self.pattern_injector = PatternInjector()
        self.pdf_compiler = PDFCompiler()

    def load_markdown_content(self, filename: str) -> str:
        """Load markdown content from the sample_content directory."""
        file_path = self.content_dir / filename
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        return ""

    def load_all_markdown_sections(self) -> List[Dict]:
        """
        Load all markdown content files and organize into sections.

        Returns:
            List of section dictionaries with title and content
        """
        sections = []

        # Define the document structure
        markdown_files = [
            ("introduction.md", "Introduction"),
            ("methodology.md", "Methodology"),
            ("research_areas.md", "Research Areas"),
            ("detailed_results.md", "Detailed Results"),
            ("results.md", "Results Discussion"),
            ("conclusion.md", "Conclusion")
        ]

        for filename, title in markdown_files:
            content = self.load_markdown_content(filename)
            if content:
                sections.append({
                    "title": title,
                    "content": content,
                    "type": "markdown"
                })

        return sections

    def load_csv_tables(self) -> List[Dict]:
        """
        Load CSV data files as table specifications.

        Returns:
            List of table dictionaries
        """
        tables = []

        # Model performance table
        csv_file = self.data_dir / "model_performance.csv"
        if csv_file.exists():
            with open(csv_file, 'r') as f:
                reader = csv.reader(f)
                rows = list(reader)
                if rows:
                    tables.append({
                        "caption": "Model Performance Comparison",
                        "data": rows,
                        "format": "booktabs"
                    })

        # Training metrics table
        csv_file2 = self.data_dir / "training_metrics.csv"
        if csv_file2.exists():
            with open(csv_file2, 'r') as f:
                reader = csv.reader(f)
                rows = list(reader)
                if rows and len(rows) > 1:
                    # Only first 5 data rows for conciseness
                    limited_rows = [rows[0]] + rows[1:6]
                    tables.append({
                        "caption": "Training Progression (First 5 Epochs)",
                        "data": limited_rows,
                        "format": "booktabs"
                    })

        return tables

    def load_figures(self) -> List[Dict]:
        """
        Discover figure files in images directory.

        Returns:
            List of figure dictionaries
        """
        figures = []

        if self.images_dir.exists():
            # Look for common image extensions
            for ext in ['*.png', '*.jpg', '*.jpeg', '*.pdf']:
                for img_path in self.images_dir.glob(ext):
                    # Generate caption from filename
                    caption = img_path.stem.replace('_', ' ').title()
                    figures.append({
                        "path": str(img_path.relative_to(self.output_dir.parent)),
                        "caption": caption,
                        "width": "0.8\\textwidth"
                    })

        return figures

    def generate_with_patterns(self) -> LaTeXGenerationResult:
        """
        Generate LaTeX document using LLM with learned patterns.

        Returns:
            Generation result with LaTeX content
        """
        print("🚀 LLM-Enhanced LaTeX Generation")
        print("=" * 60)

        # Get pattern context for Author agent
        pattern_context = self.pattern_injector.get_context_for_author()

        if pattern_context:
            print("✅ Loaded learned patterns from historical documents")
            print(self.pattern_injector.get_summary())
        else:
            print("ℹ️  No learned patterns available yet")

        print()

        # Load document components
        sections = self.load_all_markdown_sections()
        tables = self.load_csv_tables()
        figures = self.load_figures()

        print(f"📄 Loaded {len(sections)} content sections")
        print(f"📊 Loaded {len(tables)} data tables")
        print(f"🖼️  Found {len(figures)} figures")
        print()

        # Build requirements list with pattern context
        requirements = [
            "Use professional typography packages (microtype, lmodern)",
            "Format tables with booktabs package",
            "Include proper hyperref setup for navigation",
            "Use appropriate section hierarchy",
            "Add proper spacing and layout"
        ]

        # Add pattern-based requirements
        if pattern_context:
            requirements.append(
                "IMPORTANT: Apply the following learned patterns from historical documents:\n" +
                pattern_context
            )

        # Create generation request
        request = LaTeXGenerationRequest(
            title="Advanced AI Research: Transformers and Beyond",
            author="Dr. Research Smith",
            content_sections=sections,
            tables=tables,
            figures=figures,
            requirements=requirements
        )

        # Generate using LLM
        print("🤖 Generating LaTeX with Claude Sonnet 4.5...")
        result = self.llm_generator.generate_document(request, validate=True)

        if result.success:
            print(f"✅ Generation successful!")
            if result.improvements_made:
                print(f"💡 Applied {len(result.improvements_made)} improvements:")
                for improvement in result.improvements_made[:5]:
                    print(f"   • {improvement}")
            if result.warnings:
                print(f"⚠️  {len(result.warnings)} warnings:")
                for warning in result.warnings[:3]:
                    print(f"   • {warning}")
        else:
            print(f"❌ Generation failed: {result.error_message}")

        return result

    def generate_and_compile(self) -> Dict:
        """
        Generate LaTeX and compile to PDF.

        Returns:
            Dictionary with paths and status
        """
        # Generate LaTeX
        result = self.generate_with_patterns()

        if not result.success:
            return {
                "success": False,
                "error": result.error_message
            }

        # Save LaTeX file
        tex_path = self.output_dir / "research_report.tex"
        with open(tex_path, 'w', encoding='utf-8') as f:
            f.write(result.latex_content)

        print(f"\n💾 Saved LaTeX to: {tex_path}")

        # Compile to PDF
        print("\n📄 Compiling to PDF...")
        success, message = self.pdf_compiler.compile(str(tex_path))

        pdf_path = tex_path.with_suffix('.pdf')
        pdf_result = {
            "success": success,
            "message": message,
            "pdf_path": str(pdf_path) if success else None
        }

        if success:
            print(f"✅ PDF generated: {pdf_path}")
        else:
            print(f"❌ PDF compilation failed")
            print(f"Error: {message}")

        return {
            "success": pdf_result["success"],
            "tex_path": str(tex_path),
            "pdf_path": pdf_result.get("pdf_path"),
            "latex_result": result,
            "compilation_result": pdf_result
        }


def main():
    """Demonstration of LLM-enhanced report generation."""
    print("\n" + "=" * 60)
    print("🧠 LLM-Enhanced Report Generator with Pattern Learning")
    print("=" * 60)
    print()

    generator = LLMResearchReportGenerator()
    result = generator.generate_and_compile()

    print("\n" + "=" * 60)
    if result["success"]:
        print("✅ Report generation complete!")
        print("=" * 60)
        print(f"\n📄 LaTeX: {result['tex_path']}")
        print(f"📑 PDF: {result['pdf_path']}")
    else:
        print("❌ Report generation failed")
        print("=" * 60)
        if result.get("error"):
            print(f"\nError: {result['error']}")
    print()


if __name__ == "__main__":
    main()
