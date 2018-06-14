#!/bin/bash --

third_party_dir=../third_party

# Ensure third party folder exists
if [ ! -d "${third_party_dir}" ]
then
  mkdir -p ${third_party_dir}
fi

# Download pypi's inputs.py 
# exploit github's svn support: https://stackoverflow.com/questions/9609835/git-export-from-github-remote-repository
zeth_inputs=${third_party_dir}/inputs
if [ ! -d "${zeth_inputs}" ]
then
  echo "Setting up third party: inputs.py"
  svn export https://github.com/zeth/inputs/trunk ${zeth_inputs}
fi

# Virtual environment
venv=.venv
if [ ! -d "${venv}" ]
then
  echo "Setting up virtual environment"
  python3 -m venv ${venv}
fi




