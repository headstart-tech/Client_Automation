# 🚀 Release PR

## 📦 Release Version - **1.0.0**

### 🎉 Covered Epics

<!-- List all the Epics included in this release. Make sure to link each epic for easy navigation. -->

Fixes (GTCRM-)

### 📝 Release Notes

<!-- Provide a brief, bullet-point summary of the changes included in this release. Each bullet point should be a complete sentence. -->

## 📋 Checklist:

- [x] Code builds cleanly without any errors or warnings
- [x] Linting has been properly executed (🔧 `flake8 .` or equivalent command)
- [ ] This release includes potentially breaking changes (Note them under "Breaking Changes")
- [ ] This change requires updates to the documentation
- [ ] Documentation updates have been made

### 🧪 Unit Test Coverage

<!-- 
Were unit test cases updated or recorded for this release? 
Was only manual testing applicable?
Mention the test cases written for this release.
-->

- [x] Test cases have been added or updated

### 🔄 Type of Change

Please tick the box that is relevant to this PR:

- [ ] Bug fix (non-breaking change which fixes an issue)
- [x] New feature
- [ ] Improvement
- [ ] Breaking change (fix or feature that would cause existing functionality not to work as expected)

### 🐛 How Has This Been Tested?

Before submitting, run these commands for testing:

- `pytest`
- `coverage run --source=. -m pytest`
- `coverage report -m`

- [ ] New and existing unit tests pass locally with my changes
- [ ] Coverage Report is included

#### Coverage Report

```shell
# Paste your coverage report here
```

<!-- Paste your coverage report here -->

💥 Breaking Changes
<!-- If there are any breaking changes, list them here. -->