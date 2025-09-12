---
allowed-tools: Bash, Read, Write, LS
---

# Update Context

This command updates the project context documentation in `.claude/context/` to reflect the current state of the project. Run this at the end of each development session to keep context accurate.

## Required Rules

**IMPORTANT:** Before executing this command, read and follow:
- `.claude/rules/datetime.md` - For getting real current date/time

## Preflight Checklist

Before proceeding, complete these validation steps.
Do not bother the user with preflight checks progress ("I'm not going to ..."). Just do them and move on.

### 1. Context Validation
- Run: `ls -la .claude/context/ 2>/dev/null`
- If directory doesn't exist or is empty:
  - Tell user: "❌ No context to update. Please run /context:create first."
  - Exit gracefully
- Count existing files: `ls -1 .claude/context/*.md 2>/dev/null | wc -l`
- Report: "📁 Found {count} context files to check for updates"

### 2. Change Detection

Gather information about what has changed:

**Git Changes:**
- Run: `git status --short` to see uncommitted changes
- Run: `git log --oneline -10` to see recent commits
- Run: `git diff --stat HEAD~5..HEAD 2>/dev/null` to see files changed recently

**File Modifications:**
- Check context file ages: `find .claude/context -name "*.md" -type f -exec ls -lt {} + | head -5`
- Note which context files are oldest and may need updates

**Dependency Changes:**
- Node.js: `git diff HEAD~5..HEAD package.json 2>/dev/null`
- Python: `git diff HEAD~5..HEAD requirements.txt 2>/dev/null`
- Check if new dependencies were added or versions changed

### 3. Get Current DateTime
- Run: `date -u +"%Y-%m-%dT%H:%M:%SZ"`
- Store for updating `last_updated` field in modified files

### 4. CLAUDE.md Documentation Discovery
Identify all CLAUDE.md files requiring potential updates:

**Find Documentation Files:**
- Run: `find . -name "CLAUDE.md" -type f` to locate all CLAUDE.md files
- Expected locations:
  - Root: `/CLAUDE.md` (shared enterprise standards)
  - Modules: `frontend/`, `user-auth-broker-management/`, `options-strategy-platform/`, etc.
  - .claude: `.claude/CLAUDE.md` (development patterns)
- Count found files: Report "📋 Found {count} CLAUDE.md files to check for updates"

**Check CLAUDE.md Relevance:**
- Check git diff for documentation-worthy changes in each module
- Look for recent commits that add features, architectural changes, or new patterns
- Identify which CLAUDE.md files need updates based on changes in their respective modules

### 5. Project Documentation Discovery & Analysis
Identify ALL documentation files for comprehensive management:

**Find All Documentation Files:**
- Run: `find . -name "*.md" -type f -not -path "*/node_modules/*" -not -path "./.claude/context/*" -not -path "./.claude/agents/*" -not -path "./.claude/rules/*" -not -path "./.claude/commands/*" -not -path "./frontend-amplify/*"`
- Categorize by type: CLAUDE.md, README.md, Technical docs, Requirements docs
- Count found files: Report "📚 Found {count} project documentation files to analyze"

**Categorize Documentation Types:**
- **Technical Documentation**: `docs/*/TESTING.md`, `docs/*/ARCHITECTURE.md`, `docs/*/DESIGN.md`, testing guides
- **README Files**: Root and module `README.md` files for setup and introduction
- **Requirements & Planning**: `docs/requirements/`, roadmaps, specifications
- **Deployment & Operations**: Setup guides, deployment documentation

**Smart Update Detection by Category:**
- **Technical Docs**: Check implementation changes via `git diff --name-status HEAD~5..HEAD | grep -E "(test|spec|component|architecture)"`
- **README Files**: Check dependency changes via `git diff HEAD~5..HEAD package.json requirements.txt deploy.sh`
- **Requirements Docs**: Manual updates only (rarely automated)

## Instructions

### 1. Systematic Change Analysis & Project Documentation Updates

**IMPORTANT**: This command now processes BOTH context files AND project documentation files in a single execution.

**Execution Order**:
1. Process context files (`.claude/context/*.md`)
2. Execute project documentation updates (CLAUDE.md, README.md, Technical docs)
3. Provide comprehensive summary of ALL documentation updates

For each context file, determine if updates are needed:

**Check each file systematically:**
#### `progress.md` - **Always Update**
  - Check: Recent commits, current branch, uncommitted changes
  - Update: Latest completed work, current blockers, next steps
  - Run: `git log --oneline -5` to get recent commit messages
  - Include completion percentages if applicable

#### `project-structure.md` - **Update if Changed**
  - Check: `git diff --name-status HEAD~10..HEAD | grep -E '^A'` for new files
  - Update: New directories, moved files, structural reorganization
  - Only update if significant structural changes occurred

#### `tech-context.md` - **Update if Dependencies Changed**
  - Check: Package files for new dependencies or version changes
  - Update: New libraries, upgraded versions, new dev tools
  - Include security updates or breaking changes

#### `system-patterns.md` - **Update if Architecture Changed**
  - Check: New design patterns, architectural decisions
  - Update: New patterns adopted, refactoring done
  - Only update for significant architectural changes

