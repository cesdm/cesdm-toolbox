# GitHub Pages setup

The repository includes `.github/workflows/docs.yml`. It builds the MkDocs site for pull requests and deploys updates from `main`.

## One-time repository setting

1. Open **Settings → Pages**.
2. Under **Build and deployment**, select **GitHub Actions** as the source.
3. Push to `main`, or run the **Documentation** workflow manually.

The published site URL is configured in `mkdocs.yml`.
