# Deployment Guide (GitHub Pages)

## 1. Push code to GitHub
Push branch `main` to your repository.

## 2. Enable Pages
In GitHub repository:
1. `Settings` -> `Pages`
2. Build and deployment source: `GitHub Actions`

## 3. Automatic deploy
Workflow file: `.github/workflows/pages.yml`

Each push to `main` triggers deployment.

## 4. Check URL
After workflow succeeds, GitHub Pages URL appears in the workflow summary.