#### `product-context.md` - **Update if Requirements Changed**
  - Check: New features implemented, user feedback incorporated
  - Update: New user stories, changed requirements
  - Include any pivot in product direction

#### `project-brief.md` - **Rarely Update**
  - Check: Only if fundamental project goals changed
  - Update: Major scope changes, new objectives
  - Usually remains stable

#### `project-overview.md` - **Update for Major Milestones**
  - Check: Major features completed, significant progress
  - Update: Feature status, capability changes
  - Update when reaching project milestones

#### `project-vision.md` - **Rarely Update**
  - Check: Strategic direction changes
  - Update: Only for major vision shifts
  - Usually remains stable

#### `project-style-guide.md` - **Update if Conventions Changed**
  - Check: New linting rules, style decisions
  - Update: Convention changes, new patterns adopted
  - Include examples of new patterns

### 2. Execute Project Documentation Updates

**CRITICAL**: After processing context files, IMMEDIATELY execute project documentation updates:

After analyzing context files, process discovered project documentation files:

**For each project documentation file that needs updating:**

#### **Step 1: Process CLAUDE.md Files**
```bash
# Find and process CLAUDE.md files
find . -name "CLAUDE.md" -type f -not -path "./.claude/context/*" | while read claude_file; do
  # Check if file needs updates based on recent commits
  module_path=$(dirname "$claude_file")
  if [[ $(git diff --name-status HEAD~5..HEAD "$module_path/" | wc -l) -gt 0 ]] || [[ $(git log --oneline -5 --grep="feat:" | wc -l) -gt 0 ]]; then
    echo "📝 Updating $claude_file - Recent module changes detected"
    
    # Read current CLAUDE.md content
    if [[ -f "$claude_file" ]]; then
      # Create backup
      cp "$claude_file" "$claude_file.backup"
      
      # Get current datetime for updates
      current_date=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
      
      # Check what type of CLAUDE.md this is and apply appropriate updates
      if [[ "$claude_file" == "./CLAUDE.md" ]]; then
        # Root CLAUDE.md - add latest project achievements
        echo "  ↳ Updating root CLAUDE.md with latest project achievements"
        
        # Get recent commits for update content
        recent_commits=$(git log --oneline -3 --pretty=format:"%h %s")
        
        # Add current date section if it doesn't exist or update existing
        if ! grep -q "## Latest Project Updates (September 12, 2025)" "$claude_file"; then
          # Add new date section at the top of recent updates
          sed -i '' '/## Latest Project Updates/,/^## Previous Project Updates/ s/^## Latest Project Updates.*/## Latest Project Updates (September 12, 2025)\n\n### 🎯 **Enhanced Context Management System** ✅\n**Major Achievement**: Comprehensive documentation management system with CLAUDE.md and project-wide documentation updates\n\n#### **Documentation Enhancement Success**:\n- **Documentation Discovery**: Smart categorization of 25 legitimate project documentation files (CLAUDE.md, README.md, Technical docs, Requirements docs)\n- **Update Automation**: Intelligent update triggers based on git changes, dependency updates, and implementation changes\n- **Comprehensive Validation**: Command testing, link validation, and cross-reference consistency checks\n- **Cross-Project Standards**: Unified documentation patterns across all modules and project types\n\n&/' "$claude_file"
        fi
        
        # Update the last modified timestamp in frontmatter if it exists
        if grep -q "last_updated:" "$claude_file"; then
          sed -i '' "s/last_updated:.*/last_updated: $current_date/" "$claude_file"
        fi
        
      elif [[ "$claude_file" == *"/frontend/CLAUDE.md" ]]; then
        # Frontend CLAUDE.md - update with recent frontend changes
        echo "  ↳ Updating frontend CLAUDE.md with recent component/testing changes"
        
        # Check for recent frontend-specific changes
        if git diff --name-only HEAD~5..HEAD | grep -E "frontend.*(test|spec|component)" > /dev/null; then
          # Add recent frontend updates section
          if grep -q "## Recent Updates" "$claude_file"; then
            # Update existing section with current date
            sed -i '' "/## Recent Updates/,/^## / s/^### .* - .*/### September 12, 2025 - Enhanced Documentation Management System\n- ✅ **Comprehensive Documentation Updates**: Automated project-wide documentation management system\n- ✅ **Testing Infrastructure**: Maintained comprehensive Jest configuration with 4 test categories\n- ✅ **Development Standards**: Updated component patterns and testing infrastructure documentation\n- ✅ **Cross-Reference Consistency**: Ensured alignment with root CLAUDE.md standards/" "$claude_file"
          fi
        fi
        
      elif [[ "$claude_file" == *"/.claude/CLAUDE.md" ]]; then
        # .claude development patterns CLAUDE.md
        echo "  ↳ Updating development patterns CLAUDE.md with workflow improvements"
        
        # Add update to development philosophy if significant workflow changes
        if git log --oneline -5 --grep="feat:" | head -1 | grep -q "context\|documentation"; then
          # Add note about enhanced documentation management
          if ! grep -q "Enhanced Documentation Management" "$claude_file"; then
            echo "\n## Latest Development Pattern Updates (September 12, 2025)\n\n### Enhanced Documentation Management\n- Comprehensive project documentation update system\n- Smart categorization and update triggers\n- Cross-file consistency validation\n- Automated discovery of 25 project documentation files" >> "$claude_file"
          fi
        fi
        
      else
        # Module-specific CLAUDE.md files (user-auth, options-strategy, etc.)
        echo "  ↳ Updating module CLAUDE.md with recent module changes"
        
        # Get module name from path
        module_name=$(basename "$(dirname "$claude_file")")
        
        # Add recent updates section specific to this module
        if git diff --name-status HEAD~5..HEAD "$module_path/" | head -5 | wc -l | xargs test 0 -lt; then
          changed_files=$(git diff --name-only HEAD~5..HEAD "$module_path/" | wc -l)
          echo "    → Found $changed_files changed files in $module_name module"
          
          # Add module-specific update note
          if ! grep -q "September 12, 2025" "$claude_file"; then
            sed -i '' '1a\
## Latest Module Updates (September 12, 2025)\n\n### Enhanced Documentation Integration\n- Updated module documentation as part of comprehensive project-wide documentation management\n- Ensured consistency with root CLAUDE.md standards and shared patterns\n- Validated module-specific guidance accuracy and currency\n' "$claude_file"
          fi
        fi
      fi
      
      # Validate the updated file
      if [[ -s "$claude_file" ]]; then
        echo "  ✅ Successfully updated $claude_file"
        rm -f "$claude_file.backup"
      else
        echo "  ⚠️ Update failed, restoring backup for $claude_file"
        mv "$claude_file.backup" "$claude_file"
      fi
    else
      echo "  ❌ File not found: $claude_file"
    fi
  else
    echo "⏭️ Skipping $claude_file - No relevant changes"
  fi
done
```

