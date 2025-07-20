### General Instructions

```bash
mkdir demo
cd demo
git clone https://github.com/<acctname>/<reponame.git>
git status
git add -A
git status
git commit -am "Updated Howto File"
```

Before pushing, check the branch:

```bash
git branch
```

To push changes:

```bash
git push origin master

git push
```

Alternatively:

```bash
git push -u origin master
git push -u origin <branchname>
```

To use a specific SSH key:

```bash
GIT_SSH_COMMAND='ssh -i ~/.ssh/id_ed25519_git-1 -o IdentitiesOnly=yes' git pull
GIT_SSH_COMMAND='ssh -i ~/.ssh/id_ed25519-git-2 -o IdentitiesOnly=yes' git pull
GIT_SSH_COMMAND='ssh -i PATH/TO/KEY/FILE -o IdentitiesOnly=yes' git clone git@github.com:OWNER/REPOSITORY
```

Remote repository commands:

```bash
git remote add origin https://github.com/<acctname>/<reponame.git>
git remote
git remote -v
```

Fetch and pull:

```bash
git fetch
git pull   # pull is fetch + merge
```

Show directory tree (including hidden files):

```bash
tree -a
```

---

# Branching

View log graph:

```bash
git log --all --graph
```

Create and delete a branch:

```bash
git branch testing          # create a new branch called 'testing'
git branch -D testing      # delete the 'testing' branch
```

Switch to a branch:

```bash
git checkout testing       # HEAD moves to the new branch
git log --all --graph
```

List branches:

```bash
git branch
```

Switch back to master:

```bash
git checkout master
git log --all --graph
```

---

# Merging

Merge a branch:

```bash
git merge testing -m "merging testing over to master"
```

*In the event of a conflict, resolve the conflict and save.*

After resolving conflicts:

```bash
git add .
git commit -m "conflicts resolved"
```

---

# Tagging

Create tags:

```bash
git tag v1.0
git tag -a v1.2 -m "release v1.2"
```

---

# Other Useful Commands

Show log:

```bash
git log
git log --all --graph
```

Show current branch:

```bash
git branch --show-current
```

Switch branches (Git 2.23+):

```bash
git switch main
```
```
