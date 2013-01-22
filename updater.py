import SpaceAPIClient
import sys

c = SpaceAPIClient.client(["farset",sys.argv[1]],"http://localhost/spaceapi")
print(c.update_poll())