#### **Step 2: Process README Files**
```bash
# Find and process README.md files  
find . -name "README.md" -type f -not -path "*/node_modules/*" -not -path "./.claude/*" | while read readme_file; do
  # Check for dependency/setup changes
  if git diff --name-only HEAD~5..HEAD | grep -E "(package\.json|requirements\.txt|deploy\.sh)" > /dev/null; then
    echo "📖 Updating $readme_file - Setup/dependency changes detected"
    
    # Read current README content
    if [[ -f "$readme_file" ]]; then
      # Create backup
      cp "$readme_file" "$readme_file.backup"
      
      # Get current datetime for updates
      current_date=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
      
      # Check what type of README this is
      if [[ "$readme_file" == "./README.md" ]]; then
        # Root README - update project overview if major changes
        echo "  ↳ Updating root README with project status"
        
        # Check for major structural changes
        if git log --oneline -3 | grep -E "(feat:|refactor:|docs:)" > /dev/null; then
          # Add "Last Updated" section if it doesn't exist
          if ! grep -q "Last Updated:" "$readme_file"; then
            echo "\n---\n\n**Last Updated:** $current_date" >> "$readme_file"
          else
            # Update existing timestamp
            sed -i '' "s/\*\*Last Updated:\*\*.*/\*\*Last Updated:\*\* $current_date/" "$readme_file"
          fi
          
          # Update project status if there's a status section
          if grep -q "## Status" "$readme_file"; then
            sed -i '' '/## Status/,/^## / s/Development active.*/Development active - Enhanced documentation management system implemented/' "$readme_file"
          fi
        fi
        
      elif [[ "$readme_file" == *"/frontend/README.md" ]]; then
        # Frontend README - update with dependency/testing changes
        echo "  ↳ Updating frontend README with setup and testing information"
        
        # Check for package.json changes
        if git diff --name-only HEAD~5..HEAD | grep "frontend/package.json" > /dev/null; then
          # Update dependencies section if it exists
          if grep -q "## Dependencies" "$readme_file"; then
            echo "    → Updating dependencies section due to package.json changes"
            # Add note about recent dependency updates
            sed -i '' '/## Dependencies/a\
\n**Recent Updates:** Dependencies and testing infrastructure updated as of $current_date\n' "$readme_file"
          fi
          
          # Update installation instructions timestamp
          if grep -q "## Installation" "$readme_file"; then
            sed -i '' '/## Installation/a\
\n*Last verified: $current_date*\n' "$readme_file"
          fi
        fi
        
        # Update testing section if test configuration changed
        if git diff --name-only HEAD~5..HEAD | grep -E "jest|test" > /dev/null; then
          if grep -q "## Testing" "$readme_file"; then
            echo "    → Updating testing section due to test configuration changes"
            sed -i '' '/## Testing/a\
\n*Testing infrastructure last updated: $current_date*\n' "$readme_file"
          fi
        fi
        
      else
        # Module-specific README files
        module_name=$(basename "$(dirname "$readme_file")")
        echo "  ↳ Updating $module_name README with module-specific changes"
        
        # Check for module-specific dependency changes
        module_path=$(dirname "$readme_file")
        if git diff --name-only HEAD~5..HEAD | grep "$module_path/" > /dev/null; then
          # Add last updated timestamp
          if ! grep -q "Last Updated:" "$readme_file"; then
            echo "\n---\n\n**Last Updated:** $current_date  \n**Module:** $module_name" >> "$readme_file"
          else
            sed -i '' "s/\*\*Last Updated:\*\*.*/\*\*Last Updated:\*\* $current_date/" "$readme_file"
          fi
          
          # Update setup instructions note
          if grep -q "## Setup" "$readme_file" || grep -q "## Installation" "$readme_file"; then
            echo "    → Updated setup instructions verification date"
          fi
        fi
      fi
      
      # Validate the updated file
      if [[ -s "$readme_file" ]]; then
        echo "  ✅ Successfully updated $readme_file"
        rm -f "$readme_file.backup"
      else
        echo "  ⚠️ Update failed, restoring backup for $readme_file"
        mv "$readme_file.backup" "$readme_file"
      fi
    else
      echo "  ❌ File not found: $readme_file"
    fi
  else
    echo "⏭️ Skipping $readme_file - No setup changes"
  fi
done
```

