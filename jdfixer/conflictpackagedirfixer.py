# -*- coding: utf-8 -*-

import os
import shutil
from os import PathLike
from pathlib import Path
from .dirfixer import DirFixer


class ConflictPackageDirFixer(DirFixer):
    def dir_to_package(self, adir: PathLike, base_dir: PathLike):
        return (
            str(Path(os.fspath(adir)).relative_to(os.fspath(base_dir)))
            .replace("/", ".")
            .replace("\\", ".")
        )

    def package_to_dir(self, package, base_dir: PathLike):
        return Path(base_dir, package.replace(".", os.sep))

    def alter_package_name(self, package, base_dir: PathLike):
        base_dir = Path(os.fspath(base_dir))
        parts = package.split(".")
        new_parts = []
        for i in range(1, len(parts) + 1):
            apath = Path(base_dir, *parts[:i])
            same_name_module_path = Path(apath.parent, apath.name + ".java")
            if same_name_module_path.exists():
                new_parts.append("P" + apath.name)
            else:
                new_parts.append(apath.name)

        return ".".join(new_parts)

    def find_packages_needs_to_be_fix(self, base_dir: PathLike):
        packages = []
        for root, dirs, files in os.walk(os.fspath(base_dir)):
            for dirname in dirs:
                adir = Path(root, dirname)
                same_name_module_path = Path(root, dirname + ".java")
                if not same_name_module_path.exists():
                    continue

                # The same java file name as base directory
                packages.append(self.dir_to_package(adir, base_dir))

        return packages

    def gen_mappings(self, packages):
        package_mappings = dict()
        module_mappings = dict()

        # Generate for correct package mappings
        for package in packages:
            package_mappings[package] = self.alter_package_name(
                package, self._target_dir
            )

            # Put the tree dirs of current pcakges into package_mappings
            base_dir = self.package_to_dir(package, self._target_dir)
            for root, dirs, files in os.walk(os.fspath(base_dir)):

                for dirname in dirs:
                    adir = Path(root, dirname)
                    # NOTICE: Overrided the iterator variable 'package'
                    package = self.dir_to_package(adir, self._target_dir)

                    package_mappings[package] = self.alter_package_name(
                        package, self._target_dir
                    )

                # Generate module mappings
                # NOTICE: Overrided the iterator variable 'package'
                package = self.dir_to_package(root, self._target_dir)
                for filename in files:
                    afile = Path(root, filename)

                    if fnmatch(str(afile), "*.java"):
                        suffix = "." + afile.stem

                    module_mappings[package + suffix] = (
                        package_mappings[package] + suffix
                    )
        return (package_mappings, module_mappings)

    def fix_file_contents(self, package_mappings, module_mappings):
        base_dir = Path(self._target_dir)
        for root, dirs, files in os.walk(os.fspath(base_dir)):
            for filename in files:
                apath = Path(root, filename)
                if not fnmatch(filename, "*.java"):
                    continue

                # Read and fix that file
                with open(apath, "r") as f:
                    content = f.read()
                orig_content = content

                # Fix package names
                for k, v in package_mappings.items():
                    content = content.replace(
                        "package %s;" % k, "package %s;" % v
                    )

                # Fix imports
                keys = list(module_mappings.keys())
                keys.sort(key=lambda v: len(v.split(".")), reverse=True)
                for k in keys:
                    v = module_mappings[k]
                    content = content.replace("%s" % k, "%s" % v)

                if orig_content == content:
                    continue

                with open(apath, "w", encoding="utf-8") as f:
                    f.write(content)

    def fix(self, aDir: PathLike):
        self._target_dir = aDir

        packages = self.find_packages_needs_to_be_fix(self._target_dir)
        package_mappings, module_mappings = self.gen_mappings(packages)

        packages.sort(key=lambda v: len(v.split(".")), reverse=True)
        for old_package in packages:
            prefix = old_package.split(".")[:-1]
            suffix = package_mappings[old_package].split(".")[-1]
            new_package = ".".join(prefix + [suffix])

            shutil.move(
                self.package_to_dir(old_package, self._target_dir),
                self.package_to_dir(new_package, self._target_dir),
            )

        self.fix_file_contents(package_mappings, module_mappings)
