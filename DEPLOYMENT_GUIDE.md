# Deployment Guide (GitHub Pages)

## 1. Push code to GitHub
Push branch `main` to your repository.

## 2. Enable Pages
In GitHub repository:
1. `Settings` -> `Pages`
2. Build and deployment source: `GitHub Actions`

## 3. Automatic deploy
Workflow file: `.github/workflows/pages.yml`

Each push to `main` triggers deployment of `frontend/`.

## 4. Check URL
After workflow succeeds, GitHub Pages URL appears in the workflow summary.

## 5. Common failure checks (Deployments)
If deployment fails in GitHub `Deployments`, verify:
1. `Settings` -> `Pages` -> Source is `GitHub Actions` (not branch deploy mode).
2. `Settings` -> `Actions` -> `General` -> Workflow permissions is `Read and write permissions`.
3. `Settings` -> `Environments` -> `github-pages` has no blocking protection rule, or approve the deployment manually.
4. You pushed to `main` (workflow trigger is configured for `main` only).