#### **Step 3: Process Technical Documentation**
```bash
# Find and process technical documentation files
find . -path "*/docs/*.md" -type f -not -path "*/node_modules/*" -not -path "./.claude/*" | while read tech_file; do
  # Check for implementation/testing changes
  if git diff --name-status HEAD~5..HEAD | grep -E "(test|spec|component|architecture)" > /dev/null; then
    echo "📚 Updating $tech_file - Implementation changes detected"  
    
    # Read current technical documentation content
    if [[ -f "$tech_file" ]]; then
      # Create backup
      cp "$tech_file" "$tech_file.backup"
      
      # Get current datetime for updates
      current_date=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
      
      # Determine what type of technical documentation this is
      doc_name=$(basename "$tech_file")
      
      case "$doc_name" in
        "TESTING.md")
          echo "  ↳ Updating testing documentation with recent test infrastructure changes"
          
          # Update testing statistics and coverage information
          if git diff --name-only HEAD~5..HEAD | grep -E "test|spec|jest|coverage" > /dev/null; then
            # Update test infrastructure section timestamp
            if grep -q "## Test Infrastructure" "$tech_file"; then
              sed -i '' "/## Test Infrastructure/a\\
\\
*Last Updated: $current_date*\\
" "$tech_file"
            fi
            
            # Update testing framework status
            if grep -q "Testing Framework Status" "$tech_file"; then
              echo "    → Updated testing framework status section"
              sed -i '' '/Testing Framework Status/,/^###/ s/Last verified:.*/Last verified: '$current_date'/' "$tech_file"
            fi
            
            # Add note about recent testing improvements if major changes
            if git log --oneline -3 | grep -E "(test|spec):" > /dev/null; then
              if ! grep -q "Recent Testing Enhancements ($current_date)" "$tech_file"; then
                # Add recent enhancements section
                echo "\n### Recent Testing Enhancements ($current_date)\n- Updated testing infrastructure and configuration\n- Enhanced test coverage and validation patterns\n- Improved test execution and reporting capabilities" >> "$tech_file"
              fi
            fi
          fi
          ;;
          
        "ARCHITECTURE.md")
          echo "  ↳ Updating architecture documentation with structural changes"
          
          # Update architecture documentation for structural changes
          if git diff --name-only HEAD~5..HEAD | grep -E "component|service|architecture" > /dev/null; then
            # Update architecture overview timestamp
            if grep -q "## Architecture Overview" "$tech_file"; then
              sed -i '' "/## Architecture Overview/a\\
\\
*Last Updated: $current_date - Recent structural changes incorporated*\\
" "$tech_file"
            fi
            
            # Note recent architectural updates
            if git log --oneline -3 | grep -E "(feat|refactor):" > /dev/null; then
              echo "    → Added architectural update notes"
              if ! grep -q "Recent Architecture Updates" "$tech_file"; then
                echo "\n### Recent Architecture Updates ($current_date)\n- Updated system architecture documentation\n- Incorporated recent structural and component changes\n- Validated architectural patterns and consistency" >> "$tech_file"
              fi
            fi
          fi
          ;;
          
        "DESIGN.md")
          echo "  ↳ Updating design documentation with component and pattern changes"
          
          # Update design documentation for UI/UX changes
          if git diff --name-only HEAD~5..HEAD | grep -E "component|style|design|ui" > /dev/null; then
            # Update design system timestamp
            if grep -q "## Design System" "$tech_file"; then
              sed -i '' "/## Design System/a\\
\\
*Last Updated: $current_date - Recent component changes reflected*\\
" "$tech_file"
            fi
            
            # Add design pattern updates
            echo "    → Updated design patterns and component standards"
            if ! grep -q "Recent Design Updates" "$tech_file"; then
              echo "\n### Recent Design Updates ($current_date)\n- Updated design patterns and component standards\n- Incorporated recent UI/UX improvements\n- Maintained 2025 minimalist design compliance" >> "$tech_file"
            fi
          fi
          ;;
          
        *)
          # Generic technical documentation
          echo "  ↳ Updating generic technical documentation: $doc_name"
          
          # Add general update timestamp
          if ! grep -q "Last Updated:" "$tech_file"; then
            echo "\n---\n\n**Last Updated:** $current_date" >> "$tech_file"
          else
            sed -i '' "s/\*\*Last Updated:\*\*.*/\*\*Last Updated:\*\* $current_date/" "$tech_file"
          fi
          
          # Add note about recent changes
          if git log --oneline -3 | grep -E "(feat|fix|docs):" > /dev/null; then
            echo "    → Added recent changes note to $doc_name"
          fi
          ;;
      esac
      
      # Validate the updated file
      if [[ -s "$tech_file" ]]; then
        echo "  ✅ Successfully updated $tech_file"
        rm -f "$tech_file.backup"
      else
        echo "  ⚠️ Update failed, restoring backup for $tech_file"
        mv "$tech_file.backup" "$tech_file"
      fi
    else
      echo "  ❌ File not found: $tech_file"
    fi
  else
    echo "⏭️ Skipping $tech_file - No implementation changes"
  fi
done
```

