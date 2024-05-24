# Unless explicitly stated otherwise all files in this repository are licensed under the the Apache License Version 2.0.
# This product includes software developed at Datadog (https://www.datadoghq.com/).
# Copyright 2021 Datadog, Inc.

from collections import defaultdict
import re
import semantic_version as version_module


def _build(version, component):
    if isinstance(version, str):
        return Version(version, component)

    if isinstance(version, Version):
        return version

    raise TypeError(version)


class Version(version_module.Version):

    version_re = re.compile(r"^(\d+)\.(\d+)\.(\d+)(?:[-\.]?([0-9a-zA-Z.-]+))?(?:[\+ ]([0-9a-zA-Z.-]+))?$")

    def __init__(self, version, component):

        self._component = component

        version = version.strip()

        if component == "ruby":
            if version.startswith("* ddtrace"):
                version = re.sub(r"\* *ddtrace *\((.*)\)", r"\1", version)
            if version.startswith("* datadog"):
                version = re.sub(r"\* *datadog *\((.*)\)", r"\1", version)

        elif component == "libddwaf":
            if version.startswith("* libddwaf"):
                version = re.sub(r"\* *libddwaf *\((.*)\)", r"\1", version)

        elif component == "agent":
            version = re.sub(r"(.*) - Commit.*", r"\1", version)
            version = re.sub(r"(.*) - Meta.*", r"\1", version)
            version = re.sub(r"Agent (.*)", r"\1", version)
            version = re.sub("\x1b\\[\\d+m", "", version)  # remove color pattern from terminal
            version = re.sub(r"[a-zA-Z\-]*$", "", version)  # remove any lable post version

        elif component == "java":
            version = version.split("~")[0]
            version = version.replace("-SNAPSHOT", "")

        elif component == "dotnet":
            version = re.sub(r"(datadog-dotnet-apm-)?(.*?)(\.tar\.gz)?", r"\2", version)

        elif component == "php":
            version = version.replace("-nightly", "")

        if version.startswith("v"):
            version = version[1:]
            
        if re.match(r"^\d+\.\d+$", version):
            version = f"{version}.0"

        super().__init__(version)

    def __eq__(self, other):
        return super().__eq__(_build(other, self._component))

    def __lt__(self, other):
        return super().__lt__(_build(other, self._component))

    def __le__(self, other):
        return super().__le__(_build(other, self._component))

    def __gt__(self, other):
        return super().__gt__(_build(other, self._component))

    def __ge__(self, other):
        return super().__ge__(_build(other, self._component))


class LibraryVersion:
    known_versions = defaultdict(set)

    def add_known_version(self, version, library=None):
        library = self.library if library is None else library
        LibraryVersion.known_versions[library].add(str(version))

    def __init__(self, library, version=None):
        self.library = None
        self.version = None

        if library is None:
            return

        if "@" in library:
            raise ValueError("Library can't contains '@'")

        self.library = library
        self.version = Version(version, component=library) if version else None
        self.add_known_version(self.version)

    def __repr__(self):
        return f'{self.__class__.__name__}("{self.library}", "{self.version}")'

    def __str__(self):
        if not self.library:
            return str(None)

        return f"{self.library}@{self.version}" if self.version else self.library

    def __eq__(self, other):
        if not isinstance(other, str):
            raise TypeError(f"Can't compare LibraryVersion to type {type(other)}")

        if "@" in other:

            library, version = other.split("@", 1)
            self.add_known_version(library=library, version=version)

            if self.library != library:
                return False

            if self.version is None:
                raise ValueError("Weblog does not provide an library version number")

            return self.library == library and self.version == version

        library = other
        return self.library == library

    def _extract_members(self, other):
        if not isinstance(other, str):
            raise TypeError(f"Can't compare LibraryVersion to type {type(other)}")

        if "@" not in other:
            raise ValueError("Can't compare version numbers without a version")

        library, version = other.split("@", 1)

        if self.version is None and self.library == library:
            # the second comparizon is here because if it's not the good library,
            # the result will be always false, and nothing will be compared
            # on version. This use case ccan happens if a version is not provided
            # on other weblogs
            raise ValueError("Weblog does not provide an library version number")

        self.add_known_version(library=library, version=version)
        return library, version

    def __lt__(self, other):
        library, version = self._extract_members(other)
        return self.library == library and self.version < version

    def __le__(self, other):
        library, version = self._extract_members(other)
        return self.library == library and self.version <= version

    def __gt__(self, other):
        library, version = self._extract_members(other)
        return self.library == library and self.version > version

    def __ge__(self, other):
        library, version = self._extract_members(other)
        return self.library == library and self.version >= version

    def serialize(self):
        return {
            "library": self.library,
            "version": str(self.version),
        }
