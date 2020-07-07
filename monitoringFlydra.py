"""
        Script to detect the amount of frames from the FLYDRA tracking system have issues:
        Issues controlled:
                - Frames lost
                - Frames missing information
	NOTE: We need to specify in the script main function:
                - duration of the experiment in hours (totalHours) -> expDuration=3600*totalHours
		- cameras fps
                - numCams= Total number of cameras used by flydra

"""


import os
from collections import Counter
import glob

def locate_log_file(path):
        """
        Find the latest log file created by FLYDRA        
        """
        #fNames= 'flydra_mainbrain-{1..9}.log'
        print('loading data from:')
        print (path)
        fNames='flydra_mainbrain-[1,2].log'
        filesList= glob.glob(path+fNames)
        latestFile= max(filesList, key= os.path.getctime)
        print( ' - Working with file: ',latestFile)
        return latestFile



def load_file(path):
        """
        Load the latest flydra log file. 
        We will read this file to find the amount of frames lost per each camera
        """
        #path= '/home/wtunnel/.ros/log/latest/flydra_mainbrain-2.log'
        if os.path.exists(path):
                f= open(path, 'r')
                data= f.readlines()
                return data
        else:
                print( ' * Error while loading file: %s'%(path))


def read_date_from_file(data):
        """
        find Flydra's execution date from .log file (1st row)
        msg example: [rospy.client][INFO] 2019-10-14 11:08:54,195: init_node, name[/flydra_mainbrain], pid[17828]
        """
        # the date will be always character 21 to 40 (21:31 for date and 31:40 for time)
        return data[0][21:40]


def find_cameras(data, totalCameras):
        """
        find Flydra's cameras IDs from information in .log file 
        msg example: [INFO] [1570818072.846215]: new camera: Basler_22176483
        """ 
        entry= 'REGISTER NEW CAMERA '
        #totalCameras-=1     #from camera 0 to camera 15 (16 cameras)
        camIDsList=[]
        camCounter=0
        #Find the cameras IDs
        for line in data:
                #Find all lines containing the info string
                if entry in line:
                        camID= line[len(line)-16:len(line)-1]
                        camIDsList.append(camID)
                        camCounter+=1
                        if (camCounter == totalCameras):
                                #we have detected all the cameras IDs
                                break
        return camIDsList


def count_frames_lost(data):
        """
        Count the number of entries with 'frame data loss' has the log file for each of the cameras. 
        msg example: [rosout][WARNING] 2019-11-07 11:43:16,986: frame data loss Basler_22551998
        """
        entry='frame data loss'
        framesLost=[]
        for line in data:
                if entry in line:
                        #Line will contain the cameraID in position [line][59:len(line)-1]
                        framesLost.append(line[59:len(line)-1])
        return dict(Counter(framesLost))


def count_frames_with_data_lost(data):
        """
        Count the number of entries with 'missing data' has the log file for each of the cameras. Read the amount of frames lost that appear in each entry
        msg example: [rosout][INFO] 2019-11-07 12:21:56,876: requested missing data from Basler_22176500. offset 1429, frames [145521, 145522, 145523, 145524, 145525]

        """
        entry='missing data'
        framesLost=[]
        c1=c2=0
        for line in data:
                c1+=1
                if entry in line:
                        # Line will contain the cameraID and a list ([x,y,k]) with frames x,y,k
                        # Find the camera ID and the last word (frames) before the list of frames itself
                        camIndex= str.find(line, 'Basler')
                        camID= line[camIndex: camIndex+15]
                        flagIndex= str.find(line, 'frames')
                        # Add the substring containing the frames detected and split the substring into the # of frames found
                        framesList= line[flagIndex+len('frames ')+1:len(entry)-1]
                        framesList= framesList.split(',')
                        # Append to frameLost the camera ID associated as many times as frames where detected
                        framesLost+= len(framesList) * [camID]                       
        return dict(Counter(framesLost))
    

def check_health(fLost, fMissInfo, ids, fps, expDuration):
        """
        Print the amount of frames lost per each camera in the last FLYDRA run 
         and the amount of frames with missing information fo each camera
        """
        totalLosses={}
        sumAllLosses=0
        totalFrames= fps*expDuration
        for i in ids:
                # Amount of frames completely lost by each camera ID
                loss= fLost[i]
                print(' * Camera: %s -- %s frames lost over %s (%s %% of frames lost)'%(i, loss, totalFrames, round((loss/totalFrames)*100, 3)))
                totalLosses[i]= loss
        
        print(' ------------ ')
        for i in ids:
                # Amount of frames with missing information per each camera ID
                loss= fMissInfo[i]
        
                print(' * Camera: %s -- %s frames with missing info over %s (%s %% of frames lost)'%(i, loss, totalFrames, round((loss/totalFrames)*100, 3)))

                #Add the number frames with missing info (for a given camID) to the frames lost by the same camID
                totalLosses[i]+= loss
        
        print(' ------------ ')
        for i in ids:
                # Amount of total frames with any type of issue per each camera ID
                loss= totalLosses[i]
                print(' * Camera: %s -- %s %% of frames where lost or had missing information (# of frames lost: %s)'%(i, round((loss/totalFrames)*100,3), loss))
                sumAllLosses += loss

        print(' ------------ ')

        print(' * Total amount of frames lost (if all cameras have been recording at 60fps): %s %%'%(round((sumAllLosses/(totalFrames*16))*100, 3)))
        print(' * %s frames over the total of %s had an issue'%(sumAllLosses, totalFrames*16))
        # %% (%s frames over %s)'%(round(sumAllLosses/expDuration)*100,1), sumAllLosses, totalFrames*16)


if __name__ == "__main__":
        numCams= 16	# Total number of cameras used by flydra
        fps=60		# Frames Per Second	
        totalHours= 3	# How many hours has the experiments taken 
        expDuration= 3600*totalHours
        path='/home/wtunnel/.ros/log/latest/'

	#Load the log file
        newestLogFile= locate_log_file(path)
        logMsgs= load_file(newestLogFile)      
        
        #Read the date of the experiment
        #read_date_from_file(logMsgs)
        
        #Locate all the cameras used in experiment
        camIDs= find_cameras(logMsgs, numCams)
        #Count the amount of frames lost during execution of Flydra
        framesLost = count_frames_lost(logMsgs)
        #Count the amount of frames incomplete during execution of Flydra
        framesMissInfo= count_frames_with_data_lost(logMsgs)
        # Plot the log report in the terminal
        check_health(framesLost, framesMissInfo, camIDs, fps, expDuration)

