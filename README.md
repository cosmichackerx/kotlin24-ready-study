# kotlin24-ready-study

Harness and results for the recall / precision study of [kotlin24-ready](https://github.com/cosmichackerx/kotlin24-ready)
(roadmap issue [#5](https://github.com/cosmichackerx/kotlin24-ready/issues/5)). Results of the run on 2026-10-03 are below.

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

## Results (run 37109947083, 2026-10-03; scanner = kotlin24-ready at 9a22d1d, i.e. v0.1.2 + fix, Kotlin Gradle plugin 2.4.20)

Funnel: 84 repositories cloned and scanned -> 32 with a wrapper, settings file and Kotlin plugin older than 2.4 (or none detected) -> 28 whose *before* run succeeded
(4 excluded: Napier [JVM target 21 vs JDK], material-motion-compose [JVM target mismatch], moko-resources [needs `xcrun`, macOS], spmp [buildSrc resolution]) -> 25 where a Kotlin version
could be substituted (3 had none to substitute: Kodein, AboutLibraries, markdown-renderer).
Of the 25: **17 build with Kotlin 2.4.20 (`./gradlew help`), 8 fail.** Per-repository data: `results/` (copied from the workflow artifacts) and the run's artifacts.

| Failing repository | First error on 2.4.20 | Cause | Scanner at the time of the run | After the follow-up rules (0.1.3) |
|---|---|---|---|---|
| Calvin-LL/Reorderable | `Using 'KOTLIN_1_9' is an error. Unsupported` | Kotlin 2.4 removal | caught (`language-version-1-9`) | caught |
| bumble-tech/appyx | `KOTLIN_1_9` unsupported, then `kotlinOptions(...) is an error` | Kotlin 2.4 removal | caught (language version; the `kotlinOptions` error was **not** reported) | both caught |
| kizitonwose/Calendar | `AbiValidationMultiplatformExtension` / `AbiValidationVariantSpec` removed, `enabled` removed | Kotlin 2.4 removal | **missed** (only the `js(IR)` warning) | caught (`abi-validation-legacy` extended) |
| arkivanov/Decompose | `'kotlin-js' Gradle plugin is deprecated` (applying `org.jetbrains.kotlin.js` fails) | Kotlin 2.4 removal | **missed** | caught (new rule `kotlin-js-plugin`) |
| touchlab/DroidconKotlin | `SKIE 0.10.10 does not support Kotlin 2.4.20` | third-party plugin | outside scope | outside scope |
| touchlab/KaMPKit | `SKIE 0.10.14 does not support Kotlin 2.4.20` | third-party plugin | outside scope | outside scope |
| MohamedRejeb/Pokedex | AGP 8.1.3 is lower than the minimum 8.5.2 for this Kotlin plugin | AGP version | outside scope | caught by the new `agp-minimum` rule (v0.1.4; in-sample) |
| Tencent-TDS/KuiklyUI | AGP 7.4.2 is lower than the minimum 8.5.2 | AGP version | outside scope | caught by the new `agp-minimum` rule (v0.1.4; in-sample) |

What can honestly be said (small sample, in-sample for the follow-up rules):

* Kotlin-caused failures: 4 of 8. The scanner caught **2 of 4 repositories** at the time of the run (50 %). The two misses were turned into rules afterwards, each with an oracle case that fails on a real 2.4.20 plugin;
  after that it covers 4 of 4, **but that number is in-sample**: the rules were written after seeing those failures. It says the rules are not wrong, not that recall is 100 %.
* The scanner did not model the other 4 failures at the time (2 SKIE, 2 AGP minimum). Counting them, repository-level recall of "will `help` fail on 2.4.20" was 2/8 at the time of the run; after v0.1.3 and v0.1.4 it is 6/8 (in-sample), the two SKIE failures (third-party plugin support lists) remain out of scope.
* Precision: of the 25 repositories, those with an *error* finding at the time of the run were Reorderable and appyx, and both failed (0 false positives in 25). With the 0.1.3 rules, 8 repositories have error findings:
  4 confirmed by a failing build (above); Pokedex and KuiklyUI have `kotlinOptions` findings but their first failure is the AGP version, so the finding is neither confirmed nor refuted;
  realm-kotlin (a benchmarks build that `help` does not evaluate) and Stable-Diffusion-KMP (a `build-logic` included build; the textual substitution may not have reached its plugin pin) pass.
  So the worst-case precision of the 0.1.3 error findings in this sample is 4/8, and 4/6 if the two unconfirmed ones are ignored. Calf (already on 2.4.20, not in the 32) has `androidTarget { compilations.all { kotlinOptions } }`;
  the oracle verifies the JVM form only, so the Android-compilation form is unverified.
* Warning rules: `js-compiler-type` fired in 16 of the 84 repositories (82 findings) and no build failed because of it, which matches "documentation only".
* `kotlin-android-sourcesets` produced 79 false positives in the first scan (KMP modules behind convention-plugin aliases). That was fixed in v0.1.2; there is no positive example in the sample.
* Not exercised: `help` does not compile sources, so `compileKotlin` failures are not measured; the Compose rule (one hit, material-motion-compose, whose baseline fails), `dependency-handler-platform`, `target-hierarchy`, `compilation-task-accessors` and `hierarchy-builder-removed` had no real-world hit at all.
* 25 repositories, not random (popular, recently pushed, topic-tagged), one Gradle task, textual version substitution: treat every number as an anecdote, not as an estimate.

v0.1.4 `agp-minimum` also flags AGP < 8.5.2 in: Napier and material-motion-compose (their baseline fails, not evaluable), and nested sample/demo builds of realm-kotlin, moko-resources and supabase-kt (reported as warnings since they have their own settings files).
