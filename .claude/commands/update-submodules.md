Update all git submodules to their latest remote commits.

Steps:
1. Run `git submodule status` to show current state of all submodules
2. Run `git submodule update --init --recursive --remote` to pull latest commits from each submodule's tracked branch
3. Run `git submodule status` again to show the updated state
4. Show a summary of what changed (old vs new commit hashes)
5. If any submodules were updated, ask the user if they want to commit the submodule pointer updates

If a specific submodule path is provided as argument, only update that one submodule instead of all.

Argument: $ARGUMENTS
