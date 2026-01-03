## Overall objective 
I want to have a setup where one keep sending notes to a telegram bot in the phone.  

Workflow :- 
1) I send a message to the a telegram bot from my phone. I have two phone numbers, so two users. 
2) Then at a later point in time, I should be able to run a script on my macbook that reads all the messages from that telegram chat. While downloading in case there is a rich media, it should download the rich media as well. The messages should be stored in a markdown file along with the timestamp at which the message was sent. The various notes should be created based on the timestamp of when the message was sent. the files should have the following name : YYYY-MM-DD.md (Let's call these as notes markdown file) 
3) Depending on the type of message, it should then postprocess the message and add the outputs along with the message in the respective note markdown file. The attachments like photos, videos and images should be stored in a specific folders and a link should be added to the document as embedded wikilink. 

## Type of messages that I can send to the bot :-
1) Video 
2) Audio 
3) Image 
	- Screenshot 
	- (Other images)
4) Text 
	- Normal text 
	- Link to article 
	- Link to youtube video 
	- (Other links)  
(Please suggest others that Telegram supports)

## Post processing 
- For the videos and the audio files, a transcription and a summary should be stored in the markdown file. 
  - The transcription should be stored in a separate file along with the video or audio file. 
  - The summary of the video or audio file should be stored in respective markdown file along with the wikilink to the video or audio file.
- If I am sending a link to an article, the link and a summary of the link should be stored in the markdown file. 
- In case I am sending a youtube link, a summary of the key discussions in the video should be stored in the notes markdown file along with the wikilink to the video.

## Additional notes 
- Please make sure that you are using local models available on a macbook to be able to transcribe the data. 
- For transcription : Give the user an option to choose the following :- 
  - Use a local model on a macbook (Default)
  - Use a remote model 
  - In case of a youtube video - you can also fetch the transcript from youtube.
- For summarisation : Give the user an option to choose the following :-
  - 
- Use well documented python scripts wherever possible to make the process deterministic. 
- Use `uv` to run 
- Make sure that while running the scripts regularly, it downloads and processes only the new messages and not the historic ones. It should download the historic records only when a specific flags is sent. The operations should be indempotent. 
- Have a common index status file that mentions the users that are sending messages to the bot, when the user sent the first message, when did the last messages were fetched 
- While storing the information and designing the folder structure make sure that you are saving data from various different users in separate folders.

## Task 
- Generate a USAGE.md file that details how this system will be used 
- Help me first plan and design the stucture of the local folder, the various file and how you would go about implementing this. Help me with all the clarifying questions so that you are able to come up with a plan 

