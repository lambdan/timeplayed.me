.PHONY: check-version

check-version:
	@if [ -z "$(TAG)" ]; then \
		echo "Error: TAG variable is not set"; \
		exit 1; \
	fi
	@TAG_VALUE="$(TAG)"; \
	BACKEND_VERSION_FILE=./backend/tpbackend/__version__.py; \
	case "$$TAG_VALUE" in \
		backend@*) \
			if [ ! -f "$$BACKEND_VERSION_FILE" ]; then \
				echo "Error: backend version file '$$BACKEND_VERSION_FILE' not found for tag '$$TAG_VALUE'"; \
				exit 1; \
			fi; \
			PACKAGE_VERSION=$$(python3 -c 'import pathlib,re,sys; content = pathlib.Path(sys.argv[1]).read_text(); match = re.search(r"^__version__ = \"([^\"]+)\"$$", content, re.M); print(match.group(1) if match else ""); sys.exit(0 if match else 1)' "$$BACKEND_VERSION_FILE") || { \
				echo "Error: could not parse backend version from $$BACKEND_VERSION_FILE"; \
				exit 1; \
			}; \
			TAG_VERSION=$${TAG_VALUE#backend@}; \
			VERSION_SOURCE=$$BACKEND_VERSION_FILE; \
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
