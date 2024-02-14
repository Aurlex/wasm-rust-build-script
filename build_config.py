targets = [
    "wasm32-unknown-emscripten",
    "x86_64-unknown-linux-gnu",
    "x86_64-pc-windows-gnu",
]

cargo_command = "cargo build --release"
rustup = True
clean_build = False
dry_run = False
