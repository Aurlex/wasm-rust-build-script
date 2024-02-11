# wasm-rust-build-script
### Builds rust crates which use libraries that link to system libraries.

## My recommendation is that if you need to build a WASM crate with c ffi, build for the wasm-wasi-preview1-threads target, as it does not require wasi-sdk.

This python script will (attempt to) build all crates in the immediate subdirectories of the current directory. You can open the python folder and fiddle with the variables at the top to control it's behaviour.

I made this because it was very annoying to figure out how to build liblzma-sys for WASM, and needed a build tool for a project.

This has a high chance to work if the library you are using has WASM support.
An example being the liblzma-sys and xz2 crates. They both link to the same system libraries, but liblzma-sys has support for WASM, and xz2 does not. (I think)
