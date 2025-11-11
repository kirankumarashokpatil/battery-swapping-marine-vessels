# GitHub Setup Guide
## Step-by-Step Instructions to Upload Your Battery Swapping Model

### Prerequisites
- Git installed on your computer ([Download Git](https://git-scm.com/download/win))
- GitHub account ([Sign up at github.com](https://github.com/join))

---

## Part 1: Create GitHub Repository

### Step 1: Create New Repository on GitHub
1. Go to [github.com](https://github.com) and log in
2. Click the **"+"** icon in top-right corner
3. Select **"New repository"**
4. Fill in the details:
   - **Repository name**: `battery-swapping-marine-vessels`
   - **Description**: "Battery swapping optimization tool for marine vessels with dynamic programming"
   - **Visibility**: Choose **Public** or **Private**
   - **DO NOT** initialize with README, .gitignore, or license (we already have these)
5. Click **"Create repository"**

---

## Part 2: Prepare Your Local Project

### Step 2: Open PowerShell in Your Project Directory
```powershell
cd "c:\Users\kiran\OneDrive\Documents\Natpower UK\Battery Swapping Model for Marine Vessels"
```

### Step 3: Initialize Git Repository (if not already done)
```powershell
git init
```

### Step 4: Configure Git (First Time Only)
```powershell
# Set your name and email (use your GitHub email)
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

### Step 5: Add Files to Git
```powershell
# Add all files to staging
git add .

# Check what will be committed
git status
```

### Step 6: Create Initial Commit
```powershell
git commit -m "Initial commit: Battery swapping optimization tool for marine vessels"
```

---

## Part 3: Connect to GitHub and Push

### Step 7: Add GitHub Remote
Replace `YOUR_USERNAME` with your actual GitHub username:

```powershell
git remote add origin https://github.com/YOUR_USERNAME/battery-swapping-marine-vessels.git
```

### Step 8: Rename Branch to 'main' (if needed)
```powershell
git branch -M main
```

### Step 9: Push to GitHub
```powershell
git push -u origin main
```

**Note**: You may be prompted to log in to GitHub. Use your GitHub credentials or a Personal Access Token.

---

## Part 4: GitHub Authentication (If Needed)

### Option A: GitHub Desktop (Easiest)
1. Download [GitHub Desktop](https://desktop.github.com/)
2. Install and sign in
3. Use File → Add Local Repository
4. Select your project folder
5. Click "Publish repository"

### Option B: Personal Access Token (Command Line)
If prompted for password:
1. Go to GitHub.com → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Click "Generate new token (classic)"
3. Select scopes: `repo` (full control of private repositories)
4. Copy the token
5. Use the token as your password when pushing

### Option C: GitHub CLI
```powershell
# Install GitHub CLI
winget install --id GitHub.cli

# Authenticate
gh auth login

# Push using gh
gh repo create battery-swapping-marine-vessels --source=. --public --push
```

---

## Part 5: Verify Upload

### Step 10: Check Your Repository
1. Go to `https://github.com/YOUR_USERNAME/battery-swapping-marine-vessels`
2. You should see all your files including:
   - `streamlit_app/main.py`
   - `fixed_path_dp.py`
   - `requirements.txt`
   - `README.md`
   - Documentation files

---

## Part 6: Update Repository Later

### When You Make Changes:
```powershell
# Check what changed
git status

# Add specific files
git add streamlit_app/main.py

# Or add all changes
git add .

# Commit with descriptive message
git commit -m "Add vessel animation and fix global settings"

# Push to GitHub
git push
```

---

## Troubleshooting

### Problem: "fatal: remote origin already exists"
**Solution:**
```powershell
git remote remove origin
git remote add origin https://github.com/YOUR_USERNAME/battery-swapping-marine-vessels.git
```

### Problem: "failed to push some refs"
**Solution:**
```powershell
# Pull first, then push
git pull origin main --allow-unrelated-histories
git push -u origin main
```

### Problem: Large files or .venv directory being uploaded
**Solution:**
The `.gitignore` file should prevent this. If not:
```powershell
# Remove .venv from git tracking
git rm -r --cached .venv
git commit -m "Remove virtual environment from tracking"
git push
```

### Problem: OneDrive sync conflicts
**Solution:**
```powershell
# Temporarily pause OneDrive sync during git operations
# Or move project outside OneDrive folder
```

---

## Quick Reference Commands

| Task | Command |
|------|---------|
| Check status | `git status` |
| Add all files | `git add .` |
| Commit changes | `git commit -m "message"` |
| Push to GitHub | `git push` |
| Pull from GitHub | `git pull` |
| View remotes | `git remote -v` |
| View commit history | `git log --oneline` |

---

## Making Your Repository Professional

### Add These Files (Already Created):
- ✅ `README.md` - Project documentation
- ✅ `.gitignore` - Ignore unnecessary files
- ⬜ `LICENSE` - Choose a license (MIT recommended for open source)
- ⬜ `CONTRIBUTING.md` - Contribution guidelines
- ⬜ `.github/workflows/` - CI/CD automation (optional)

### Repository Settings on GitHub:
1. **Add Topics**: Go to repository → About section → Add topics
   - Suggested: `battery-swapping`, `maritime`, `optimization`, `streamlit`, `python`, `dynamic-programming`
2. **Add Description**: Same as repository description
3. **Enable Issues**: For bug reports and feature requests
4. **Add License**: Settings → Add license file

---

## Example: Complete Upload Session

```powershell
# Navigate to project
cd "c:\Users\kiran\OneDrive\Documents\Natpower UK\Battery Swapping Model for Marine Vessels"

# Initialize (first time only)
git init

# Configure (first time only)
git config --global user.name "Kiran"
git config --global user.email "kiran@example.com"

# Add files
git add .

# Commit
git commit -m "Initial commit: Battery swapping optimization tool"

# Connect to GitHub (replace YOUR_USERNAME)
git remote add origin https://github.com/YOUR_USERNAME/battery-swapping-marine-vessels.git

# Push
git branch -M main
git push -u origin main
```

---

## Next Steps After Upload

1. **Update README.md** with:
   - Live demo link (if you deploy to Streamlit Cloud)
   - Screenshots of the UI
   - Example results

2. **Deploy to Streamlit Cloud** (Free):
   - Go to [share.streamlit.io](https://share.streamlit.io)
   - Connect your GitHub account
   - Deploy your repository
   - Share the live URL!

3. **Add GitHub Actions** for:
   - Automated testing
   - Code quality checks
   - Documentation generation

---

## Need Help?

- GitHub Docs: https://docs.github.com/en/get-started
- Git Tutorial: https://git-scm.com/book/en/v2
- Streamlit Deployment: https://docs.streamlit.io/streamlit-community-cloud

---

**Created**: November 11, 2025
**Project**: Battery Swapping Model for Marine Vessels
**Author**: Natpower UK
