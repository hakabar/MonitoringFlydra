# MonitoringFlydra
Script to detect the amount of frames from the FLYDRA tracking system have the following issues:
  - Frames lost
  - Frames missing information

NOTE: We need to specify in the script main function:
  - duration of the experiment in hours (totalHours) -> expDuration=3600*totalHours
	- The amount of frames per second used by FLYDRA (fps)
  - Total number of cameras used by flydra (numCams)
