# GitHub Branch Protection Setup

To ensure all tests pass before merging PRs into `master`, you need to configure branch protection rules in your GitHub repository.

## Steps to Configure Branch Protection

1. Go to your repository on GitHub
2. Navigate to **Settings** → **Branches**
3. Under "Branch protection rules", click **Add rule**
4. Configure the following:

### Branch name pattern
```
master
```

### Protection Rules to Enable

✅ **Require a pull request before merging**
   - ✅ Require approvals: 0 (or 1 if you want self-review)
   - ✅ Dismiss stale pull request approvals when new commits are pushed

✅ **Require status checks to pass before merging**
   - ✅ Require branches to be up to date before merging
   - **Required status checks:**
     - `test` (this is the job name from your `ci.yml`)

✅ **Require conversation resolution before merging** (optional but recommended)

✅ **Do not allow bypassing the above settings** (recommended unless you need emergency access)

## How This Works with Release-Please

Your current workflow setup:

1. **Developer Flow:**
   - Create feature branch
   - Make changes with conventional commits
   - Open PR → **CI runs and must pass** ✅
   - Merge to `master`

2. **Release-Please Flow:**
   - Runs on every push to `master`
   - Creates/updates a release PR with changelog
   - When you merge the release PR → triggers `build-and-push.yml`

3. **Build and Push Flow:**
   - Only runs on published releases
   - Builds and pushes Docker images to GHCR

## Testing the Workflow

To test that your CI workflow works correctly:

```bash
# Create a test branch
git checkout -b test/ci-workflow

# Make a small change (already done - you have uncommitted changes)
git add .
git commit -m "test(ci): verify GitHub Actions workflow"

# Push and create a PR
git push -u origin test/ci-workflow
```

Then open a PR on GitHub and verify that the `CI / test` check runs and passes.
