# [0.4.0-develop.3](https://github.com/jStrider/grafana-publisher/compare/v0.4.0-develop.2...v0.4.0-develop.3) (2025-08-22)


### Bug Fixes

* ensure VERSION file compatibility with PEP 440 ([54a0036](https://github.com/jStrider/grafana-publisher/commit/54a003657862b4070a4f4f5bff143815213a85bf))

# [0.4.0-develop.2](https://github.com/jStrider/grafana-publisher/compare/v0.4.0-develop.1...v0.4.0-develop.2) (2025-08-22)


### Bug Fixes

* add missing dependencies and improve version detection ([c30e852](https://github.com/jStrider/grafana-publisher/commit/c30e85254fe4186bfcc9a11d708022de5379e2f6))

# [0.4.0-develop.1](https://github.com/jStrider/grafana-publisher/compare/v0.3.0...v0.4.0-develop.1) (2025-08-22)


### Bug Fixes

* improve auto-upgrade for development installations ([1e42324](https://github.com/jStrider/grafana-publisher/commit/1e42324f2d144e99f2eea83d63aebfc35cddd243))


### Features

* add intelligent auto-upgrade system ([3113c74](https://github.com/jStrider/grafana-publisher/commit/3113c741218f1f50bbe669ddc02a00386e2eb66c))
* add uv package manager support ([d6ae812](https://github.com/jStrider/grafana-publisher/commit/d6ae812155b36c74a346e01fc2b91cd8695e2b0c))

# [0.3.1](https://github.com/jStrider/grafana-publisher/compare/v0.3.0...v0.3.1) (2025-08-22)


### Features

* add uv package manager support ([d6ae812](https://github.com/jStrider/grafana-publisher/commit/d6ae812))
  - Add uv detection and installation option in install.sh
  - Prioritize uv as recommended package manager when available
  - Add uv support in auto-upgrade functionality
  - Update README with uv installation instructions
  - Fix VERSION file format for PEP 440 compatibility

# [0.3.0](https://github.com/jStrider/grafana-publisher/compare/v0.2.2...v0.3.0) (2025-08-22)


### Bug Fixes

* clone main branch in install script ([bf3401c](https://github.com/jStrider/grafana-publisher/commit/bf3401c396115c1be50bde9280ce266f93d18e58))


### Features

* improve install.sh with intelligent branch detection ([380017c](https://github.com/jStrider/grafana-publisher/commit/380017c13d3286b23100b7e0257e686e8b30d08e))

## [0.2.2](https://github.com/jStrider/grafana-publisher/compare/v0.2.1...v0.2.2) (2025-08-22)


### Bug Fixes

* remove trailing newline from VERSION file ([2c75bb3](https://github.com/jStrider/grafana-publisher/commit/2c75bb3fd1a58050fd449757cd290372b45f3eed))

## [0.2.1](https://github.com/jStrider/grafana-publisher/compare/v0.2.0...v0.2.1) (2025-08-22)


### Bug Fixes

* resolve CI/CD pipeline issues ([691e538](https://github.com/jStrider/grafana-publisher/commit/691e538328ff64642d4e855806b36ed9505c0f17))

# [0.2.0](https://github.com/jStrider/grafana-publisher/compare/v0.1.0...v0.2.0) (2025-08-22)


### Bug Fixes

* add ruff import order fix for app.py ([1036e81](https://github.com/jStrider/grafana-publisher/commit/1036e812f893419b4f0e3c59cc98e2c0c3c06bd3))
* **ci:** correct test command and update Python versions ([4c87779](https://github.com/jStrider/grafana-publisher/commit/4c87779c98f1c388bd3bb69a91fcc3e652bb9e05))
* **ci:** implement semantic release dry run for develop branch ([fa60e31](https://github.com/jStrider/grafana-publisher/commit/fa60e31e965e4b907e93bb95bceec4a009b14a1f))
* correct all ruff violations ([d829e38](https://github.com/jStrider/grafana-publisher/commit/d829e38c39f670b6c86f19b1e93f02cc859fc8de))
* correct import issues in web module ([19d16e6](https://github.com/jStrider/grafana-publisher/commit/19d16e6b3c3d47d78b3e5c1733797fb4eb0e44f0))
* correct linting issues in flask_base.py ([be1e60b](https://github.com/jStrider/grafana-publisher/commit/be1e60bccd6e456dd956bc0ff5f27fc039e64eb9))
* enhance test suite ([f768f67](https://github.com/jStrider/grafana-publisher/commit/f768f6754f1e0e1f09c08ce00d4e4c8ba3177f23))
* fix type hint issues ([e39bbce](https://github.com/jStrider/grafana-publisher/commit/e39bbce2f05e1f592f4c43fb99ec3e977ee6f907))
* remove setup.py and use only pyproject.toml ([7e26f0f](https://github.com/jStrider/grafana-publisher/commit/7e26f0ff65ea6d5c859f39c2b5fb3a6fb6c2e3d5))
* replace deprecated typing imports ([ce8cf2f](https://github.com/jStrider/grafana-publisher/commit/ce8cf2fbdbfe57c15c4bb666fb44e83e00c4e9f9))
* resolve all ruff errors ([cad2e0f](https://github.com/jStrider/grafana-publisher/commit/cad2e0f3c2c9f8dcf948e08f8c3c1e30c7797bd7))
* resolve type issues ([f19c7ce](https://github.com/jStrider/grafana-publisher/commit/f19c7cea9f2ee59f079bbba837c27d4e8f956a9e))
* tests import fix ([dcb4a96](https://github.com/jStrider/grafana-publisher/commit/dcb4a9692fc7c8a948e57adb87de8e19b96ee3e7))
* **tests:** update mock paths for API tests ([5f5f1e2](https://github.com/jStrider/grafana-publisher/commit/5f5f1e2e860e86c9acf6c087bb2d99e996b88990))
* update all test imports to src paths ([c03fb02](https://github.com/jStrider/grafana-publisher/commit/c03fb02dc2e37fb587e0c3333f03db3f088833ff))
* update semantic-release config ([5701c74](https://github.com/jStrider/grafana-publisher/commit/5701c747c75e23fa8f68f1bc858c34f2a652be83))


### Features

* add automated release workflow ([d88e9f2](https://github.com/jStrider/grafana-publisher/commit/d88e9f26e008b018c826e96d9b4e7e36f35f0f9d))
* **automation:** introduce release automation and update config ([31bf72e](https://github.com/jStrider/grafana-publisher/commit/31bf72ee0b949f15e8cbd96f2bc07e8e8c8e9abd))
* **ci:** add comprehensive CI/CD pipeline with semantic release ([c8f4a95](https://github.com/jStrider/grafana-publisher/commit/c8f4a95dc20fa2e31f656e41bb35c890c8dddc59))
* publish workflow fix ([80f7c18](https://github.com/jStrider/grafana-publisher/commit/80f7c185a89ce4dd07f4f5e70ad42b59ad0f0e10))
* **refactor:** implement src layout and comprehensive project restructure ([3ed96f4](https://github.com/jStrider/grafana-publisher/commit/3ed96f4f3e0a1cc5f8e3e4aca955c91a45e00abd))
* **release:** implement semantic-release configuration ([c0b08d8](https://github.com/jStrider/grafana-publisher/commit/c0b08d80e977a5f859a43b04e88c96e2fa7bed2b))
* **tests:** add comprehensive test suite with 95% coverage target ([b7b1797](https://github.com/jStrider/grafana-publisher/commit/b7b1797a0ac9ad3ad38b955c7fb9b7e72fdb20a7))

# [0.1.0](https://github.com/jStrider/grafana-publisher/compare/2fa7fc89f33e088ce5fa4bc326f063c9b17c2f4f...v0.1.0) (2025-08-22)


### Bug Fixes

* **config:** add default values for jira fields ([0f38093](https://github.com/jStrider/grafana-publisher/commit/0f38093fa7b5177bfea00b87a019f0de0bd55f0f))


### Features

* **clickup:** implement clickup publisher ([67ee35e](https://github.com/jStrider/grafana-publisher/commit/67ee35e582e088a90c69b079b7b44e2c0a1fbe81))
* **config:** add comprehensive configuration system ([fcdda4e](https://github.com/jStrider/grafana-publisher/commit/fcdda4e3bc8fac5a1c96f4d993c088e383b93f5a))
* **grafana:** implement grafana scraper with multi-source support ([b0e4e8e](https://github.com/jStrider/grafana-publisher/commit/b0e4e8ebbf82b2e49f0bc75a2f018c1e3dddc04c))
* initial project structure ([2fa7fc8](https://github.com/jStrider/grafana-publisher/commit/2fa7fc89f33e088ce5fa4bc326f063c9b17c2f4f))
* **jira:** add Jira publisher implementation ([1e9a0e0](https://github.com/jStrider/grafana-publisher/commit/1e9a0e03b4c982c656a66f6a2e837b93e1b5cb3b))
* **main:** implement CLI with rich interface ([d8ca37b](https://github.com/jStrider/grafana-publisher/commit/d8ca37b956063dd017b79c9f5f757c20e2872b9e))
* **processors:** add smart alert processing and field mapping ([7b40e09](https://github.com/jStrider/grafana-publisher/commit/7b40e09a87fb825b83f2d5b88797e5b30cf973e9))
* **publishers:** define base publisher interface ([8e7f8e9](https://github.com/jStrider/grafana-publisher/commit/8e7f8e968e0ca48b7f05b8bc23bc37e01e97c074))
* **scrapers:** define base scraper interface ([4f6c73e](https://github.com/jStrider/grafana-publisher/commit/4f6c73e19e1df8c08ad6b2ac7fb02f1bc2bc5277))
