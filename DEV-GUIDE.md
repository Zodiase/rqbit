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

    python3 scripts/test_ci_security.py

Actions use full commit pins, with the original reference retained as a comment.
Resolve updates from the action owner's repository and review the change before
updating a pin. Pinning prevents silent reference changes; it does not certify
the pinned code or its dependencies. Explicit frontend build commands still
execute project code and build-tool dependencies, even with install scripts off.
