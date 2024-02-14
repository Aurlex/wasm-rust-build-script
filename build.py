# Aurlex's super build tool thing of doom 3000 v2. (henceforth thing of doom 6000)
# This is so much better but also not <3
# Config was moved to build_config.py

# Main purpose is to build rust crates for any platform without me having to be intelligent
# Requires you to have python, and maybe a few other things. (I will add them as needed)

from enum import Enum
from os import path, mkdir, remove, environ, listdir, system, getcwd
from shutil import which, unpack_archive, copyfileobj, move
from subprocess import run
from urllib.request import urlopen
from sys import platform as system_platform


class Platform(Enum):
    Windows = "windows", "nt", "win32"
    Linux = ("linux",)
    Darwin = "macos", "darwin"
    Posix = *Linux, *Darwin
    All = *Windows, *Linux, *Darwin

    def current(posix_switch: bool = False) -> "Platform":
        if posix_switch and system_platform in Platform.Posix:
            return Platform.Posix
        for platform in Platform:
            if system_platform in platform.value:
                return platform


cwd = path.dirname(path.abspath(__file__)).replace("\\", "/")
path_sep = ";" if system_platform == "win32" else ":"


def extract(file_name: str, dir_name: str, archive_type: str):
    unpack_archive(file_name, dir_name, archive_type)
    while True:
        contents = listdir(dir_name)
        if len(contents) == 1 and path.isdir(f"{dir_name}/{contents[0]}"):
            for file in listdir(f"{dir_name}/{contents[0]}/"):
                move(f"{dir_name}/{contents[0]}/{file}", f"{dir_name}/{file}")
            try:
                remove(f"{dir_name}/{contents[0]}")
            except:
                pass
        else:
            break


class Install:
    def __init__(self, name: str):
        self.name = name
        self.aliases: list[str] = []
        self.links: dict[
            Platform, tuple[str, str, str | None, str | None, str | None]
        ] = {}
        self.path: str = cwd

    def add_alias(self, alias: str) -> "Install":
        self.aliases.append(alias)
        return self

    def with_install_path(self, path: str) -> "Install":
        self.path = path.dirname(path.abspath(path))
        return self

    def has_command(self) -> bool:
        return any(which(alias) is not None for alias in self.aliases)

    def add_link(
        self,
        link: str,
        file_type: str,
        platform: Platform = Platform.All,
        custom_name: str | None = None,
        arguments: str | None = None,
        subdir: str | None = None,
    ) -> "Install":
        if file_type not in ("zip", "tar", "gztar", "bztar", "xztar", "exe", "sh"):
            raise ValueError(f"Invalid file type: {file_type}")
        self.links[platform] = (link, file_type, custom_name, arguments, subdir)
        return self

    def build(self) -> bool:
        try:
            if self.path is None:
                raise ValueError(
                    "Path not given.\nUse Install.add_path() to add a path."
                )
            if not path.exists(self.path) or not path.isdir(self.path):
                raise IOError(
                    f'Path "{self.path}" does not exist or is not a directory.'
                )
            if self.has_command():
                print(f"Already installed: {self.name}")
                return True
            for platform, (
                link,
                file_type,
                custom_name,
                arguments,
                subdir,
            ) in self.links.items():
                if system_platform not in platform.value:
                    continue
                if custom_name is None:
                    dir_name = f"{self.path}/{self.name}-{platform}-folder"
                    file_name = f"{self.path}/{self.name}-{platform}"
                else:
                    dir_name = f"{self.path}/{custom_name}-folder"
                    file_name = f"{self.path}/{custom_name}"
                if not path.exists(dir_name) and not path.exists(file_name):
                    print(f"Installing in {self.path}")
                    print(f"Downloading {link}")
                    with urlopen(link) as stream, open(file_name, "wb") as file:
                        copyfileobj(stream, file)
                    if file_type in ("zip", "tar", "gztar", "bztar", "xztar"):
                        mkdir(dir_name)
                        print(f"Extracting to {dir_name}")
                        extract(file_name, dir_name, file_type)
                        if subdir is not None:
                            mkdir(f"{dir_name}/{subdir}")
                            for dir in listdir(dir_name):
                                if dir != subdir:
                                    move(
                                        f"{dir_name}/{dir}",
                                        f"{dir_name}/{subdir}/{dir}",
                                    )
                    elif file_type in ("exe", "sh"):
                        print(f"Opening executable...")
                        system(f"{file_name} {arguments or ''}")
                    remove(file_name)
                    print(f"{self.name} installed")
                else:
                    print(f"Already installed: {self.name}")
        except KeyboardInterrupt:
            print("\nExiting...")
            remove(f"{self.path}/{self.name}-{platform}")
            exit()


try:
    exec(
        open(f"{cwd}/build_config.py").read(),
        globals(),
    )
except:
    targets = []
    cargo_command = "cargo build"
    rustup = True
    clean_build = False
    dry_run = False

