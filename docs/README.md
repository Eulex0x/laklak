# Laklak Documentation

This directory contains comprehensive technical documentation for the Laklak project.

## 📚 Available Documentation

### `CODEBASE_KNOWLEDGE.md` ⭐
**The Complete Knowledge Base**

This is the **source of truth** for understanding the Laklak codebase. It contains:

#### 📋 What's Inside:
- **Executive Summary** - High-level overview
- **Architecture Overview** - Repository structure and design
- **Key Components** - Detailed analysis of 6 major components:
  - laklak/core.py (Main API)
  - modules/exchanges/ (Exchange integrations)
  - modules/influx_writer.py (Data pipeline)
  - data_collector.py (Automation script)
  - backfill.py (Historical data)
  - assets.csv (Configuration)
- **Testing Results** - Test suite analysis (62 tests)
- **Usage Examples** - Practical code examples
- **Data Flow Diagram** - Visual architecture
- **Configuration System** - All settings explained
- **Quick Reference** - Common functions and patterns

#### 🎯 When to Read This:
- **Before making changes** - Understand current implementation
- **When debugging** - Check known issues and limitations
- **Learning the codebase** - Complete architecture overview
- **Adding features** - Understand existing patterns

#### 📊 Statistics:
- 19,000+ characters of detailed documentation
- Covers all 6 exchange integrations
- Includes verified test results
- Contains working code examples

---

## 🚀 Quick Start

### For Developers
1. Read `CODEBASE_KNOWLEDGE.md` first
2. Review the main README in project root
3. Check test results in `../tests/`
4. Look at exchange implementations in `../modules/exchanges/`

### For AI Assistants (GitHub Copilot, etc.)
**MANDATORY:** Read `CODEBASE_KNOWLEDGE.md` before responding to any questions about the codebase.

See: `../.github/copilot-instructions.md` for detailed AI assistant guidelines.

---

## 📁 Documentation Structure

```
docs/
├── README.md                   # This file
└── CODEBASE_KNOWLEDGE.md      # 🧠 Complete knowledge base

.github/
├── README.md                   # GitHub config explanation
└── copilot-instructions.md    # AI assistant instructions
```

---

## 🔄 Keeping Documentation Updated

### Update Frequency

**CODEBASE_KNOWLEDGE.md should be updated when:**
- ✅ New exchange integrations are added
- ✅ Major architecture changes occur
- ✅ Test results change significantly
- ✅ New features are implemented
- ✅ Known issues are discovered or resolved

**How to Update:**
1. Make code changes
2. Run full test suite: `pytest tests/ -v`
3. Verify functionality works
4. Update relevant sections in CODEBASE_KNOWLEDGE.md
5. Commit both code and documentation together

### Update Template

When updating, include:
- Date of update
- What changed
- Test results
- New examples if applicable

---

## 🎓 Documentation Philosophy

> **"Code tells you how, documentation tells you why."**

- **Code is the truth** - Documentation should match reality
- **Keep it current** - Outdated docs are worse than no docs
- **Be comprehensive** - Better too much than too little
- **Include examples** - Show, don't just tell
- **Document limitations** - Known issues help debugging

---

## 🔗 External Resources

- **PyPI Package:** https://pypi.org/project/laklak/
- **GitHub Repository:** https://github.com/Eulex0x/laklak
- **Issue Tracker:** https://github.com/Eulex0x/laklak/issues

---

**Last Updated:** 2026-01-29  
**Documentation Version:** 1.0  
**Status:** ✅ Complete and verified