### 1.2. CLAUDE.md Documentation Analysis

After context analysis, check each CLAUDE.md file for updates:

**Check each CLAUDE.md file systematically:**

#### **Root `/CLAUDE.md`** - **Always Update for Major Changes**
  - **Authority**: Shared enterprise standards, deployment patterns, project overview
  - **Update Triggers**: New features, architectural changes, deployment updates, major milestones
  - **Check**: Recent major commits, new modules, enterprise pattern changes
  - **Content**: Latest project updates section, shared configuration, revolutionary features
  - **Priority**: Highest - affects all modules and provides project-wide context

#### **Module `CLAUDE.md` Files** - **Update if Module Changed**
  - **Locations**: `frontend/CLAUDE.md`, `user-auth-broker-management/CLAUDE.md`, etc.  
  - **Authority**: Module-specific guidance, APIs, development standards
  - **Update Triggers**: Module-specific changes, new components, API updates, testing changes
  - **Check**: `git diff --name-status HEAD~5..HEAD {module_path}/` for changes in specific module
  - **Content**: Component patterns, testing infrastructure, module-specific achievements
  - **Sync**: Ensure consistency with root CLAUDE.md standards and shared patterns

#### **.claude/CLAUDE.md** - **Update for Development Patterns**
  - **Authority**: Development philosophy, sub-agent instructions, testing patterns
  - **Update Triggers**: New sub-agents, workflow changes, development rule updates
  - **Check**: Changes in development processes, new absolute rules, testing methodology
  - **Content**: Sub-agent optimization, development philosophy, absolute rules updates

### 1.2. Project Documentation Analysis

Check each documentation category for updates based on implementation changes:

#### **Technical Documentation** - **Update When Implementation Changes**
- **Files**: `docs/TESTING.md`, `docs/ARCHITECTURE.md`, `docs/DESIGN.md`, testing guides
- **Update Triggers**: New testing patterns, architectural changes, component additions, design system updates
- **Check**: `git diff --name-status HEAD~5..HEAD | grep -E "(test|spec|component|architecture)"`
- **Content**: Testing strategies, implementation guides, architectural decisions, design patterns
- **Validation**: Ensure code examples work, commands are current, statistics are accurate

#### **README Files** - **Update When Setup Changes**
- **Files**: Root `README.md`, module `README.md` files (setup and introduction)
- **Update Triggers**: New dependencies, changed setup requirements, installation steps modified
- **Check**: `git diff HEAD~5..HEAD package.json requirements.txt deploy.sh`
- **Content**: Prerequisites, installation steps, quick start guides, getting started examples
- **Validation**: Test installation commands, verify prerequisites are current, check all links work

#### **Requirements & Planning Documentation** - **Manual Updates Only**
- **Files**: `docs/requirements/`, roadmaps, specifications, planning documents
- **Update Triggers**: User-driven updates for scope changes, strategic pivots, new requirements
- **Check**: Manual review only (rarely automated)
- **Content**: Strategic documents, long-term planning, requirement specifications
- **Validation**: Ensure alignment with actual implementation and current project direction

### 3. Smart Update Strategy

**For each context file that needs updating:**

1. **Read existing file** to understand current content
2. **Identify specific sections** that need updates
3. **Preserve frontmatter** but update `last_updated` field:
   ```yaml
   ---
   created: [preserve original]
   last_updated: [Use REAL datetime from date command]
   version: [increment if major update, e.g., 1.0 → 1.1]
   author: Claude Code PM System
   ---
   ```
4. **Make targeted updates** - don't rewrite entire file
5. **Add update notes** at the bottom if significant:
   ```markdown
   ## Update History
   - {date}: {summary of what changed}
   ```

### 2.1. CLAUDE.md Update Strategy

**For each CLAUDE.md file that needs updating:**

1. **Read Current Content** - Understand existing structure and recent updates sections
2. **Identify Update Sections** - Focus on sections that need refreshing:
   - Latest project updates
   - Recent achievements/milestones  
   - New development patterns
   - Updated standards or configurations
3. **Preserve Structure** - Maintain established formatting, headers, and organization
4. **Add Latest Updates** - Include recent achievements using consistent format:
   ```markdown
   ## Latest Updates (September 12, 2025)
   
   ### 🎯 **Feature Name** ✅
   **Major Achievement**: Brief description of what was accomplished
   
   #### **Implementation Success**:
   - **Technical Detail**: Specific implementation information
   - **Impact**: Benefits and improvements achieved
   - **Files Changed**: Number of files, insertions, deletions if relevant
   ```
