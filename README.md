# py-traveller
A quick tool that opens the given youtube video and automatically skips to the next recommended video over and over.

Does some basic image recognition on each page to find all the sponsored posts or videos.

Outputs a csv with basic metadata for wach watched and a screenshot of the page for each video to the `output` directory.

Should work with most versions of python >= `3.10`, but has only been tested using `3.13`.


### Know Issues/Quirks
* Can't deal with live streams very well
* There is no way to automate logging in
* Will sometimes get stuck looping the same 2-4 videos forever until the browser is closed
* Will sometimes not go to the next video, will need to manually click on a video when that happens