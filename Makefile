.PHONY: check-version

check-version:
	@if [ -z "$(TAG)" ]; then \
		echo "Error: TAG variable is not set"; \
		exit 1; \
	fi
	@PACKAGE_VERSION=$$(node -p "require('./frontend/package.json').version"); \
	TAG_VERSION=$$(echo "$(TAG)" | sed 's/^v//'); \
	if [ "$$PACKAGE_VERSION" != "$$TAG_VERSION" ]; then \
		echo "Version mismatch: frontend/package.json has '$$PACKAGE_VERSION' but release tag is '$(TAG)'"; \
		exit 1; \
	fi; \
	echo "Version check passed: '$$PACKAGE_VERSION' matches tag '$(TAG)'"

release:
	./make-release.sh