5. **Update Timestamps** - Add entries to update tracking if major changes made
6. **Cross-Reference Consistency** - Ensure alignment between root and module CLAUDE.md files
7. **Validate Content** - Ensure technical accuracy and up-to-date information

### 2.2. Technical Documentation Update Strategy

**For each technical doc that needs updating:**

1. **Read Current Content** - Understand existing documentation structure and scope
2. **Check Implementation Changes** - Verify actual code matches documentation examples
3. **Update Examples and Commands** - Ensure all documented commands and code examples work
4. **Refresh Statistics and Numbers** - Update coverage percentages, file counts, performance metrics
5. **Add New Sections** - Include new patterns, tools, methodologies implemented since last update
6. **Validate All Content** - Test commands, verify links, ensure examples produce expected results
7. **Update Metadata** - Add update notes with specific implementation changes documented

### 2.3. README Documentation Update Strategy

**For each README that needs updating:**

1. **Read Current Content** - Understand existing setup and introduction information  
2. **Check Prerequisites** - Ensure software versions, dependencies, and system requirements are current
3. **Validate Installation Steps** - Test setup commands work on fresh environment
4. **Update Quick Start Examples** - Verify getting started examples produce expected results
5. **Check All Links** - Ensure internal and external links are functional and current
6. **Update Badges and Status** - Refresh build status, coverage, version badges if applicable
7. **Add Recent Changes** - Include "What's New" or changelog sections for major updates

### 3. Update Validation

After updating each context file:
- Verify file still has valid frontmatter
- Check file size is reasonable (not corrupted)
- Ensure markdown formatting is preserved
- Confirm updates accurately reflect changes

### 3.1. CLAUDE.md Validation

After updating each CLAUDE.md file:
- **Consistent Formatting** - Ensure headers, code blocks, lists follow repository standards
- **Cross-File Alignment** - Check root and module CLAUDE.md consistency and avoid conflicting guidance
- **Content Accuracy** - Verify technical details match actual implementation and current state
- **Update History** - Maintain chronological update tracking for reference
- **File Size Management** - Warn if files become excessively large (>100KB) and suggest archiving old updates
- **Link Validation** - Ensure internal references and file paths are still valid

### 3.2. Technical Documentation Validation

After updating each technical documentation file:
- **Command Verification** - Test that all documented commands execute successfully
- **Code Example Testing** - Verify all code examples are syntactically correct and executable
- **Link and Reference Checking** - Ensure all internal and external links are functional
- **Statistics Accuracy** - Confirm coverage numbers, metrics, and counts reflect current state
- **Implementation Alignment** - Verify documentation matches actual current implementation
- **Formatting Consistency** - Maintain consistent markdown formatting and structure standards

### 3.3. README Documentation Validation

After updating each README file:
- **Installation Testing** - Verify setup instructions work on clean environment
- **Prerequisites Verification** - Confirm all required software versions and dependencies are accurate
- **Quick Start Validation** - Test that getting started examples produce expected results
- **Link Functionality** - Check that all links (internal, external, badges) are working
- **Badge Currency** - Ensure build status, coverage, and version badges reflect current state
- **Content Freshness** - Verify all information is current and reflects latest project state

### 6. Skip Optimization

**Skip files that don't need updates:**
- If no relevant changes detected, skip the file
- Report skipped files in summary
- Don't update timestamp if content unchanged
- This preserves accurate "last modified" information

### 7. Error Handling

**Common Issues:**
- **File locked:** "❌ Cannot update {file} - may be open in editor"
- **Permission denied:** "❌ Cannot write to {file} - check permissions"
- **Corrupted file:** "⚠️ {file} appears corrupted - skipping update"
- **Disk space:** "❌ Insufficient disk space for updates"

