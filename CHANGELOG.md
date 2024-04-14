# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/).<br/>
This project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

<!-- insertion marker -->

## [v3.2.0](https://github.com/bswck/runtime_generics/tree/v3.2.0) (2024-04-14)


### Fixed

- Relaxed support Python version range to >=3.8.


## [v3.1.0](https://github.com/bswck/runtime_generics/tree/v3.1.0) (2024-03-16)


### Added

- Exposed `get_alias()` to retrieve the alias form used in runtime generic instance construction.
- Implemented `get_mro()` function for resolving MROs of runtime generics.
- Implemented `type_check()` for checking whether a runtime generic is a valid subtype of another runtime generic.


## [v3.0.5](https://github.com/bswck/runtime_generics/tree/v3.0.5) (2024-02-24)


### Added

- Wide support for resolving parametrized parents of runtime generic classes as well as instances of them.


## [v3.0.4](https://github.com/bswck/runtime_generics/tree/v3.0.4) (2024-02-22)


### Fixed

- Updated documentation that contained obsolete information.


## [v3.0.3](https://github.com/bswck/runtime_generics/tree/v3.0.3) (2024-02-22)


### Changed

- Constructing parametrized generics now also sets `__origin__` on the instance (so far, only `__args__` was set).


## [v3.0.2](https://github.com/bswck/runtime_generics/tree/v3.0.2) (2024-02-22)


No significant changes.


## [v3.0.1](https://github.com/bswck/runtime_generics/tree/v3.0.1) (2024-02-20)


No significant changes.


## [v3.0.0](https://github.com/bswck/runtime_generics/tree/v3.0.0) (2024-02-20)

### Removed
-  `generic_issubclass()` and `generic_isinstance()`.

### Added

- `get_parents()` for resolving parametrized parents, `runtime_generic_proxy()` and `runtime_generic_patch()` for subclassing e.g. `typing.List` as a runtime generic.

