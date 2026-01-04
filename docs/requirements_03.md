Refactor the implementation. 
Please make sure that you create a sold plan of implementation and ask me any clarifying questions before you start implementing the system. The detailed requirements and the plan should be stored in this folder in filename requirements_04.md

My inputs on what has to be changed in the current implementation are as follows :-

## Core Change 1 
The system should be divided into two different phases. 
1) Fetching 
2) Processing  

The fetching phase should be responsible for fetching messages from the Telegram API and save in markdown format. These files should be stored in a staging area. The processing phase should be responsible for processing the fetched messages and then saving them in the final destination files. The naming conventions should be similar. 

Note that therefore we would have to maintain multiple stages , one for downloading the messages and another for processing them. Design the system accordingly.

## Core Change 2 : Workflows need to be atomic instead of combined 
Also we would therefore need to change what all the commands and arguments are there for running trudy :- 

Broadly :-  
1) Run the script to automatically detect users. These should be stored in some json based state.
2) Run the script to fetch messages and store then in the staging area. 
3) The post processing stage should work on new data that has been entered in the staging area 

## Core Change 3 : Change in the markdown formats 
Staging area markdown : Should essentially be whatever we have downloaded using the api 

Post processing markdown : Should essentially have more details based on postprocessing. Something similar to the following (Please feel free to improve this):- 
```
- Timestamp : 
  - type : normal_text 
  - link : 
  - automatic_tags :
- Timestamp : Image 
  - type : image
  - wikilink : 
  - automatic_tags : 
  - about : 
  - ocr_text : 
- Timestamp : Video
  - type : normal_text 
  - wikilink : 
  - automatic_tags :
  - automatic_summary : 
  - transcript_file : 
- Timestamp : Audio 
  - type : normal_text 
  - wikilink : 
  - automatic_tags :
  - automatic_summary : 
  - transcript_file : 
- Timestamp : Text (Youtube Link)
  - type : normal_text 
  - youtube_link : 
  - video_title : 
  - video_description : 
  - automatic_tags :
  - automatic_summary : 
  - transcript_file : 
- Timestamp : Document
  - type : normal_text 
  - wikilink : 
```

## Core Change 4 : Remove unnecessary previous functionalities 
Remove the manual mode for fetching users. Users should be automatically discovered by running the Trudy script with specific commands 

## Core Change 5 : Python dependencies 
Using typer python package instead of click for the cli tool




## Note : Kind of messages to be supported :- 
1) Video 
   - Can be video file 
   - Can be video notes
2) Audio 
   - Can be audio file
   - Can be voice message
3) Image 
	- Screenshot 
	- (Other images)
4) Text 
	- Normal text 
	- Can contain links 
    	- Article 
    	- Youtube video  
    	- Others 
  	- Can contain 
    	- hashtags, mentions, bold, italic, underline etc 
5) Documents 
6) Others (Stickers etc)




