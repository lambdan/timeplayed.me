.PHONY: check-version

check-version:
	@if [ -z "$(TAG)" ]; then \
		echo "Error: TAG variable is not set"; \
		exit 1; \
	fi
	@TAG_VALUE="$(TAG)"; \
	case "$$TAG_VALUE" in \
		backend@*) \
			if [ ! -f ./backend/tpbackend/__version__.py ]; then \
				echo "Error: backend version file './backend/tpbackend/__version__.py' not found for tag '$$TAG_VALUE'"; \
				exit 1; \
			fi; \
			PACKAGE_VERSION=$$(python3 -c 'import pathlib,re,sys; match = re.search(r"^__version__ = \"([^\"]+)\"$$", pathlib.Path("backend/tpbackend/__version__.py").read_text(), re.M); sys.exit(print(match.group(1)) or 0 if match else 1)') || { \
				echo "Error: could not parse backend version from backend/tpbackend/__version__.py"; \
				exit 1; \
			}; \
			TAG_VERSION=$${TAG_VALUE#backend@}; \
			VERSION_SOURCE=backend/tpbackend/__version__.py; \
			;; \
		frontend@*) \
			PACKAGE_VERSION=$$(node -p "require('./frontend/package.json').version"); \
			TAG_VERSION=$${TAG_VALUE#frontend@}; \
			VERSION_SOURCE=frontend/package.json; \
			;; \
		*) \
			PACKAGE_VERSION=$$(node -p "require('./frontend/package.json').version"); \
			TAG_VERSION=$$(echo "$$TAG_VALUE" | sed 's/^v//'); \
			VERSION_SOURCE=frontend/package.json; \
			;; \
	esac; \
	if [ "$$PACKAGE_VERSION" != "$$TAG_VERSION" ]; then \
		echo "Version mismatch: $$VERSION_SOURCE has '$$PACKAGE_VERSION' but release tag is '$(TAG)'"; \
		exit 1; \
	fi; \
	echo "Version check passed: '$$PACKAGE_VERSION' matches tag '$(TAG)'"

release:
	./make-release.sh
