# Repository Guide for Agents

## Purpose and scope

Document Builder converts Markdown collections into PDF, HTML, Markdown, and
data archives. It also validates source documents, supports
assignment/key/feedback generation, and can upload data archives to Dropbox.
`document-builder.py` is the main implementation; `authorize-dropbox.py` handles
the one-time OAuth flow.

Read `README.md`, `requirements.txt`, `config/config.json`, `test.sh`, and the
relevant sample inputs before modifying behavior. This repository is the
dependency used by
[bioinformatics-tutorials](https://github.com/paulstothard/bioinformatics-tutorials)
and
[bioinformatics-assignments](https://github.com/paulstothard/bioinformatics-assignments).
Keep backward compatibility with their existing projects unless a coordinated
migration is explicitly requested.

## `just` and consuming repositories

The tutorial and assignment repositories use
[just](https://github.com/casey/just) and their root `justfile` files as the
primary interface to Document Builder. When fixing Document Builder for one of
those repositories, first run `just -l` there, understand the recipe that
exposes the behavior, and use that recipe for the final integration check. Do
not leave consumers dependent on an undocumented one-off Python command.

This repository currently uses `test.sh` and `test-dropbox.sh` directly rather
than defining its own `justfile`. Focused direct Python commands and `test.sh`
are therefore appropriate here. If a root `justfile` is added later, keep it as
a thin, documented interface to the supported development tasks and prefer its
recipes once they exist. It is acceptable to update a consuming repository's
`justfile` when a new option or repeatable workflow is part of a coordinated
change; keep the recipe help accurate and verify both repositories.

## Development environment setup

Use a repository-local virtual environment as the reference development setup.
This matches Paul's local workflow, isolates the pinned Dropbox/Python packages,
and lets `test.sh` activate the expected environment automatically. Document
Builder requires Python 3.8 or newer; a current supported Python 3 release is
preferable.

From the repository root:

```bash
python3 -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Install the external programs listed in `README.md` with the operating system's
package manager: Pandoc, `markdown-link-check`, `spellchecker` from
`spellchecker-cli`, and `mdl`. PDF-generating projects also need the PDF engine
named in their configuration, normally `xelatex` from a TeX distribution.
Install `just` when working with the tutorial or assignment consumers.

Verify the local tools and Python entry point:

```bash
command -v pandoc xelatex markdown-link-check spellchecker mdl
venv/bin/python document-builder.py --help
venv/bin/python -m py_compile document-builder.py authorize-dropbox.py
```

Run `./test.sh` for the full local sample-project smoke test after the required
executables are installed. Conda, `uv`, containers, or another environment
manager may be used instead, but maintain the behavior of the reference `venv`
setup and do not commit environments or machine-specific paths.

When a consuming repository invokes a symlinked `document-builder.py`, activate
that repository's environment first so the `#!/usr/bin/env python3` interpreter
resolves to its installed dependencies. Keep the consumer and Document Builder
requirements compatible when dependencies change.

## Project contract

The `create` command produces a project whose source documents are direct
children of its `source/` folder:

```text
<project>/
├── config/config.json
├── build_includes/
├── data_links/
├── source/<document_name>/
│   ├── document.md
│   ├── settings.yaml
│   ├── includes/
│   ├── data/
│   └── data_not_tracked/
└── final_documents/
```

The document folder name is a stable identifier used in output filenames, data
ZIP names, link metadata, logs, and table-of-contents entries. Preserve that
relationship when changing create, import, processing, or publishing code.

- `data/` is intended for ordinary project data tracked by Git.
- `data_not_tracked/` is intended for large local data ignored by consuming
  repositories. Code must tolerate empty folders, but it must not pretend a
  missing required file exists.
- `[DATA_DOWNLOAD_LINK]` is replaced with data-link metadata during processing.
- Paths beginning with `~` are expanded, and project-relative paths are resolved
  through `project_root` in the configuration.
- The script may be invoked through a symlink from a consuming repository.
  Preserve real-path/config-path handling.

## Creating, importing, modifying, and generating content

Create a standalone project with examples:

```bash
venv/bin/python document-builder.py create -p my_project -e
```

Import existing Markdown into a created project:

```bash
venv/bin/python document-builder.py import \
  -c my_project/config/config.json \
  -m markdown_for_import
```

In an existing annual course project, the normal way to start a subsequent-year
edition is to copy the closest suitable direct child of `source/` to a new
folder whose name contains the new year. This preserves the known-good project
contract and leaves the published edition unchanged. The consuming repository
should then audit every copied date, answer, figure, data file, link, script,
and setting; it should never copy generated output.

For a major redesign or content with large ignored data, a clean or selective
copy is equally valid: create the required document folder structure, reuse only
the relevant Markdown/settings/includes, and deliberately add tracked data or
reproducible download scripts. The `create` command is best for a new project,
and `import` is useful when bringing standalone Markdown into a project; neither
requires historical course folders to be overwritten.

Modify source content under `my_project/source/<document_name>/`, not
intermediate output folders. Generate normal documents with:

```bash
venv/bin/python document-builder.py process \
  -c my_project/config/config.json
```

Generate assignments, instructor keys, and question-level feedback with:

```bash
venv/bin/python document-builder.py process \
  -c my_project/config/config.json \
  --assignment
```

Use `--force` to reprocess unchanged inputs and `--remove` only when existing
generated output is intentionally being replaced. Assignment parsing depends on
the heading format documented in `README.md`. The supported authoring convention
is one `# Assignment ...` title followed by sequential `## Question N` sections;
each question must contain a `### N mark` or `### N marks` heading followed by a
`### Answer` heading. Preserve validation of sequence, marks, and answer
boundaries when changing the parser.

Assignment mode turns this single source into three kinds of deliverables: a
student assignment without answers, a complete instructor answer key, and one
question-level feedback PDF per answer. Answer keys and feedback PDFs are often
released to students after marking, so sample content and parser behavior must
support polished, self-contained worked answers rather than marker-only notes.
Answers should be able to include explanatory prose, commands, code, expected
output, marking guidance, and images stored under the document's `includes/`
folder.

Answer-only images belong after the corresponding `### Answer` heading so they
do not appear in the student version. Preserve relative image handling and
verify that images remain legible and correctly scoped in instructor and
feedback output. Images embedded in question text are student-visible by design.
Keep appendix/supplementary handling consistent: these sections remain in
complete assignment and instructor output but are excluded from question-level
feedback, so each feedback answer must remain understandable without them.

When modifying assignment parsing or rendering, test at least one multi-question
fixture containing singular and plural mark headings, prose and code answers,
multiple answer images, an appendix, and supplementary material. Inspect the
student, instructor, and every feedback PDF to catch answer leakage, missing
figures, incorrect boundaries, mark-total errors, or unreadable layout.

When adding or changing a user-facing feature, update the CLI help, README,
default/sample config, relevant import fixtures, sample source, and expected
generated artifacts together. Do not casually rewrite unrelated sample output.

## Large data and consuming repositories

Fresh clones of consuming tutorial and assignment repositories may not have the
contents of `data_not_tracked/`. Design workflows and diagnostics with that
constraint in mind. Prefer small tracked fixtures for tests. When documentation
needs a large real dataset, recommend a tracked download/reconstruction script
using a stable, versioned NCBI or other HTTPS source, explicit output filenames,
provenance, and checksums. Never embed credentials or rely on an author's
private filesystem.

Document Builder merges locally present `data/` and `data_not_tracked/` files
into per-document ZIP archives. Changes to this behavior must be tested for
tracked-only data, untracked large data, empty data folders, nested directories,
and missing local large data.

## Dependencies and verification

Create a virtual environment and install `requirements.txt`. Runtime checks also
require the external programs documented in `README.md`, including Pandoc,
`markdown-link-check`, `spellchecker`, `mdl`, and the configured PDF engine
(commonly `xelatex`).

For Python-only changes, start with:

```bash
venv/bin/python -m py_compile document-builder.py authorize-dropbox.py
```

For processing changes, run:

```bash
./test.sh
```

The test script recreates `sample-project/` and `sample-project-assignment/`,
including tracked sample sources and final artifacts. Review `git status` and
the generated PDFs/HTML after it runs; retain only intentional fixture changes.
Test normal and assignment modes, incremental rebuilds, filenames, links,
archives, and page-level PDF output in proportion to the change.

Do not run `test-dropbox.sh` merely to validate local processing. It writes to
an external Dropbox account and should run only when Dropbox integration is in
scope and configured for a safe test app/folder.

## Dropbox setup and secrets

Normal document generation does not require Dropbox. The `process` command and
`./test.sh` render local output without Dropbox credentials or uploads. Only the
`dropbox` command and `test-dropbox.sh` perform Dropbox synchronization. Most
collaborators should use local processing and leave Dropbox synchronization to
Paul on his configured computer.

For the person responsible for synchronization, Dropbox integration uses
long-lived refresh tokens:

1. Create a Dropbox app with Scoped Access and App Folder permission.
1. Enable `files.content.write`, `files.content.read`, `files.metadata.write`,
   and `files.metadata.read`.
1. Set `DOCUMENT_BUILDER_DROPBOX_APP_KEY`,
   `DOCUMENT_BUILDER_DROPBOX_APP_SECRET`, and
   `DOCUMENT_BUILDER_DROPBOX_TOKEN_FILE`.
1. Run `venv/bin/python authorize-dropbox.py`, approve the app, and paste the
   authorization code.
1. Keep the generated token file outside the repository with mode `0600`.
1. Run the `dropbox` command only when an external upload is intended.

Never print or commit app secrets, authorization codes, access tokens, refresh
tokens, or token-file contents. Use a dedicated test app/folder for integration
work. If credentials are absent, keep verification local and report that Dropbox
integration was not exercised.

## Publishing and symlinks

The `publish_folder_data`, `publish_folder_html`, `publish_folder_markdown`, and
`publish_folder_pdf` configuration values may point outside a project, including
into Dropbox-synced folders. They may also resolve through a developer-created
local symlink. Before writing, resolve and inspect the destination so a typo or
stale link does not publish to the wrong course folder.

Machine-specific absolute symlinks belong in consuming projects' local setup,
not in Git. Do not replace source or fixture folders with symlinks to private
material, and do not add assumptions about a specific user's home directory to
the implementation or default configuration.

## Scope of changes

Agents may improve Document Builder, fix bugs, refactor implementation, add
tests, update dependencies and configuration, revise documentation and sample
content, and make coordinated changes in consuming tutorial or assignment
repositories when those changes are necessary for a complete solution. Prefer
fixing a general defect here over duplicating workarounds in multiple content
repositories. Preserve compatibility when practical; when a breaking change is
necessary, update and verify all affected consumers in the same task.

This `AGENTS.md` is living repository documentation. Agents may and should
update it when the project contract, tooling, supported workflows, testing
expectations, or consuming-repository relationships change. Keep new guidance
specific and accurate, verify commands against the repository, and commit the
file with the related change or in a focused documentation commit.

## Commits

Before committing, inspect `git status`, review source and generated fixture
diffs, and exclude credentials, token files, virtual environments, local
symlinks, and unrelated regenerated artifacts. Make small, coherent commits and
use concise imperative subjects that identify the behavior, such as
`Fix assignment feedback appendix handling`,
`Add checksum validation for data archives`, or `Document Dropbox token setup`.
Avoid vague messages such as `Update` or `Changes`. Keep Document Builder
implementation commits separate from consuming course-content commits, and
explain cross-repository dependencies in commit bodies when useful.

## Change checklist

- Preserve the project folder contract and existing configuration compatibility.
- Keep normal and assignment modes working when the entry point is invoked
  directly or through a symlink.
- Account for consuming clones that lack large `data_not_tracked/` files.
- Keep secrets and external publishing out of ordinary tests.
- Update documentation, fixtures, and generated examples when behavior changes.
- Run focused syntax/tests, visually inspect affected documents, and review
  `git status` before committing.
- Use consuming repositories' `justfile` recipes for integration verification,
  and verify any recipe changed as part of the work.
- Keep this root `AGENTS.md` tracked with the repository.
