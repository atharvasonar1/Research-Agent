# Repository workflow

For a completed GitHub issue implementation:

1. Run the checks required by the issue and the relevant full offline suite.
2. Commit the completed implementation after those checks pass.
3. Push the working branch to `origin`, setting its upstream when needed.
4. Do not create a pull request for each issue unless the user requests one.
5. Do not merge into `main` unless the user explicitly requests it.

Every implementation review must report and verify:

- Branch name.
- Whether the work is committed; when it is, include the commit hash.
- Whether the work is pushed; when it is, include GitHub links to the commit and branch.
- Whether the working tree is clean; otherwise list the remaining changes.
- Any blocker that prevented a commit or push.
