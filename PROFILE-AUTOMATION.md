# Automatic profile refresh

All three profile refreshes are active and their first live runs passed. The personal workflows embed the reviewed updater; they do not download executable code. The retained installer template is automation/templates/founder-refresh.yml.txt.

Verified runs:
- Company: https://github.com/HR-Presents/HR-Presents/actions/runs/40901535803
- Haziq: https://github.com/HaziqBinAfzal/HaziqBinAfzal/actions/runs/40902020024
- Ruveeha: https://github.com/ruveeha33/ruveeha33/actions/runs/40902757192

The intended deployments use the Refresh profile workflow; the company uses scripts/refresh_profile.py.

## What updates automatically

- Account followers/following, public repository counts, stars and forks.
- Rolling-year contribution calendar and total.
- Byte-weighted language distribution across public non-fork repositories.
- Company AegisLog repository metrics, latest release link and publishing-workflow result.
- Product/course titles, URLs, summaries and matching SVG text from the company profile-data.json.

## Shared editing

Edit https://github.com/HR-Presents/HR-Presents/blob/main/profile-data.json once. The company refreshes after the push; the founder repositories fetch that public data at their next six-hour refresh, or via Actions > Refresh profile > Run workflow. Shared card text preserves the existing SVG artwork. Keep the same number of lines and fit text to existing card widths.

Editable bios, project explanations, education, credentials and historical test evidence stay hand maintained. A project code change does not automatically rewrite prose or imply a new verification run. Linked images/files always point to the current branch, subject to GitHub cache delays.

## Timing and verification

Runs every six hours at minute 23 UTC, after profile/script/SVG edits, and manually. GitHub schedules may be delayed. The first successful run replaces the seed images. Images show the last successful refresh time; source data is in assets/dynamic/data.json. The refresh badge links to real run results. If collection fails, the workflow fails and keeps previously committed graphics rather than inventing values.

Uses only Python's standard library and the built-in repository-scoped GITHUB_TOKEN. Public API data only; no PAT or new account secret is required. Each workflow writes only its own repository and fetches the company manifest as data, never as executable code. Generated bot pushes do not recursively start workflows.

## Important limits

GitHub may disable scheduled workflows after long repository inactivity. Re-enable the workflow or run it manually if necessary. Historical evidence keeps its date. Primary narrative text is not machine generated. Adding a new product requires a manifest entry plus its intended README placement.
