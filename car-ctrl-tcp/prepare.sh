#!/bin/bash --

# Virtual environment
venv=.venv
if [ ! -d "${venv}" ]
then
  echo "Setting up virtual environment"
  python3 -m venv ${venv}
  source ${venv}/bin/activate
  pip3 install -r requirements.txt

  
  # Set up OpenCV - assumes that you already installed it!
  echo "Trying to link to your OpenCV installation"
  # TODO as is, won't work with multiple installed OpenCV versions, would have to select the first line/the latest version/etc.
  opencv_lib=$(find /usr/local/lib/python3* -name cv2*)
  if [ -z "${opencv_lib}" ]
  then
    echo "[E] You need to install OpenCV first!" 1>&2
    exit 23
  fi
  # Get correct python subfolder
  pverstring=$(ls ${venv}/lib/ | grep python3)
  libdir=$(dirname "${opencv_lib}")
  #echo $libdir
  #echo $pverstring
  # Create link file in virtualenv
  echo ${libdir} > ${venv}/lib/${pverstring}/site-packages/cv2.pth  
fi

