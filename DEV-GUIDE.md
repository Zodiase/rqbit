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
Cargo's package listing may resolve registry metadata, so the packaging test
allows network access and does not assume a pre-populated local Cargo cache.

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

## Keyboard deletion smoke check

Use `npm run dev:mock --workspace rqbit-webui` for fake torrents, not a live
session. This is a manual/browser-automation recipe, not an automated CI suite;
frontend test infrastructure is tracked in fork issue #6.

1. In compact view, select a row or its checkbox and press Delete (Backspace on
   a Mac keyboard also works). Confirm the dialog lists the intended selection
   and focuses its Delete button. Opening the dialog must not remove anything.
2. Press Enter and verify the selected mock torrent disappears. Repeat with
   two selected torrents. Tab to Cancel and press Enter to verify normal button
   activation remains intact.
3. Check "Also delete downloaded files", then cancel with Escape or the close
   button. Reopen and verify the option is unchecked. Default confirmation must
   use the forget operation, not file deletion.
4. Type in Search and press Backspace/Delete; no confirmation should open.
   Repeat with an unrelated modal open. Held/repeated keys must not reopen or
   repeatedly submit a confirmation.
5. While deletion is pending, repeat Enter/clicks. Only one batch should run;
   dismissal and changing the file-deletion option are blocked until it settles.
   Verify API errors remain visible and allow retry.

The confirmation is a native form: Delete is a submit button and Cancel is a
non-submit button. The form submit handler prevents navigation and invokes the
guarded deletion operation; no modal-specific Enter listener is needed.
The shared modal uses Restart UI's show lifecycle to focus the confirmation
after mounting; React autofocus alone can be overridden by the modal container.
Verify the same keyboard flow in the packaged macOS app before treating native
behavior as tested. Browser checks do not establish native WebView behavior.
