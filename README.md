# DVC-Sensor
UMD 2023 senior design deer detection project\
Arduino nano source code: deerdetionsensorarray.ino

This project was inspired by the large amount of damage caused by deer-vehicle collisions in Michigan. Our state has a large amount of deer, and any car that runs into a deer has a good chance to be totalled. This project aims to reduce deer collisions by providing detection modules and lights to notify drivers about deer approaching the road. 

So far, we have detection modules based on image processing, which do successfully detect deer. Two variations exist; one variation uses a Raspberry Pi for the image processing, and one uses an Arduino Nano instead. 

A light module has also been created, in order to simplify the process of blinking a light and driving LEDs. The module is also designed with expansion in mind, with documentation including a possible way to use a diode and relay to drive more powerful or higher voltage lights. The schematics for the lighting module have been provided in the form of images in documentation, and KiCad project files. 

The project still needs more work to be done. One major point is improving the accuracy of the detector modules. The Pi version is overall more accurate, but neither are quite good enough. Furthermore, we have not tested either of these modules at scale, having only built one of each. 
