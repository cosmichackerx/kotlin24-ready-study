# kotlin24-ready-study

Harness and results for the recall / precision study of [kotlin24-ready](https://github.com/cosmichackerx/kotlin24-ready)
(roadmap issue [#5](https://github.com/cosmichackerx/kotlin24-ready/issues/5)). Results are added below once the workflow has run.

## Method

1. Candidates: public GitHub repositories with the topic `kotlin-multiplatform` or `compose-multiplatform`, written in Kotlin, pushed after 2025-06-01, at least 150 stars,
   at most ~300 MB; the 84 that could be shallow-cloned on 2026-10-03.
2. The scanner runs on all 84 (`scan_results` in the report).
3. Gradle truth is measured on the subset that has a Gradle wrapper, a settings file and a detected Kotlin Gradle plugin version older than 2.4 (or none detected): 32 repositories (`repos.json`).
   For each, `./gradlew help` runs **before** (project as is) and **after** (Kotlin plugin version raised to 2.4.20 by `scripts/sub.py`) on a GitHub-hosted runner.
4. A project counts only when *before* succeeds. For *after* failures the first error is classified by hand as caused by a Kotlin 2.4 removal, or by something else
   (Gradle / AGP / JDK / network), and compared with the scanner's findings.

Limits that apply to every number: `help` evaluates build scripts only (it does not compile Kotlin sources, so source-language changes and the language-version rule are not exercised by it); version substitution
is textual and may miss projects that pin Kotlin elsewhere; failures from unrelated causes are not "recall" misses; the sample is small and is not random (popular, recently pushed repositories).
