SpaceAPI
========

SpaceAPI provides access to the k8055 USB interface board that is used to connect some of the Farset Labs facilities together, such as the 'Big Red Button', door striker, and door contact.

Access is provided via the SpaceAPIClient module, which exposes the following interfaces
* get(self,path, **params): Provides Raw access
* authGet(self,path, **params) : Provides Raw Authenticated Access, requires valid authpair=(username,password) to be passed at client init
* authPut(self,path, **params) : Ditto
* buttonDownState(self) : surprisingly enough, returns a bool of the button down state, i.e. True means the space should be open
* doorClosedState(self) : ditto, for the door
* spaceState(self) : Returns the current state of the space as defined in [The SpaceAPI](https://hackerspaces.nl/spaceapi/)

##Example
>from SpaceAPIClient import client

>authpair=("username","TotallySecurePassword")

>base="http://farbot:5000"

>c=client(authpair=authpair,base=base)

>doorClosed=c.doorClosedState()

>print "Door is closed" if doorClosed else "Door is open"


##Actual API Capabilities
* ```/space``` [GET) :returns the spaceAPI JSON (see spaceState())
* ```/door``` [GET, authenticated]: Opens the space door for 2 seconds (more like 5)
* ```/open?state=<state in 'True','False'>``` [PUT, authenticated]: Set the space open state
* ```/board?type=<type in 'digital','analog'>&channel=<channel in [0-4] digital or [1-2] analog>``` [GET]: Read the board's inputs directly


