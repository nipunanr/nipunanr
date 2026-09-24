# Setup (5 minutes)

1. Create a public repo named exactly `nipunanr` (same as your username) and tick "Add a README".
2. Upload everything from this folder, keeping the structure:
   - README.md
   - assets/hero.svg, assets/skills.svg, assets/divider.svg
   - .github/workflows/snake.yml and .github/workflows/stats.yml
   - scripts/generate_stats.py
   - assets/generated/ (4 placeholder SVGs)
3. Repo > Settings > Actions > General > Workflow permissions > "Read and write permissions" > Save.
4. Repo > Actions > run "Generate Snake" and then "Update Profile Stats" (Run workflow on each). Snake creates the `output` branch; Stats fills assets/generated with your real numbers. Both then refresh automatically. Optional: add a `STATS_TOKEN` secret (a PAT with read:user) to include private contributions.
5. Open github.com/nipunanr. Done. Delete this file if you don't want it in the repo.
