#!/bin/bash

testname="multiline-string"

rm -rf gitreport

rm -rf tests/$testname
mkdir tests/$testname
cd tests/$testname

git init --initial-branch=main
git config user.name "Test1"
git config user.email "testuser1@test.com"

cp ../../test-definitions/$testname/version1.c main.c
git add main.c
git commit -m "Initial commit"

git config user.name "Test2"
git config user.email "testuser2@test.com"

cp ../../test-definitions/$testname/version2.c main.c
git add main.c
git commit -m "Second commit"

cd ../..
gitreporter -c test-definitions/$testname/config.json
