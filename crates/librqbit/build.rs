fn main() {
    #[cfg(feature = "webui")]
    {
        // Frontend preparation is explicit: Rust builds never install or execute npm.
        for asset in [
            "index.html",
            "assets/index.js",
            "assets/index.css",
            "assets/logo.svg",
        ] {
            let path = std::path::Path::new("webui/dist").join(asset);
            println!("cargo:rerun-if-changed={}", path.display());
            assert!(
                path.is_file(),
                "Missing web UI asset {}. From the repository root run: npm ci --ignore-scripts && npm run build --workspace rqbit-webui",
                path.display()
            );
        }
    }
}