if rustup:
    Install("rustup").add_alias("rustup").add_link(
        "https://win.rustup.rs/x86_64", "exe", Platform.Windows, "rustup-init.exe", "-y"
    ).add_link("https://sh.rustup.rs", "sh", Platform.Posix, arguments="-y").build()

    installed_targets = (
        run(["rustup", "target", "list", "--installed"], capture_output=True)
        .stdout.decode("utf-8")
        .splitlines()
    )

    host_target = (
        run(["rustup", "show"], capture_output=True)
        .stdout.decode("utf-8")
        .splitlines()[0]
        .split(":")[1]
    )

    for target in targets:
        if target not in installed_targets:
            print(f"Installing: {target}")
            system(f"rustup target add {target}")
        print(f"{target} installed.")

    host_arch, host_device, host_platform, host_compiler, *_ = (
        host_target.split("-") + [None] * 4
    )
    for target in targets:
        arch, device, platform, compiler, *_ = target.split("-") + [None] * 4
        target = target.replace("-", "_")
        if arch == "wasm32" and platform == "emscripten":
            Install("emscripten").add_alias("emcc").add_link(
                "https://storage.googleapis.com/webassembly/emscripten-releases-builds/linux/e5523d57a0e0dcf80f3b101bbc23613fcc3101aa/wasm-binaries.tar.xz",
                "xztar",
                Platform.All,
            ).build()
            Install("nodejs").add_link(
                "https://nodejs.org/dist/v20.11.0/node-v20.11.0-win-x64.zip",
                "zip",
                Platform.Windows,
                subdir="node",
            ).add_link(
                "https://nodejs.org/dist/v20.11.0/node-v20.11.0-darwin-x64.tar.gz",
                "gztar",
                Platform.Darwin,
                subdir="node",
            ).add_link(
                "https://nodejs.org/dist/v20.11.0/node-v20.11.0-linux-x64.tar.xz",
                "xztar",
                Platform.Linux,
                subdir="node",
            ).build()
            environ["PATH"] += (
                path_sep + f"{cwd}/nodejs-{Platform.current()}-folder/node/"
            )
            environ["PATH"] += path_sep + (
                f"{cwd}/emscripten-Platform.All-folder/emscripten/"
            )
            environ["PATH"] += path_sep + (f"{cwd}/emscripten-Platform.All-folder/bin/")
        elif arch == "wasm32" and device == "wasi":
            Install("wasi-sdk").add_link(
                "https://github.com/WebAssembly/wasi-sdk/releases/download/wasi-sdk-21/wasi-sdk-21.0.m-mingw.tar.gz",
                "gztar",
                Platform.Windows,
            ).add_link(
                "https://github.com/WebAssembly/wasi-sdk/releases/download/wasi-sdk-21/wasi-sdk-21.0-linux.tar.gz",
                "gztar",
                Platform.Linux,
            ).add_link(
                "https://github.com/WebAssembly/wasi-sdk/releases/download/wasi-sdk-21/wasi-sdk-21.0-macos.tar.gz",
                "gztar",
                Platform.Darwin,
            ).build()
            environ[f"CARGO_TARGET_{target.upper()}_LINKER"] = (
                f"{cwd}/wasi-sdk-{Platform.current()}-folder/bin/clang"
                + (".exe" if Platform.current() == Platform.Windows else "")
            )
            environ[f"CC_{target}"] = (
                f"{cwd}/wasi-sdk-{Platform.current()}-folder/bin/clang"
                + (".exe" if Platform.current() == Platform.Windows else "")
            )
        elif compiler == "gnu" and host_platform == "windows":
            Install("gcc").add_alias("cc").add_link(
                "https://github.com/brechtsanders/winlibs_mingw/releases/download/13.2.0posix-17.0.6-11.0.1-ucrt-r5/winlibs-x86_64-posix-seh-gcc-13.2.0-llvm-17.0.6-mingw-w64ucrt-11.0.1-r5.zip",
                "zip",
                Platform.Windows,
            ).build()
            environ[f"AR_{target}"] = f"{cwd}/gcc-Platform.Windows-folder/bin/ar.exe"
            environ[f"CC_{target}"] = f"{cwd}/gcc-Platform.Windows-folder/bin/gcc.exe"
            environ[f"CARGO_TARGET_{target.upper()}_LINKER"] = (
                f"{cwd}/gcc-Platform.Windows-folder/bin/gcc.exe"
            )

if not dry_run:
    if path.exists(f"{getcwd()}/Cargo.toml"):
        if clean_build:
            system(f"cargo clean --manifest-path={getcwd()}/Cargo.toml")
        target_str = "--target=" + (" --target=".join(targets))
        system(f"{cargo_command} --manifest-path={getcwd()}/Cargo.toml {target_str}")
    else:
        for local_path in listdir(getcwd()):
            full_path = f"{getcwd()}/{local_path}"
            if path.isdir(f"{full_path}"):
                if path.exists(f"{full_path}/Cargo.toml"):
                    if clean_build:
                        system(f"cargo clean --manifest-path={full_path}/Cargo.toml")
                    target_str = (
                        ("--target=" + (" --target=".join(targets)))
                        if targets != []
                        else ""
                    )
                    print(target_str)
                    system(
                        f"{cargo_command} --manifest-path={full_path}/Cargo.toml {target_str}"
                    )
