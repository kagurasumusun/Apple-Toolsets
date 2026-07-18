import os
import shutil
from pathlib import Path

docs_dir = Path("docs")
wiki_dir = docs_dir / "wiki"
wiki_dir.mkdir(exist_ok=True)

# Define wiki structure
structure = {
    "1_architecture": ["ENGINEERING_LOG.md", "MINI_ISA_NOTES.md"],
    "2_audits_and_evidence": ["CLEAN_ROOM_AUDIT.md", "CLEAN_ROOM_EVIDENCE.md", "EVIDENCE_MANIFEST.json", "VERIFICATION.md"],
    "3_progress_and_status": ["FINAL_STATUS.md", "HANDOFF.md", "PROGRESS_REPORT.md", "PROJECT_STATE.json", "SESSION_COMPLETE.md", "SESSION_SUMMARY.md"],
    "4_guides_and_analysis": ["USAGE_GUIDE.md", "ATLAS_SWEEP_ANALYSIS.md"]
}

# Move files to wiki structure
for folder, files in structure.items():
    folder_path = wiki_dir / folder
    folder_path.mkdir(exist_ok=True)
    for f in files:
        src = docs_dir / "project_reports" / f
        if src.exists():
            shutil.move(str(src), str(folder_path / f))

# Create a central README/index for the wiki
index_content = """# Apple-actool-py Knowledge Base (Wiki)

Welcome to the internal knowledge base for the `Apple-actool-py` project.
This wiki contains all engineering logs, clean-room reverse engineering evidence, architectural notes, and research data.

## Table of Contents

### 1. Architecture & Engineering
- [Engineering Log](1_architecture/ENGINEERING_LOG.md): Detailed daily engineering notes and breakthroughs.
- [Mini ISA Notes](1_architecture/MINI_ISA_NOTES.md): Notes on reverse-engineered instruction sets and formats.

### 2. Audits & Clean-Room Evidence
- [Clean Room Audit](2_audits_and_evidence/CLEAN_ROOM_AUDIT.md): Rules and logs of the clean-room implementation process.
- [Clean Room Evidence](2_audits_and_evidence/CLEAN_ROOM_EVIDENCE.md): Proof of non-infringing implementation.
- [Verification](2_audits_and_evidence/VERIFICATION.md): Verification steps and hashes.

### 3. Progress & Status Reports
- [Handoff](3_progress_and_status/HANDOFF.md)
- [Project State](3_progress_and_status/PROJECT_STATE.json)
- [Final Status](3_progress_and_status/FINAL_STATUS.md)

### 4. Guides & Research Analysis
- [Usage Guide](4_guides_and_analysis/USAGE_GUIDE.md): How to use the CLI and Python API.
- [Atlas Sweep Analysis](4_guides_and_analysis/ATLAS_SWEEP_ANALYSIS.md): Deep dive into Apple's Sprite Atlas packing algorithms.
- [Research Reports](../research_reports): Raw dumps, JSON probes, and matrix analysis from our rigorous testing against Apple's `actool`.

---
*Generated automatically by the documentation organizer.*
"""

with open(wiki_dir / "Home.md", "w") as f:
    f.write(index_content)

# Clean up empty project_reports
if (docs_dir / "project_reports").exists() and not os.listdir(docs_dir / "project_reports"):
    os.rmdir(docs_dir / "project_reports")

