
General Instructions

mkdir demo
cd demo
git clone https://github.com/<acctname>/<reponame.git>
git status
git add -A
git status
git commit -am "Updated Howto File"

Before pushing check the branch
git branch

git push origin master

git push

Alternatively git push -u origin master
              git push -u origin <branchname>

GIT_SSH_COMMAND='ssh -i ~/.ssh/id_ed25519_git-1 -o IdentitiesOnly=yes' git pull
GIT_SSH_COMMAND='ssh -i ~/.ssh/id_ed25519-git-2 -o IdentitiesOnly=yes' git pull
GIT_SSH_COMMAND='ssh -i PATH/TO/KEY/FILE -o IdentitiesOnly=yes' git clone git@github.com:OWNER/REPOSITORY

git remote add origin https://github.com/<acctname>/<reponame.git>
git remote
git remote -v

git fetch
git pull (pull is fetch + merge)

tree -a

#Branching

git log --all --graph
git branch testing # create a new branch called testing git branch -D testing to delete

git checkout testing  # Head moves to the new branch
git log --all --graph


git branch

git checkout master
git log --all --graph

#Merging

git merge testing -m "merging testing over to master"

# in the event of conflict resolve conflict and save


git add .
git commit -m "conflicts resolved"


git tag v1.0

git tag -a v1.2 -m "release v1.2"


git log

git log --all --graph

git branch --show-current
git switch main