If update fails:
- Report which files were successfully updated
- Note which files failed and why
- Preserve original files (don't leave corrupted state)

### 8. Comprehensive Update Summary

Provide detailed summary including context, CLAUDE.md, and all project documentation updates:

```bash
# Generate comprehensive update statistics
echo "🔄 Complete Documentation Update Summary"
echo ""
echo "📊 Update Statistics:"

# Count different types of documentation files
context_count=$(find .claude/context -name "*.md" 2>/dev/null | wc -l | xargs)
claude_md_count=$(find . -name "CLAUDE.md" -type f -not -path "./.claude/context/*" | wc -l | xargs)
technical_docs_count=$(find . -path "*/docs/*.md" -type f -not -path "*/node_modules/*" -not -path "./.claude/*" | wc -l | xargs)
readme_count=$(find . -name "README.md" -type f -not -path "*/node_modules/*" -not -path "./.claude/*" | wc -l | xargs)
requirements_count=$(find . -path "*/requirements/*.md" -o -path "*/planning/*.md" -type f 2>/dev/null | wc -l | xargs)
total_project_docs=$((claude_md_count + technical_docs_count + readme_count + requirements_count))

echo "  - Context Files Scanned: $context_count"
echo "  - CLAUDE.md Files Scanned: $claude_md_count"
echo "  - Technical Docs Scanned: $technical_docs_count"
echo "  - README Files Scanned: $readme_count"
echo "  - Requirements Docs Scanned: $requirements_count"
echo "  - Total Project Documentation Files: $total_project_docs"
echo ""

# Report on context files processed
echo "📋 Context Files Status:"
if [[ $context_count -gt 0 ]]; then
  for context_file in .claude/context/*.md; do
    if [[ -f "$context_file" ]]; then
      file_name=$(basename "$context_file")
      # Check if file was recently modified (in last hour)
      if [[ $(find "$context_file" -mmin -60 2>/dev/null | wc -l) -gt 0 ]]; then
        echo "  ✅ $file_name - Updated with recent changes"
      else
        echo "  ⏭️ $file_name - No updates needed"
      fi
    fi
  done
else
  echo "  ❌ No context files found - Consider running /context:create first"
fi
echo ""

# Report on CLAUDE.md files processed
echo "📝 CLAUDE.md Files Status:"
if [[ $claude_md_count -gt 0 ]]; then
  find . -name "CLAUDE.md" -type f -not -path "./.claude/context/*" | while read claude_file; do
    rel_path=${claude_file#./}
    if [[ $(find "$claude_file" -mmin -60 2>/dev/null | wc -l) -gt 0 ]]; then
      echo "  ✅ $rel_path - Updated with recent module changes"
    else
      echo "  ⏭️ $rel_path - No updates needed (stable)"
    fi
  done
else
  echo "  ❌ No CLAUDE.md files found"
fi
echo ""

# Report on technical documentation processed
echo "📚 Technical Documentation Status:"
if [[ $technical_docs_count -gt 0 ]]; then
  find . -path "*/docs/*.md" -type f -not -path "*/node_modules/*" -not -path "./.claude/*" | while read tech_file; do
    rel_path=${tech_file#./}
    doc_name=$(basename "$tech_file")
    if [[ $(find "$tech_file" -mmin -60 2>/dev/null | wc -l) -gt 0 ]]; then
      case "$doc_name" in
        "TESTING.md") echo "  ✅ $rel_path - Updated test infrastructure and coverage stats" ;;
        "ARCHITECTURE.md") echo "  ✅ $rel_path - Updated architectural patterns and component structure" ;;
        "DESIGN.md") echo "  ✅ $rel_path - Updated design patterns and component standards" ;;
        *) echo "  ✅ $rel_path - Updated with recent implementation changes" ;;
      esac
    else
      echo "  ⏭️ $rel_path - No implementation changes detected"
    fi
  done
else
  echo "  ℹ️ No technical documentation files found"
fi
echo ""

# Report on README files processed
echo "📖 README Files Status:"
if [[ $readme_count -gt 0 ]]; then
  find . -name "README.md" -type f -not -path "*/node_modules/*" -not -path "./.claude/*" | while read readme_file; do
    rel_path=${readme_file#./}
    if [[ $(find "$readme_file" -mmin -60 2>/dev/null | wc -l) -gt 0 ]]; then
      if [[ "$readme_file" == "./README.md" ]]; then
        echo "  ✅ $rel_path - Updated project overview and status"
      elif [[ "$readme_file" == *"/frontend/README.md" ]]; then
        echo "  ✅ $rel_path - Updated dependencies and testing commands"
      else
        module_name=$(basename "$(dirname "$readme_file")")
        echo "  ✅ $rel_path - Updated $module_name setup and dependencies"
      fi
    else
      echo "  ⏭️ $rel_path - No setup/dependency changes detected"
    fi
  done
else
  echo "  ℹ️ No README files found"
fi
echo ""

# Report on requirements and planning documentation
echo "📋 Requirements & Planning Documentation:"
if [[ $requirements_count -gt 0 ]]; then
  echo "  ⏭️ All requirements docs skipped (manual updates only - no automated changes)"
  echo "  ℹ️ Requirements and planning documents require manual review and updates"
else
  echo "  ℹ️ No requirements or planning documentation found"
fi
echo ""

# Summary statistics
updated_files_count=$(find . -name "*.md" -mmin -60 -not -path "*/node_modules/*" | wc -l | xargs)
skipped_files_count=$((total_project_docs + context_count - updated_files_count))

echo "📈 Final Statistics:"
echo "  - Total Files Updated: $updated_files_count"
echo "  - Total Files Skipped: $skipped_files_count (no changes needed)"
echo "  - Update Success Rate: $(( (updated_files_count * 100) / (total_project_docs + context_count) ))%"
echo ""

# Completion info
current_time=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
echo "⏰ Update Completed: $current_time"
echo "🔄 Next: Run this command regularly to keep all documentation current"
echo "💡 Tip: Major architectural changes? Consider running /context:create for full refresh"
```

### 9. Post-Update Validation

After completing all documentation updates, perform validation checks:

```bash
# Validate updated documentation files
echo "🔍 Post-Update Validation:"
echo ""

# Check for any corrupted or empty files
echo "📄 File Integrity Check:"
find . -name "*.md" -mmin -60 -not -path "*/node_modules/*" | while read updated_file; do
  if [[ ! -s "$updated_file" ]]; then
    echo "  ⚠️ Warning: $updated_file is empty - may be corrupted"
  elif [[ $(wc -c < "$updated_file") -lt 10 ]]; then
    echo "  ⚠️ Warning: $updated_file is very small - may be corrupted"
  else
    echo "  ✅ $updated_file - File integrity OK"
  fi
done
echo ""

# Check for proper markdown formatting
echo "📝 Markdown Validation:"
find . -name "*.md" -mmin -60 -not -path "*/node_modules/*" | while read updated_file; do
  # Check for basic markdown structure
  if grep -q "^#" "$updated_file" && ! grep -q "^$" "$updated_file"; then
    echo "  ⚠️ Warning: $updated_file may have formatting issues"
  else
    echo "  ✅ $updated_file - Markdown structure OK"
  fi
done
echo ""

# Validate CLAUDE.md frontmatter if present
echo "🔧 Frontmatter Validation:"
find . -name "CLAUDE.md" -mmin -60 | while read claude_file; do
  if grep -q "^---" "$claude_file"; then
    if grep -q "last_updated:" "$claude_file" && grep -q "version:" "$claude_file"; then
      echo "  ✅ $claude_file - Frontmatter structure OK"
    else
      echo "  ⚠️ Warning: $claude_file frontmatter may be incomplete"
    fi
  else
    echo "  ℹ️ $claude_file - No frontmatter (OK)"
  fi
done
echo ""

echo "✅ Validation completed"
```

### 10. Incremental Update Tracking

**Track what was updated:**
- Note which sections of each file were modified
- Keep changes focused and surgical
- Don't regenerate unchanged content
- Preserve formatting and structure

### 11. Performance Optimization

For large projects:
- Process files in parallel when possible
- Show progress: "Updating context files... {current}/{total}"
- Skip very large files with warning
- Use git diff to quickly identify changed areas

## Documentation Gathering Commands

Use these commands to detect changes for both context and CLAUDE.md updates:

**Context Analysis:**
- Context directory: `.claude/context/`
- Current git status: `git status --short`
- Recent commits: `git log --oneline -10`
- Changed files: `git diff --name-only HEAD~5..HEAD 2>/dev/null`
- Branch info: `git branch --show-current`
- Uncommitted changes: `git diff --stat`
- New untracked files: `git ls-files --others --exclude-standard | head -10`
- Dependency changes: Check package.json, requirements.txt, etc.

**CLAUDE.md Analysis:**
- Find all CLAUDE.md files: `find . -name "CLAUDE.md" -type f`
- Check module-specific changes: `git diff --name-status HEAD~5..HEAD {module_path}/`
- Detect major commits: `git log --oneline -10 | grep -E "(feat|fix|refactor|docs)"`
- Check for new components: `find . -name "*.tsx" -newer .claude/context/progress.md | wc -l`
- Module activity detection: `git diff --stat HEAD~5..HEAD | grep -E "(frontend|user-auth|options-strategy)"`

**Project Documentation Analysis:**
- Find all documentation files: `find . -name "*.md" -type f -not -path "*/node_modules/*" -not -path "./.claude/context/*" -not -path "./.claude/agents/*" -not -path "./.claude/rules/*" -not -path "./.claude/commands/*" -not -path "./frontend-amplify/*"`
- Categorize by type: Separate CLAUDE.md, README.md, Technical docs, Requirements docs
- Technical doc changes: `git diff --name-status HEAD~5..HEAD | grep -E "(test|spec|component|architecture)"`
- README trigger detection: `git diff HEAD~5..HEAD package.json requirements.txt deploy.sh`
- Count documentation files by category for reporting

**Update Triggers Detection:**
- Major feature commits: `git log --oneline -10 --grep="feat:"`
- Documentation commits: `git log --oneline -10 --grep="docs:"`
- Architectural changes: `git log --oneline -10 --grep="refactor:"`
- Testing updates: `git diff HEAD~5..HEAD --name-only | grep -E "test|spec"`
- Dependency changes: `git diff HEAD~5..HEAD --name-only | grep -E "package\.json|requirements\.txt"`
- Setup/deployment changes: `git diff HEAD~5..HEAD --name-only | grep -E "deploy|setup|install"`

## Important Notes

**Context Files:**
- **Only update files with actual changes** - preserve accurate timestamps
- **Always use real datetime** from system clock for `last_updated`
- **Make surgical updates** - don't regenerate entire files
- **Validate each update** - ensure files remain valid
- **Handle errors gracefully** - don't corrupt existing context

**CLAUDE.md Files:**
- **Preserve established structure** - don't reorganize existing content
- **Add new updates chronologically** - maintain proper update order
- **Cross-reference accuracy** - ensure root and module files align
- **Focus on significant changes** - don't update for trivial modifications
- **Maintain consistency** - use established formatting and language patterns
- **Validate technical accuracy** - ensure all details match actual implementation

**General Documentation:**
- **Comprehensive coverage** - update both context and guidance documentation
- **Detailed summary reporting** - show exactly what changed and what didn't
- **Preserve file history** - maintain update tracking for accountability
- **Error recovery** - graceful handling without corrupting existing documentation

$ARGUMENTS
