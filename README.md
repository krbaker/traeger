# traeger
Attempt to connect to traeger wifire

I wish traeger would just have an open API, this might break at any time though I think using a lot of AWS' IOT tools might limit that risk.  I reversed the traffic from the android app mainly and also looked at the AWS IOT docs to figure out the usage.  I couldn't find the 'shadow' data in AWS for a one time lookup so I'm subscribing and waiting for data which is pretty lame.  I haven't had time to make it better recently so I'm going to share this for now.

The traeger2graphite script is what I'm currently using to get a graph of my smoker data and is a simple example too.  Needs a simple ~/.traeger config file with the contents:

`{"username": "<your email>", "password": "<your password", "graphite_port": "2003", "graphite_host": "graphite.local"}`
