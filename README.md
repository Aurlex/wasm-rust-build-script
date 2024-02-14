# wasm-rust-build-script (works on my machine™)
### Builds rust crates which use libraries that link to system libraries.

## My recommendation is that if you need to build a WASM crate with c ffi, build for wasm32-unknown-emscripten. It's easier than trying to get it to work for unknown-unknown, and wasi-preview1-threads is too immature. wasm32-wasi is decent, but I had trouble with it.

This python script will (attempt to) first build the crate in the current directory, and failing that, build all crates in the immediate subdirectories of the current directory. You can open build_config.py and fiddle with the variables to control its behaviour.

I made this because it was very annoying to figure out how to build liblzma-sys for WASM, due to my unfamiliarity with WASM build tools.

This has a high chance to work if the library you are using has WASM support, and the script works properly (lol)
An example being the liblzma-rs and xz2 crates. They both link to the same system libraries, but liblzma-rs has support for WASM, and xz2 does not. (I think) (update: sort of, yes, but not as good as liblzma-rs)
