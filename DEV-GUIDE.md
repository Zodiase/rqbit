# Development guide

## Rust

For builds with the `webui` feature (including desktop), prepare assets first:

    make webui-build

This runs `npm ci --ignore-scripts` and an explicit frontend build. Rust's
build script never invokes npm or downloads frontend dependencies. Repeat the
frontend build after editing web UI source; existing assets are not a freshness
check. Builds without `webui` do not require Node.

Then run with

    make devserver

## Web UI

Start the server

    make devserver

Run Web UI dev

    make webui-dev

## Desktop app

Stop the devserver, otherwise ports will conflict.

Install deps

    cargo install tauri-cli
    make webui-build

Run tauri dev

    cargo tauri dev

## CI hardening checks

Before packaging or publishing `librqbit`, run `make webui-build`. The crate
explicitly includes the four generated web assets, not node_modules or frontend
source. Packaging without these assets is not supported for webui consumers.
The security tests inspect Cargo's package file list, execute its asset-checking
build script, and compile include_str checks against those selected assets in an
isolated directory. This focused check does not replace a full packaged-crate
build, which also requires published sibling dependencies.

    npm ci --ignore-scripts
    npm run build --workspace rqbit-webui
    python3 scripts/test_ci_security.py

Actions use full commit pins, with the original reference retained as a comment.
Resolve updates from the action owner's repository and review the change before
updating a pin. Pinning prevents silent reference changes; it does not certify
the pinned code or its dependencies. Explicit frontend build commands still
execute project code and build-tool dependencies, even with install scripts off.

To update an action pin:

1. Resolve the intended reference in the owning repository, for example
   `gh api repos/actions/checkout/commits/v4 --jq .sha`.
2. Review the source changes and release notes between the old and new commits.
   Verify the commit belongs to the owner, not an unrelated fork.
3. Replace the full SHA and update the reference comment in each affected workflow.
   Local actions use repository-relative paths; container actions require a
   `sha256` image digest rather than a floating tag.
4. Run the security checks above and submit a PR. Require CI to pass before merging;
   leave disabled release workflows disabled unless separately approved.

These tests parse YAML, but do not fully parse shell programs or audit dependency
code. Their policy checks are regression guardrails, not a sandbox.
