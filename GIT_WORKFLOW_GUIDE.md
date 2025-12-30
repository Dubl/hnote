# Git Workflow Guide for hello-rust

Welcome to version control! This guide will help you use Git effectively with your MIDI music generation project.

## What Just Happened?

Your repository has been cleaned up and organized:
- ✅ Git is configured with your name (Jon) and email (jkeskit@gmail.com)
- ✅ Initial commit created with your core source files
- ✅ Backup files and data files are now ignored by Git
- ✅ Clean working directory

## Essential Git Commands

### Check Status
See what files have changed:
```bash
cd ~/hello-rust
git status
```

### View Changes
See what you've modified:
```bash
git diff                    # See unstaged changes
git diff --staged           # See staged changes
```

### Save Your Work (Commit)
When you've made meaningful progress (fixed a bug, added a feature):
```bash
# 1. Add files you want to commit
git add src/main.rs                    # Add specific file
git add src/                           # Add all changed files in src/
git add .                              # Add all changed files

# 2. Create a commit with a message
git commit -m "Fix MIDI timing bug in playback"
```

### View History
See your commit history:
```bash
git log                     # Full history
git log --oneline           # Compact view
git log --oneline -5        # Last 5 commits
```

### Undo Changes
Made a mistake? Here's how to fix it:
```bash
# Discard changes to a specific file (CAREFUL: can't undo!)
git checkout -- src/main.rs

# Unstage a file (keep the changes)
git restore --staged src/main.rs

# See what changed in last commit
git show
```

## Daily Workflow

### When You Start Working
```bash
cd ~/hello-rust
git status                  # See current state
```

### While Working
- Edit your code as normal
- Run `git status` occasionally to see what's changed
- No need to create manual backup files anymore!

### When You Complete a Task
```bash
# Check what you changed
git status
git diff

# Add and commit your changes
git add src/
git commit -m "Brief description of what you did"
```

## Stop Creating Backup Files!

**Old way (don't do this):**
- Copy `main.rs` to `main_backup20250315.rs`
- Creates clutter
- Hard to track what changed
- Waste of disk space

**New way (do this):**
```bash
# Just commit your work regularly
git add src/main.rs
git commit -m "Working MIDI playback implementation"

# Later, if you want to see or restore old versions
git log                                    # Find the commit
git show <commit-hash>:src/main.rs        # View old version
git checkout <commit-hash> -- src/main.rs # Restore old version
```

## Advanced: Using Branches for Experiments

When you want to try something experimental without affecting your working code:

```bash
# Create and switch to a new branch
git checkout -b experimental-feature

# Make changes, commit as usual
git add .
git commit -m "Try new algorithm"

# Switch back to main code
git checkout master

# If experiment worked, merge it
git merge experimental-feature

# If experiment failed, just delete the branch
git branch -d experimental-feature
```

## Good Commit Messages

**Bad:**
- "update"
- "fix stuff"
- "changes"

**Good:**
- "Fix MIDI timing drift in long sequences"
- "Add support for triplet rhythms"
- "Refactor song_generator to use iterator pattern"

## Tips

1. **Commit Often**: Small, focused commits are better than large ones
2. **One Logical Change Per Commit**: Don't mix bug fixes with new features
3. **Test Before Committing**: Make sure your code works
4. **Use Descriptive Messages**: Your future self will thank you

## Current Repository State

Your .gitignore automatically excludes:
- Build artifacts (`/target`)
- Backup files (`*backup*.rs`, `*_backup*.rs`)
- Data files (`*.json`, `*.jsonc`, `*.csv`)
- Editor files (`.vscode/`, `.idea/`)
- OS files (`Thumbs.db`, `.DS_Store`)

This means these files will stay on your disk but won't be tracked by Git.

## Need Help?

Common issues:

**"I made a mistake in my last commit"**
```bash
# If you haven't pushed to a remote
git commit --amend -m "Corrected message"
```

**"I want to see what I changed 3 commits ago"**
```bash
git log --oneline        # Find the commit hash
git show <commit-hash>
```

**"I accidentally committed the wrong file"**
```bash
# Before pushing
git reset --soft HEAD~1  # Undo commit, keep changes
git reset HEAD <file>    # Unstage the file
```

## Next Steps

Consider setting up a remote repository on GitHub:
1. Create a GitHub account (if you don't have one)
2. Create a new repository on GitHub
3. Link your local repo to GitHub:
   ```bash
   git remote add origin https://github.com/yourusername/hello-rust.git
   git push -u origin master
   ```

This provides backup and allows you to access your code from anywhere.

---

**Remember:** Git is your time machine for code. Use it to explore freely without fear!
