# Founder profile refresh

Installation was explicitly approved and completed directly in both original repositories using their respective signed-in accounts. No fork was created.

- Haziq: https://github.com/HaziqBinAfzal/HaziqBinAfzal/actions/runs/40902020024 — success
- Ruveeha: https://github.com/ruveeha33/ruveeha33/actions/runs/40902757192 — success

The retained founder-refresh.yml.txt is a reviewable source template; active copies are under .github/workflows/refresh-profile.yml in each founder repository. The updater is embedded in the workflow. The company manifest is fetched only as data.

Each workflow uses its built-in repository-scoped GITHUB_TOKEN to commit generated updates to its own repository. Runs every six hours, after README/SVG edits, and via manual Run workflow. Shared products and course records come from the company profile-data.json. Historical verification and manually written bios remain separate.
