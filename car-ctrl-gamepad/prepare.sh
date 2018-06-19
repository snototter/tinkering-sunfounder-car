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

# Download SunFounder's demo to reuse the motor/servo control.
sunfounder_repo=${third_party_dir}/sunfounder
if [ ! -d "${sunfounder_repo}" ]
then
  echo "Setting up third party: sunfounder"
  svn export https://github.com/sunfounder/Sunfounder_Smart_Video_Car_Kit_for_RaspberryPi/trunk ${sunfounder_repo}

  mkdir sunfounder-patched
  #diff -ruN ../third_party/sunfounder/server/car_dir.py sunfounder-patched/car_dir.py > patch_car_dir.patch
  cp ../third_party/sunfounder/server/PCA9685.py sunfounder-patched
  cp ../third_party/sunfounder/server/motor.py sunfounder-patched
  cp ../third_party/sunfounder/server/car_dir.py sunfounder-patched
  cp ../third_party/sunfounder/server/video_dir.py sunfounder-patched
  patch sunfounder-patched/PCA9685.py patch_pca9685.patch
  patch sunfounder-patched/motor.py patch_motor.patch
  patch sunfounder-patched/car_dir.py patch_car_dir.patch
  # No need to patch video dir as of now...
fi


# Virtual environment
venv=.venv
if [ ! -d "${venv}" ]
then
  echo "Setting up virtual environment"
  python3 -m venv ${venv}
  source ${venv}/bin/activate
  pip3 install -r requirements.txt
fi




