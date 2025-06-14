# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
[markdownlint](https://dlaa.me/markdownlint/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.6.7] - 2023-06-07

### Added in 1.6.7

- Improved detection of license file or string and use in container(s)
- Warning message if SENZING_ENGINE_CONFIGURATION_JSON is set

## [1.6.6] - 2023-02-06

### Changed in 1.6.6

- Modify configparser to not interpolate percent encoded config values

## [1.6.5] - 2023-01-10

### Changed in 1.6.5

- Fixed case sensitive bug

## [1.6.4] - 2022-12-02

### Changed in 1.6.4

- Improve conversion of INI config file to JSON

## [1.6.3] - 2022-10-31

### Changed in 1.6.3

- Fix an issue parsing CLI arguments on Python version < 3.8

## [1.6.2] - 2022-09-13

### Changed in 1.6.2

- Add timeout to update check to prevent premature warning

## [1.6.1] - 2022-09-08

### Changed in 1.6.1

- Fixed bug in --saveImages

## [1.6.0] - 2022-09-07

### Changed in 1.6.0

- Substantial performance improvements
- Checks if a new version is available
- Can self update if newer version is available
- New output formatting
- New flag to be stricter on checking health of containers, to use if issues arise (--waitHealth)
- New arg to specify the Docker URL (--dockUrl)

## [1.5.2] - 2022-07-20

### Changed in 1.5.2

- Fix bug with saving images to a package
- Add detection of running in AWS and report public facing host & IP address
- Add IP address to resources output

## [1.5.1] - 2021-05-12

### Changed in 1.5.1

- Remove temporary use of transitional Docker assets URL used during Senzing V2 -> V3
- Modified technique to collect the user ID running as to improve compatibility with WSL2

## [1.5.0] - 2022-05-04

### Added to 1.5.0

- Support SenzingAPI 3.0.0

## [1.4.0] - 2021-12-06

### Changed in 1.4.0

- Initial release
