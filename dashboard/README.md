# GitHub Pages configuration for AICheck Dashboard

This directory is served via GitHub Pages at:
https://zjyyong2.github.io/AICheck/

## Directory Structure

```
dashboard/
├── index.html          # Main dashboard page
└── data/               # JSON data files (auto-generated)
    ├── speed_data.json
    ├── quality_data.json
    └── alerts_data.json
```

## Auto-Update

The dashboard data is automatically updated via GitHub Actions:
- **Hourly**: Degradation detection runs
- **Daily**: Speed test runs

After each run, the data is exported to JSON files in the `dashboard/data/` directory.

## Manual Update

To manually update the dashboard data:

```bash
python -m ai_token_tester --export-dashboard dashboard/data
```

Then commit and push the changes:

```bash
git add dashboard/data/
git commit -m "Update dashboard data"
git push
```

## GitHub Actions

The following workflows handle automatic testing and data updates:

1. `.github/workflows/hourly-degradation.yml` - Runs degradation detection every hour
2. `.github/workflows/daily-test.yml` - Runs speed test daily at 2 AM

Both workflows will commit updated data to the repository, which will trigger GitHub Pages to rebuild.