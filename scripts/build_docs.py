#!/usr/bin/python

"""
build-docs.py

Version:        18 June 2025

Purpose:        Build the OSS Druid Docusaurus 3 docs for all
                versions supplied in the [-v, --versions] flag.
                Versions aside from "latest" only retain content
                from the docs folder. The "latest" version keeps
                everything. Assumes script is called from
                `druid-website-src/static/build-scripts` directory.

Help:           python build-docs.py --help

Example call:   python build-docs.py -v latest 26.0.0
"""

import fileinput
import os
import re
import shutil
import subprocess
import sys

def build_docs(versions, use_yarn):

    # define the folders that Docusaurus builds into and a temporary one
    build_dir = "build"
    temp_dir = "build__temp"

    for v in versions:
        print(f"Building the docs for version '{v}'...")

        # replace "latest" in redirects to the appropriate version
        if v != "latest":
            for line in fileinput.input("redirects.js", inplace=1):
                print(line.replace("/latest/", f"/{v}/"), end='')

        # set the version in "buildVersion" variable in docusaurus.config.js
        replacement = f'var buildVersion = "{v}";'
        for line in fileinput.input("docusaurus.config.js", inplace=1):
            print(re.sub(r"^var buildVersion.*", replacement, line), end='')

        # build the docs
        if not use_yarn:
            subprocess.run(["npm", "run", "build"])
        else:
            subprocess.run(["yarn", "build"])

        # move output to temporary directory since docusaurus 3
        # overwrites build directory with each build.
        # the "latest" version is built last to maintain
        # all the non-docs content for latest
        if not os.path.isdir(build_dir):
            sys.exit("ERROR: The docs were not built. Check Docusaurus logs.")
        shutil.copytree(build_dir, temp_dir, dirs_exist_ok=True)

        # restore the redirect file back to URLs with "latest"
        if v != "latest":
            for line in fileinput.input("redirects.js", inplace=1):
                print(line.replace(f"/{v}/", "/latest/"), end='')

    # after building ALL versions, rename the temp directory back to "build"
    shutil.rmtree(build_dir)
    shutil.move(temp_dir, build_dir)


def main(versions, skip_install, use_yarn):

    # from druid-website-src/scripts,
    # move to druid-website-src to run the npm commands
    os.chdir("../")

    # sort to build "latest" last
    versions = sorted(versions)

    # install docusaurus 2
    if not skip_install:
        print("Installing Docusaurus...")

        if not use_yarn:
            subprocess.run(["npm", "install"])
        else:
            subprocess.run(["yarn", "install"])

    # remove the old build directory
    shutil.rmtree('build', ignore_errors=True)

    # do the actual builds
    build_docs(versions, use_yarn)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()

    parser.add_argument("-v", "--versions", required=True, nargs='+',
                        help="One or more versions to build. "
                        "For example: -v latest 26.0.0")

    parser.add_argument("--skip-install",
                        help="Skip the Docusaurus 3 installation",
                        action='store_true')

    parser.add_argument("--yarn", default=False,
                        help="Use yarn to install and build instead of npm",
                        action='store_true')

    args = parser.parse_args()

    main(args.versions, args.skip_install, args.yarn)
