# Aurlex's super build tool thing of doom 3000.

# Main purpose is to build rust crates that use C libraries on WASM targets.
# Requires you to have the appropriate build tools installed. (https://github.com/rust-lang/cc-rs#compile-time-requirements)

import os
import sys
import tarfile
import shutil
import subprocess
from urllib import request

# -------Things for you to touch--------
use_rustup = True
targets = [
  "wasm32-unknown-unknown",
  "x86_64-unknown-linux-gnu",
  "x86_64-pc-windows-gnu",
]
wasi_version_major = "21"
wasi_version_minor = "0"
cargo_args = "--release"
# --------------------------------------

wasi_version = wasi_version_major + "." + wasi_version_minor

platform = ""
if sys.platform == "darwin":
  platform = "-macos"
elif sys.platform == "linux":
  platform = "-linux"
elif sys.platform == "win32":
  platform = ".m-mingw"
else:
  raise Exception("Unsupported operating system")

working_directory = os.path.dirname(os.path.abspath(__file__))
wasi_path = f"wasi-sdk-{wasi_version}{platform}"
wasi_path_full = f"{working_directory}/{wasi_path}"

if not os.path.exists(f"{wasi_path_full}"):
  print(f"Downloading wasi-sdk-{wasi_version}{platform}. This may take a while.")
  request.urlretrieve(f"https://github.com/WebAssembly/wasi-sdk/releases/download/wasi-sdk-{wasi_version_major}/wasi-sdk-{wasi_version}{platform}.tar.gz", "wasi-sdk.tar.gz")
  print("Download finished. Cleaning up now.")
  os.mkdir(f"{wasi_path_full}")
  tarfile.open("wasi-sdk.tar.gz").extractall(f"{wasi_path_full}")
  os.remove("wasi-sdk.tar.gz")

wasi_path_full += f"/wasi-sdk-{wasi_version}"

for triple in ["unknown_unknown", "unknown_emscripten", "wasi", "wasi_preview1_threads"]:
  os.environ[f"CC_wasm32_{triple}"] = f"{wasi_path_full}/bin/clang" 
  os.environ[f"CARGO_TARGET_WASM32_{triple.upper()}_LINKER"] = f"{wasi_path_full}/bin/clang" 

if use_rustup:
  if shutil.which("rustup") is None:
    if platform == ".m-mingw":
      if not os.path.exists("rustup-init.exe"):
        request.urlretrieve("https://win.rustup.rs/x86_64", "rustup-init.exe")
      os.system(f"{working_directory}/rustup-init.exe -y")
    else:
      os.system("curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -y")
  
  installed_targets = [ line.decode("utf-8") for line in subprocess.run("rustup component list --installed", capture_output=True, shell=True).stdout.splitlines() ]
  for target in targets:
    needs_install = True
    for installed_target in installed_targets:
      if target in installed_target:
        needs_install = False
    if needs_install:
      os.system(f"rustup target add {target}")

for path in os.listdir(working_directory):
  full_path = f"{working_directory}/{path}"
  if os.path.isdir(f"{full_path}"):
    if os.path.exists(f"{full_path}/Cargo.toml"):
      os.chdir(f"{full_path}")
      for target in targets:
        os.system(f"cargo build {cargo_args} --target={target}")