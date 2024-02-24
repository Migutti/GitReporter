#!/bin/bash

testname="demonstration-repo"

rm -rf gitreport

rm -rf tests/$testname
mkdir tests/$testname
cd tests/$testname

git init --initial-branch=main
git config user.name "Alice"
git config user.email "alice@test.com"

cp ../../test-definitions/$testname/version1.c main.c
git add main.c
git commit -m "Initial commit"

git config user.name "Bob"
git config user.email "bob@test.com"

cp ../../test-definitions/$testname/version2.c main.c
git add main.c
git commit -m "Second commit"

cd ../..
gitreporter -c test-definitions/$testname/config.json
