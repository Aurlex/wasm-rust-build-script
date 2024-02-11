# Aurlex's super build tool thing of doom 3000.

# Main purpose is to build rust crates that use C libraries on WASM targets.
# Requires you to have the appropriate build tools installed. (https://github.com/rust-lang/cc-rs#compile-time-requirements)

import sys
from tarfile import open as open_tar
from zipfile import ZipFile
from os import path, mkdir, remove, system, environ, listdir, chdir
from shutil import which
from subprocess import run
from urllib import request

# -------Things for you to touch--------
use_rustup = True
clean_build = False
dry_run = False
targets = [
    "wasm32-unknown-unknown",
    "x86_64-unknown-linux-gnu",
    "x86_64-pc-windows-gnu",
]
cargo_command = "cargo build --release"
rustflags = ""
# --------------------------------------

working_directory = path.dirname(path.abspath(__file__))

if use_rustup:
    if which("rustup") is None:
        print("Installing rustup now.")
        if sys.platform == "win32":
            if not path.exists("rustup-init.exe"):
                request.urlretrieve("https://win.rustup.rs/x86_64", "rustup-init.exe")
            system(f"{working_directory}/rustup-init.exe -y")
            remove(f"{working_directory}/rustup-init.exe")
        else:
            request.urlretrieve("https://sh.rustup.rs", "rustup.sh")
            system(f"sh {working_directory}/rustup.sh -y")
            remove(f"{working_directory}/rustup.sh")
        print("Installation probably succeeded.")

    installed_targets = run(
        ["rustup", "target", "list", "--installed"], capture_output=True
    ).stdout.splitlines()
    for target in targets:
        if target.encode("utf-8") not in installed_targets:
            print(f"Installing: {target}")
            system(f"rustup target add {target}")

environ["RUSTFLAGS"] = rustflags

try:
    host_arch, host_device, host_platform, host_compiler = (
        run(["rustup", "show"], capture_output=True)
        .stdout.splitlines()[0]
        .split(b":")[1]
        .split(b"-")
    )
except:
    host_arch, host_device, host_platform = (
        run(["rustup", "show"], capture_output=True)
        .stdout.splitlines()[0]
        .split(b":")[1]
        .split(b"-")
    )
    host_compiler = None

for target in targets:
    try:
        arch, device, platform, compiler = target.split("-")
    except:
        arch, device, platform = target.split("-")
        compiler = None
    if arch == "wasm32":
        if host_platform == b"darwin":
            platform = "-macos"
        elif host_platform == b"linux":
            platform = "-linux"
        elif host_platform == b"windows":
            platform = ".m-mingw"
        else:
            raise Exception("Unsupported operating system")
        wasi_path = f"{working_directory}/wasi-sdk-21.0{platform}"

        if not path.exists(f"{wasi_path}"):
            print(f"Downloading wasi-sdk-21.0{platform}. This may take a while.")
            request.urlretrieve(
                f"https://github.com/WebAssembly/wasi-sdk/releases/download/wasi-sdk-21/wasi-sdk-21.0{platform}.tar.gz",
                f"{working_directory}/wasi-sdk.tar.gz",
            )
            print("Download finished. Extracting now.")
            mkdir(f"{wasi_path}")
            open_tar(f"{working_directory}/wasi-sdk.tar.gz").extractall(f"{wasi_path}")
            print("Cleaning up...")
            remove(f"{working_directory}/wasi-sdk.tar.gz")

        wasi_path += f"/wasi-sdk-21.0"
        if platform == ".m-mingw":
            wasi_path += "+m"

        environ[f"CC_{target}"] = (
            f"{wasi_path}/bin/clang.exe"
            if host_platform == b"windows"
            else f"{wasi_path}/bin/clang"
        )
        environ[f"CARGO_TARGET_{target.upper()}_LINKER"] = f"{wasi_path}/bin/clang"
    elif (
        (platform == "linux" or platform == "windows")
        and compiler == "gnu"
        and host_platform == b"windows"
        and host_compiler == b"msvc"
    ):
        print("hello")
        if which("cc") is None:
            if not path.exists(f"{working_directory}/mingw64"):
                request.urlretrieve(
                    "https://github.com/brechtsanders/winlibs_mingw/releases/download/13.2.0posix-17.0.6-11.0.1-ucrt-r5/winlibs-x86_64-posix-seh-gcc-13.2.0-llvm-17.0.6-mingw-w64ucrt-11.0.1-r5.zip",
                    f"{working_directory}/winlibs.zip",
                )
                ZipFile(f"{working_directory}/winlibs.zip").extractall(
                    f"{working_directory}"
                )
                remove(f"{working_directory}/winlibs.zip")
            environ[f"AR_{target}"] = f"{working_directory}/mingw64/bin/ar.exe"
            environ[f"CC_{target}"] = f"{working_directory}/mingw64/bin/gcc.exe"
            environ[f"CARGO_TARGET_{target.upper()}_LINKER"] = (
                f"{working_directory}/mingw64/bin/gcc.exe"
            )

if not dry_run:
    for local_path in listdir(working_directory):
        full_path = f"{working_directory}/{local_path}"
        if path.isdir(f"{full_path}"):
            if path.exists(f"{full_path}/Cargo.toml"):
                chdir(f"{full_path}")
                if clean_build:
                    system("cargo clean")
                target_str = "--target=" + (" --target=".join(targets))
                system(f"{cargo_command} {target_str}")
