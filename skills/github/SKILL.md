---
name: github
description: "Load before any git or GitHub work in a chat: committing model changes, pushing a branch, opening a pull request, updating a pull request, or commenting on one. Covers the sandbox git checkout, the signalpilot/ branch rule, and the open_pull_request, update_pull_request, and comment_on_pull_request tools."
type: skill
---

# GitHub: propose project changes on a branch

The chat agent proposes changes to the dbt project as commits on a
`signalpilot/` branch. The branch stays on SignalPilot's git server. You then
file it as a suggestion with `make_recommendations`. An admin reviews the
diff on the Suggestions page and clicks Create PR, which puts the branch on
GitHub and opens the pull request. A person merges on GitHub. The agent never
merges.

Open a pull request yourself only when the user asks for one in this chat.

## Where git runs

The sandbox VM holds the project at `/workspace`. `/workspace` is a git
repository. The remote `origin` is SignalPilot's git server, not GitHub.
Credentials are already configured. You do not need a token.

Run every git command with `sandbox_exec`. Set `cwd` to `/workspace`. Edit
files with `sandbox_write_file`. Do not edit files in your own working
directory. It is a frozen copy for reading only.

The system prompt names the base branch. Your commits go on top of that
branch.

## Branch rule

The server accepts a push only to a branch that starts with `signalpilot/`.
Use the form `signalpilot/<short-name>`. Use a short lowercase name with
hyphens that describes the change. Example: `signalpilot/fix-revenue-grain`.

Use one branch name for one piece of work. Push to the same name each time
you add commits.

The server refuses these pushes and prints the reason:

- A push to any branch that does not start with `signalpilot/`.
- A force push. Add a new commit instead.
- A branch deletion.
- A branch that another chat created. Use a new name.
- A new branch name that already exists on GitHub. Use a new name.

## Steps to propose a change

1. Change the files in `/workspace` in the sandbox VM. Any project file is
   fine: model SQL, YAML descriptions and tests, docs, seeds.
2. For model changes, call `estimate_query_cost` on each changed model's
   compiled SQL, and optimize it until it fits or ask for more time. Then run
   `dbt_execute` with `build` and fix errors until it passes. A
   description-only change needs no build. If the user or spec says not to
   build, skip it and say why in the PR body or suggestion reason. Run the
   verifiers and fix every FAIL before you commit.
3. Check the diff: `git status` and `git diff`.
4. Stage and commit: `git add -A && git commit -m "<clear message>"`.
5. Push: `git push origin HEAD:signalpilot/<short-name>`. The branch stays on
   SignalPilot's server; it does not reach GitHub yet.
6. File it: call `make_recommendations` with a change
   `{"type": "dbt_branch", "branch": "signalpilot/<short-name>", "reason": "...", "files": [{"path": "...", "why": "..."}]}`.
   Give one `files` item for each changed file.
   Load the `recommendations` skill first for the rest of the call.
7. Name the suggestion number in your answer. Do not open a pull request.

If the user asks for a pull request, do steps 1 to 5, then call
`open_pull_request` and put the URL in your answer.

## Pull request tools

- `open_pull_request(title, body, draft, branch)`: only when the user asks
  for a pull request. It puts the branch on GitHub and opens the pull request
  for it. Leave `branch` empty to use your most recent
  push. Set `draft` true for work that is not ready for review. If the
  branch already has an open pull request, the tool returns it.
- `update_pull_request(title, body, pr_number)`: changes the title or the
  body. Use it after you push more commits, so the description stays true.
- `comment_on_pull_request(body, pr_number)`: adds a comment. Use it to
  report a new build result, to answer a review comment, or to explain one
  part of the change in detail.

Every tool returns `pr_url`. Give the user that link. Every tool acts only
on branches and pull requests that this chat created.

## Good pull request messaging

- Title: one line, imperative, under 70 characters.
- Body: what changed, why, how you verified it, and what the reviewer
  should check.
- When the user asks for detailed explanations, put one topic per comment
  with `comment_on_pull_request`.

## Do not

- Do not run `git push --force`.
- Do not push to `main` or to any branch outside `signalpilot/`.
- Do not try to merge. There is no tool for it.
- Do not put tokens or credentials in commits, comments, or answers.
